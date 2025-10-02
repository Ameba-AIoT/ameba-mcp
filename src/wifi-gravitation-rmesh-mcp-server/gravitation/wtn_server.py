import logging
import platform
import random
import socket
import struct
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone

import psutil

from .packet_model import PacketModel
from .enums import ConnectionProtocol
from .rmesh_parser import pack_tool_announce, pack_rmesh_packet, RmeshPacketType, unpack_rmesh_packet, parse_payload, \
    PayloadType


def construct_json_report(parsed_data: PacketModel):
    father_score = parsed_data.father_score
    candidate_score = parsed_data.candidate_score
    score = f"wtn_score:{parsed_data.father_mac.split(':')[-1]}{father_score}"
    if parsed_data.candidate_mac:
        score += f", {parsed_data.candidate_mac.split(':')[-1]}{candidate_score}"

    return {
        "type": "report",
        "mac": parsed_data.self_mac,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "payload": [
            {
                "type": "mac",
                "data": f"wtn_self_mac:{parsed_data.self_mac}"
            },
            {
                "type": "father_mac",
                "data": f"wtn_father:{parsed_data.father_mac}"
            },
            {
                "type": "score",
                "data": score
            },
            {
                "type": "ip",
                "data": f"Interface 0 IP address : {parsed_data.self_ip}"
            },
            {
                "type": "bssid",
                "data": f"wtn_bssid:{parsed_data.bssid}"
            },
            {
                "type": "node_name",
                "data": f"wtn_node_name:{parsed_data.node_name}"
            }
        ]
    }


