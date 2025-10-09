import os
import sys
import time
from datetime import datetime
from enum import Enum
from statistics import mean
from typing import Optional

#import color_config
import gravitation.wtn_config_mcp as wtn_config_mcp
from .enums import ConnectionType
# from wtn_dut import default_mac
from .wtn_control_mcp import default_ip, default_mac

from .wtn_log_filter import should_drop
from .wtn_ping import PingMonitor


class Node:
    def __init__(self, id, enable=wtn_config_mcp.enable_all_mode, mac=None):
        self.id = id
        self.com = "?"
        # from wtn_dut import default_mac
        self.mac = mac or default_mac
        self.node_text = None
        self.ping_text = None
        self.device = None
        self.status = "default"
        self.rssi_table = {}
        self.relation_line = None
        self.relation_line_mark = None
        self.secondary_line = None
        # self.secondary_line_mark = None
        self.father_node = None
        self.father_mac = default_mac
        self.candidate_mac = default_mac
        from gravitation.wtn_control_mcp import default_ip
        self.ip = default_ip
        self.children = []
        self.ping_monitor: Optional[PingMonitor] = None
        self.ping_rtt_history = []
        # store (time, package_size) tuple
        self.log_file = None
        self.output_cache = ""
        self.children_text = ""
        self.bssid = None
        self.score = None
        self.aid = None
        self.debug_text = None
        self.mesh_enable = enable
        self.power_off = 0
        self.should_relocate = False
        self.online = True
        self.last_report_timestamp: datetime | None = None
        self.reconnect_counter = 0
        self.scan_list = []
        self.build = ""
        self.rnat_flag: bool | None = None
        self.node_name = ""
        self.node_sta_type = ""

    def __del__(self):
        if self.ping_monitor:
            self.ping_monitor.stop()
        self.ping_monitor = None
        self.ui = None

    # def node_color(self):
    #     return color_config.enable_color if self.mesh_enable else color_config.disable_color

    def save_log(self, data):
        current_time = datetime.now().strftime("%H:%M:%S:%f")[:-3]
        lines = data.splitlines()
        result = ""
        for line in lines:
            if should_drop(line.strip()):
                continue
            if line.strip():
                result += f"{current_time} {line.lstrip()}\n"
            elif wtn_config_mcp.keep_empty_line_in_log:
                result += "\n"

        if self.log_file:
            with open(self.log_file, 'a') as file:
                if self.output_cache:
                    file.write(self.output_cache)
                    self.output_cache = None
                file.write(result)
        elif self.output_cache:
            self.output_cache += result

    def set_device(self, device):
        self.device = device

        # set log file path
        self.log_file = os.path.join(os.getcwd(), "logs",
                                     f"{datetime.now().strftime('%Y%m%d_%H%M%S_%f')[:-3]}_{self.com}_{self.mac.split(':')[-1]}.txt")
        directory = os.path.dirname(self.log_file)
        if not os.path.exists(directory):
            os.makedirs(directory)
        self.status = "root"

    def update_children_info(self, text):
        from gravitation.wtn_control_mcp import default_ip
        print(f"Update children info for {self.mac}: {text}", file=sys.stderr)
        self.children_text = text
        # won't update ui when pinging
        if self.ping_monitor and not self.ping_monitor.stop_event.is_set():
            return

    def add_ping_monitor(self):
        from gravitation.wtn_control_mcp import default_ip

        # ip changes
        if self.ping_monitor and not self.ping_monitor.stop_event.is_set() and self.ip != self.ping_monitor.ip_address:
            self.stop_ping_and_clear()

        # start ping monitor, only add New monitor when self.ping_monitor is None
        if self.ip != default_ip and not self.ping_monitor:
            self.ping_monitor = PingMonitor(self.ip, callback=self.ping_update,
                                            icmp_packet_size=wtn_config_mcp.ping_packet_size,
                                            interval=wtn_config_mcp.ping_interval,
                                            ping_timeout_sec=wtn_config_mcp.ping_timeout_sec)
            self.ping_monitor.start()

    def calculate_packet_loss(self, success_count: int, failure_count: int) -> float:
        total_count = success_count + failure_count
        if total_count == 0:
            return 0.0  # avoid /0 error
        loss_rate = (failure_count / total_count) * 100
        return round(loss_rate, 1)

    def ping_update(self, ip_address, status, latency, ttl, success_count, failure_count, start_time):
        if latency:
            self.ping_rtt_history.append(latency)

        # solve StatisticsError('mean requires at least one data point')
        if len(self.ping_rtt_history) > 1:
            delay = round(mean(map(float, self.ping_rtt_history[-wtn_config_mcp.ping_rtt_aver_window_size:])))
        else:
            delay = round(self.ping_rtt_history[0]) if self.ping_rtt_history else 0
        # Clear history to minimize memory usage
        self.ping_rtt_history = self.ping_rtt_history[-wtn_config_mcp.ping_rtt_aver_window_size:]
        # com/mac/ip addr/ping ok/ping loss/ping delay/ping TP
        ping_result = f"p:{success_count} / {failure_count}-{self.calculate_packet_loss(success_count, failure_count)}% / {delay}"
        from gravitation.wtn_control_mcp import ping_results
        ping_results[self.id] = ping_result

    def stop_ping_and_clear(self):
        self.ping_rtt_history = []
        self.ping_monitor.stop()
        self.ping_monitor = None
        from gravitation.wtn_control_mcp import ping_results
        ping_results.pop(self.id, None)

    def clear_ping_history(self):
        if self.ping_monitor:
            self.ping_monitor.clear()
        self.ping_rtt_history = []
        from gravitation.wtn_control_mcp import ping_results
        ping_results.pop(self.id, None)

    def set_com(self, com):
        self.com = com

    def add_item_to_rssi_table(self, rssi_map_item):
        from gravitation.wtn_control_mcp import default_mac
        if rssi_map_item[0] == default_mac:
            return
        if rssi_map_item[0] in self.rssi_table:
            self.rssi_table[rssi_map_item[0]] = rssi_map_item[1]
        else:
            self.rssi_table.update({rssi_map_item[0]: rssi_map_item[1]})

    def get_fix_rssi_str(self):
        str_list = []
        rssi_str = f"{wtn_config_mcp.cmd_prefix} fix_rssi "
        count = 1
        for key, value in self.rssi_table.items():
            rssi_str += f"{key} {value} "
            if count % 2 == 0:
                str_list.append(rssi_str[:-1])
                rssi_str = f"{wtn_config_mcp.cmd_prefix} fix_rssi "
            count += 1
        if rssi_str != f"{wtn_config_mcp.cmd_prefix} fix_rssi ":
            str_list.append(rssi_str[:-1])
        return str_list

    def get_display_text(self):
        if self.mac in wtn_config_mcp.ap_mac_list:
            return f"AP({self.mac.split(":")[-1]})"
        return self.mac.split(":")[-1].upper()

    def get_basic_info_text(self):
        if wtn_config_mcp.Node_Mode is ConnectionType.SOCKET:
           # return (f"{self.mac.split(':')[-1].upper()}:{self.ip}" +
           return (f"mac={self.mac};ip={self.ip};" +
                    (
                        f" ({self.last_report_timestamp.minute}:{self.last_report_timestamp.second})" if self.last_report_timestamp else "") +
                        (
                            f"-{self.reconnect_counter}" if self.reconnect_counter != 0 else "") +
                            f"{("\n" + self.node_name) if self.node_name else ""}"
                            f"{("\n" + self.children_text) if self.children_text else ""}"
                        )
        else:
            return (f"{self.com.replace('COM', '')} / {self.mac.split(':')[-1].upper()}"
                    f"{("\n" + self.children_text) if self.children_text else ""}"
                    f"{("\nscore: " + self.score) if self.score else ""}")

    def get_suffix(self):
        return (f"{f'\naid:{self.aid}' if self.aid else ''}"
                f"{f'\n{self.debug_text}' if self.debug_text else ''}"
                )

    # def __str__(self):
    #     #return f"Node ID: {self.id}, Position: ({self.x}, {self.y}), Com: {self.com}"
    #     return self.get_basic_info_text()

    # def __repr__(self):
    #     #return f"Node ID: {self.id}, Position: ({self.x}, {self.y}), Com: {self.com}"
    #     return self.get_basic_info_text()

    # def macToScoreMap(self):
    #     mac_score_map = {}
    #     parts = self.score.split(', ')
    #     for part in parts:
    #         mac, score = part.split('-')
    #         mac = mac.strip()
    #         score = score.strip()
    #         mac_score_map[mac] = score
    #     return mac_score_map

    def disconnect(self):
        # self.ip = None
        # self.father_node = None
        self.bssid = default_mac
        self.father_mac = default_mac
        self.candidate_mac = default_mac
        self.score = None
        # self.aid = None
        self.online = False
        self.reconnect_counter += 1
        self.scan_list = []

    def get_score_to(self, target_mac: str) -> str | None:
        if self.score:
            scores = self.score.split(', ')
            for part in scores:
                mac, score = part[:17], part[17:]
                if target_mac.lower() == mac.lower():
                    return score
        return None

    def get_candidate_mac(self) -> str | None:
        if self.score:
            scores = self.score.split(', ')
            if len(scores) > 1:
                return scores[1].split('-')[0].strip()
        return None


class NodeType(Enum):
    UART = "uart"
    REMOTE = "remote"


class NodeStatus(Enum):
    ONLINE = "Online"
    OFFLINE = "Offline"