class WTNServer:
    def __init__(self, report_timeout, max_connection=100, broadcast_port=12345, listening_port=12346, ifname=None):
        self.listening_port = listening_port
        self.ifname = ifname or self.detect_interface()
        self.local_ip = self.get_local_ip()
        self.local_mac = self.get_local_mac()
        self.broadcast_address = ('<broadcast>', broadcast_port)
        self.max_connection = max_connection
        self.stop_event = threading.Event()
        self.tcp_server_thread = None
        self.nodes = {}
        self.report_timeout = report_timeout
        self.node_connected_callback = None
        self.node_disconnected_callback = None
        self.node_report_callback = None
        self.random_byte = random.randbytes(1)[0]
        logging.debug(f"Random byte is {self.random_byte}")
        self.nodes_lock = threading.Lock()

    def detect_interface(self):
        for iface, addrs in psutil.net_if_addrs().items():
            for addr in addrs:
                if addr.family == socket.AF_INET and addr.address.startswith('192.168.0'):
                    logging.info(f"Detected interface with 192 IP: {iface}")
                    return iface
        raise RuntimeError("No suitable network interface with 192 IP found")

    def get_local_ip(self):
        def get_windows_ip():
            preferred_ip = None
            for iface, addrs in psutil.net_if_addrs().items():
                if iface == self.ifname:
                    for addr in addrs:
                        if addr.family == socket.AF_INET and not addr.address.startswith('169.254'):
                            if addr.address.startswith('192'):
                                return addr.address
                            if preferred_ip is None:
                                preferred_ip = addr.address
            return preferred_ip

        def get_non_windows_ip():
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            return socket.inet_ntoa(fcntl.ioctl(
                s.fileno(),
                0x8915,  # SIOCGIFADDR
                struct.pack('256s', self.ifname[:15].encode('utf-8'))
            )[20:24])

        if platform.system() == 'Windows':
            return get_windows_ip()
        else:
            return get_non_windows_ip()

        return None

    def get_local_mac(self):
        if platform.system() == 'Windows':
            for iface, addrs in psutil.net_if_addrs().items():
                if iface == self.ifname:
                    for addr in addrs:
                        if addr.family == psutil.AF_LINK:
                            return addr.address
        else:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            info = fcntl.ioctl(s.fileno(), 0x8927, struct.pack('256s', self.ifname[:15].encode('utf-8')))
            return ':'.join(['%02x' % b for b in info[18:24]])
        return None

    def send_broadcast(self):
        """
        [重构后] 周期性发送 'Tool Announce' 数据包。
        此函数是一个阻塞式循环，会持续广播直到 self.stop_event 被设置。
        """
        # 1. 业务层 & 协议帧层: 使用标准化工具一次性创建好要发送的完整数据包
        try:
            # 1a. 创建标准负载
            payload = pack_tool_announce(
                random_byte=self.random_byte,
                pc_ip=self.local_ip,
                report_port=self.listening_port
            )
            # 1b. 封装成标准R-MESH数据包
            message = pack_rmesh_packet(
                packet_type=RmeshPacketType.TOOL_ANNOUNCE,
                payload=payload
            )
            logging.debug(f"Prepared Tool Announce packet: {message.hex(' ')}")
        except Exception as e:
            logging.error(f"Fatal: Failed to create broadcast packet: {e}")
            return # 如果包都创建不了，直接退出

        # 2. 网络层: 创建Socket并进入广播循环 (此部分逻辑与您原始代码保持一致)
        udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        udp_socket.bind((self.local_ip, 0)) # 绑定到指定IP，源端口由系统随机分配

        logging.info(f"Starting broadcast loop to {self.broadcast_address}...")
        try:
            while not self.stop_event.is_set():
                # 3. 发送已创建好的标准数据包
                udp_socket.sendto(message, self.broadcast_address)
                time.sleep(1)
                logging.info(f"Nodes: {list(self.nodes.keys())}")
        except KeyboardInterrupt:
            logging.info("Broadcast stopped by user (KeyboardInterrupt).")
        except Exception as e:
            logging.error(f"An error occurred in broadcast loop: {e}")
        finally:
            udp_socket.close()
            logging.info("Broadcast socket closed.")

    def start_broadcast(self):
        self.stop_event.clear()
        broadcast_thread = threading.Thread(target=self.send_broadcast)
        broadcast_thread.daemon = True
        broadcast_thread.start()

    def stop_broadcast(self):
        self.stop_event.set()

    def handle_client(self, client_socket, addr):
        try:
            while True:
                # Read the length prefix (4 bytes)
                length_prefix = client_socket.recv(4)
                if not length_prefix:
                    break
                message_length = int.from_bytes(length_prefix, byteorder='big')

                # Read the actual message data
                message_data = client_socket.recv(message_length)
                if not message_data:
                    break

                parsed_data = PacketModel(message_data)
                report = construct_json_report(parsed_data)
                mac = report.get("mac")
                if not mac:
                    return
                if mac not in self.nodes:
                    self.node_connected_callback(mac, parsed_data.rnat_flag)
                if self.node_report_callback:
                    self.node_report_callback(report, parsed_data)
                self.nodes[mac] = datetime.now(timezone.utc)
                # logging.info(f"Received report from {mac}: {report}")
        except Exception as e:
            logging.error(f"Error handling client {addr}: {e}")
        finally:
            client_socket.close()
            logging.info(f"Closed connection from {addr}")

    def handle_udp_message(self, message_data, addr):
        try:
            # 1. [已修改] 使用新工具解开R-MESH标准包，获取类型和负载
            packet_type, payload = unpack_rmesh_packet(message_data)

            # 确保我们只处理节点报告
            if packet_type != RmeshPacketType.NODE_REPORT:
                return

            # 2. [已修改] 使用新工具将负载解析为字典
            parsed_data_dict = parse_payload(payload, PayloadType.NODE_REPORT)

            # 3. [适配层] 使用解析出的字典实例化 PacketModel，对业务层保持接口兼容
            parsed_data = PacketModel(parsed_data_dict)
            report = construct_json_report(parsed_data)
            mac = report.get("mac")
            if not mac:
                return
            with self.nodes_lock:
                if mac not in self.nodes:
                    if self.node_connected_callback:
                        # 业务层代码不变，仍然使用 parsed_data.rnat_flag
                        self.node_connected_callback(mac, parsed_data)
                self.nodes[mac] = datetime.now(timezone.utc)
            if self.node_report_callback:
                # 业务层代码不变，回调的第二个参数仍然是 PacketModel 对象
                self.node_report_callback(report, parsed_data)
        except ValueError as e:
            # 捕获由 unpack_rmesh_packet 或 parse_payload 抛出的格式错误
            logging.error(f"Error handling message from {addr} (Invalid R-MESH packet): {e}")
        except Exception as e:
            logging.error(f"Error handling message from {addr}: {e}")

    def start_udp_server(self):
        udp_server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        udp_server.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 1024 * 1024)  # Buffer设置为1MB
        udp_server.bind((self.local_ip, self.listening_port))
        logging.info(f"UDP server listening on {self.local_ip}:{self.listening_port}")

        with ThreadPoolExecutor(max_workers=20) as executor:
            try:
                while not self.stop_event.is_set():
                    message_data, addr = udp_server.recvfrom(1024)
                    logging.info(f"Received message from {addr}")
                    executor.submit(self.handle_udp_message, message_data, addr)
            except KeyboardInterrupt:
                logging.info("UDP server stopped.")
            except RuntimeError:
                logging.info("UDP server runtime error, exiting.")
            finally:
                udp_server.close()

    def start_tcp_server(self):
        tcp_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        tcp_server.bind((self.local_ip, 12346))
        tcp_server.listen(self.max_connection)
        logging.info(f"TCP server listening on {self.local_ip}:12346")

        try:
            while not self.stop_event.is_set():
                client_socket, addr = tcp_server.accept()
                logging.info(f"Accepted connection from {addr}")
                # if self.node_connected_callback:
                #     self.node_connected_callback(addr)
                client_thread = threading.Thread(target=self.handle_client, args=(client_socket, addr))
                client_thread.daemon = True
                client_thread.start()
        except KeyboardInterrupt:
            logging.info("TCP server stopped.")
        finally:
            tcp_server.close()

    def check_node_disconnections(self):
        while not self.stop_event.is_set():
            now = datetime.now(timezone.utc)
            with self.nodes_lock:
                for mac, last_report_time in list(self.nodes.items()):
                    if now - last_report_time > timedelta(seconds=self.report_timeout):
                        del self.nodes[mac]
                        if self.node_disconnected_callback:
                            self.node_disconnected_callback(mac)
                        logging.info(f"Node {mac} disconnected due to timeout")
            time.sleep(5)

    def start(self, protocol: ConnectionProtocol):
        self.start_broadcast()
        if protocol is ConnectionProtocol.UDP:
            self.udp_server_thread = threading.Thread(target=self.start_udp_server)
            self.udp_server_thread.daemon = True
            self.udp_server_thread.start()
        elif protocol is ConnectionProtocol.TCP:
            self.tcp_server_thread = threading.Thread(target=self.start_tcp_server)
            self.tcp_server_thread.daemon = True
            self.tcp_server_thread.start()
        else:
            raise RuntimeError
        self.node_check_thread = threading.Thread(target=self.check_node_disconnections)
        self.node_check_thread.daemon = True
        self.node_check_thread.start()

    def stop(self):
        self.stop_broadcast()
        self.stop_event.set()
        if self.tcp_server_thread:
            self.tcp_server_thread.join()
        if self.node_check_thread:
            self.node_check_thread.join()
        if self.udp_server_thread:
            self.udp_server_thread.join()

    def set_node_connected_callback(self, callback):
        self.node_connected_callback = callback

    def set_node_disconnected_callback(self, callback):
        self.node_disconnected_callback = callback

    def set_node_report_callback(self, callback):
        self.node_report_callback = callback
