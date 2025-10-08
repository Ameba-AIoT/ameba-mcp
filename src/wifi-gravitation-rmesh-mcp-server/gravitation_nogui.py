from asyncio import CancelledError
from gravitation.utils import *
from gravitation.wtn_server import WTNServer
from gravitation.wtn_node import Node
from gravitation.packet_model import PacketModel
from gravitation.wtn_config_mcp import *
from gravitation.wtn_control_mcp import *
import threading
import logging
from datetime import datetime
import time
import re
from typing import Dict, List

class GravitationServer:
    chosen_iface = None
    nodes: Dict[int, Node] = {}
    node_activities_log_file = None
    thread_status = None

    def __init__(self, chosen_iface: str):
        # start monitoring threads
        threading.Thread(target=self.refresh_relation_thread).start()
        self.thread_status = True

        # set node0 as the AP mac. we assume that there is only 1 AP center
        self.nodes[0] = Node(0, mac=ap_mac_list[0])
        self.nodes[0].online = True
        self.nodes[0].bssid = ap_mac_list[0]
        self.nodes[0].mac = ap_mac_list[0]
        self.nodes[0].node_name = f"AP-{self.nodes[0].mac}"

        # start wifi tunnel server
        server = WTNServer(report_timeout=REMOTE_NODE_TIMEOUT, ifname=chosen_iface)
        server.set_node_connected_callback(self.on_node_connected)
        server.set_node_disconnected_callback(self.on_node_disconnected)
        server.set_node_report_callback(self.on_node_report)

        try:
            print("Starting WTN server...")
            server.start(REMOTE_CONNECTION_PROTOCOL)
        except (KeyboardInterrupt, CancelledError):
            self.thread_status = False
            print("WTN server interrupted.")
            raise KeyboardInterrupt
        #server.start(REMOTE_CONNECTION_PROTOCOL)
        
    def configure_logging(self):
        from gravitation.wtn_config_mcp import logging_enabled
        if logging_enabled:
            logging.basicConfig(stream=sys.stderr, level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
        else:
            logging.basicConfig(stream=sys.stderr, level=logging.CRITICAL)  # Only log critical errors

    def refresh_relation_thread(self):
        time.sleep(5)
        print("refresh_relation_thread start", file=sys.stderr)
        while self.thread_status:
            try:
                # if self.need_send_rssi_table:
                #     self.send_rssi_table(None)
                self.draw_connection_to_father()
                # self.draw_connection_to_2nd_target()
            except KeyboardInterrupt:
                #print(f"SerialException3: {e}")
                #traceback.print_exc()
                self.thread_status = False
                print("refresh_relation_thread interrupted.", file=sys.stderr)
            time.sleep(0.5)

    ########## CALLBACKS FOR WTN SERVER ############

    #def on_node_connected(self, addr, rnat_flag):
    def on_node_connected(self, addr, parsed_data: PacketModel):
        logging.info(f"Node connected: {addr}")
        self.add_remote_node(addr, parsed_data.self_ip, parsed_data.rnat_flag)
        current_time = datetime.now().strftime("%H:%M:%S:%f")[:-3]
        if self.node_activities_log_file:
            with open(self.node_activities_log_file, 'a') as file:
                file.write(f"{addr}: online\t{current_time}\n")

    def on_node_disconnected(self, mac):
        current_time = datetime.now().strftime("%H:%M:%S:%f")[:-3]
        if self.node_activities_log_file:
            with open(self.node_activities_log_file, 'a') as file:
                file.write(f"{mac}: offline\t{current_time}\n")
        node = self.find_node_by_mac(mac)
        if node:
            node.disconnect()
            # self.clear_connect_lines_and_marks_for(node)
            self.draw_connection_to_father()
            # self.redraw_connection_to_2nd_target()

        logging.info(f"Node disconnected: {mac}")

    def on_node_report(self, report, packet: PacketModel):
        def resolve_out_put(text, children_update, data_update):
            regex_rules = {
                "mac": r"wtn_self_mac:([\b\w:]+)",
                "bssid": r"wtn_bssid:([\b\w:]+)",
                "father_mac": r"wtn_father:([\b\w:/]+)",
                "ip": r"Interface \d IP address : ([\d\.,]+)",
                "score": r"wtn_score:([\d\.\w, -]+)",
                "aid": r"wtn_aid:(\d+)",
                "debug_text": r"debug:(.*)$",
                "node_name": r"wtn_node_name:([\b\w:/]+)",
            }
            # child-3:%x/%x/%x
            if children_update:
                match = re.search(r"(child-\d+:[\w/]*)", text)
                if match:
                    children_update(match.group(1).strip())
            if data_update:
                for name, regex in regex_rules.items():
                    match = re.search(regex, text)
                    if match:
                        data_update(name, match.group(1).strip())

        def update_node_data(name, value, node):
            # update father_mac handler
            if name == "father_mac" and value != node.father_mac and value != default_mac:
                #print(f"{node} -- {node.father_mac}")
                #logging.info(f"node {node.mac.split(":")[-1]} 's father changed from {node.father_mac.split(":")[-1]} to {value.split(":")[-1]}")
                print(f"node {node.mac.split(":")[-1]} 's father changed from {node.father_mac.split(":")[-1]} to {value.split(":")[-1]}", file=sys.stderr)
                #node.should_relocate = True
                node.father_mac = value

                mac_to_node = {n.mac: n for n in self.nodes.values()}
                father_node = mac_to_node.get(node.father_mac)
                node.father_node = father_node

                # related_nodes: List[Node] = list(filter(lambda n: n.father_mac in [value, node.father_mac], self.nodes.values()))
                # #print(related_nodes)
                # for related_node in related_nodes:
                #     related_node.should_relocate = True

            # update bssid handler
            if name == "bssid":
                node.bssid = value
                if value == node.mac:
                    node.node_name = "AP"
                else:
                    if node.bssid == node.father_mac:
                        node.node_name = "ROOT-" + node.mac
                    else:
                        node.node_name = "STA-" + node.mac
        
        def node_switch_record(node_activities_log_file, packet: PacketModel, mac, node):
            current_time = datetime.now().strftime("%H:%M:%S:%f")[:-3]
            if packet.father_mac != node.father_mac:
                new_father = packet.father_mac
                new_candidate = packet.candidate_mac
                new_father_score = packet.father_score
                new_candidate_score = packet.candidate_score

                old_father = node.father_mac
                old_candidate = node.candidate_mac
                old_father_score = None
                old_candidate_score = None
                if node.score:
                    mac_to_score = {part[:2]: part[2:] for part in node.score.split(', ')}
                    old_father_score = mac_to_score[old_father.split(":")[-1]]
                    old_candidate_score = mac_to_score[old_candidate.split(":")[-1]]

                if node_activities_log_file:
                    with open(node_activities_log_file, 'a') as file:
                        file.write(f"{mac}: switch\t{current_time}\t"
                                f"{old_father.split(":")[-1]}/{old_candidate.split(":")[-1]}[{old_father_score}/{old_candidate_score}]"
                                f" to {new_father.split(":")[-1]}/{new_candidate.split(":")[-1]}[{new_father_score}/{new_candidate_score}]\n")

        mac = report.get("mac")
        node = self.find_node_by_mac(mac)
        try:
            node_switch_record(self.node_activities_log_file, packet, mac, node)
        except Exception as e:
            logging.error(f"node {mac} switch log error: {e}")

        if not node:
            logging.error(f"update info for non-existing node {mac}")
            return
        node.online = True
        node.last_report_timestamp = datetime.now()
        node.build = packet.build
        node.ota_version = packet.ota_version
        original_rnat_flag = node.rnat_flag
        node.rnat_flag = packet.rnat_flag
        ####### RMESH DEMO #########
        node.node_name = packet.node_name
        
        if original_rnat_flag != node.rnat_flag:
            logging.warning(f"Node {mac} rnat_flag changed from {original_rnat_flag} to {node.rnat_flag}")
        node.scan_list = packet.scan_list
        node.candidate_mac = packet.candidate_mac

        # retrieve the report generated from WTN server
        for record in report.get('payload') or []:
            resolve_out_put(record.get('data'), node.update_children_info, lambda name, value: update_node_data(name, value, node))
        logging.info(f"Node report: {packet}")

    def add_remote_node(self, mac, ip, rnat_flag):
        if self.find_node_by_mac(mac):
            # TODO: -redraw connection
            return
        logging.info(f"添加节点: {mac}")

        node_id = None
        for i in range(1, 255):
            if i not in self.nodes:
                node_id = i
                break

        #self.nodes[node_id] = Node(node_id, x, y, self.ui, mac=mac)
        self.nodes[node_id] = Node(node_id, mac=mac)
        self.nodes[node_id].ip = ip
        self.nodes[node_id].rnat_flag = rnat_flag
        print(f"add remote node {node_id} ({mac})", file=sys.stderr)
        selected_node = node_id
        node = self.nodes[selected_node]
        if selected_node not in self.nodes:
            return

        node_text = f"{node.get_basic_info_text()}{node.get_suffix()}"

        # Create the ping_text
        ping_text = ""

        #node.ui = self.ui
        node.node_text = node_text
        node.ping_text = ping_text

    def find_node_by_mac(self, mac)->Node:
        nodes = list(filter(lambda item: item.mac == mac, self.nodes.values()))
        if not nodes:
            logging.info(f"Node {mac} not found")
        elif len(nodes) != 1:
            logging.error(f"wrong node count: {len(nodes)} - {nodes}")
        return nodes[0] if nodes else None
    
    def draw_connection_to_father(self):
        mac_to_node = {n.mac: n for n in self.nodes.values()}
        for key in list(self.nodes.keys()):
            if key not in self.nodes.keys(): # avoid concurrent modify
                continue
            node = self.nodes[key]
            if node:
                pass
                #self.update_node_color(key)
            if not node.online:
                continue

            # this is the AP node
            if node and node.father_mac == default_mac and node.bssid == node.mac:
                node.father_node = None

            # these nodes are STA or ROOT
            if node and node.father_mac and node.father_mac != default_mac:
                father_node = mac_to_node.get(node.father_mac)
                bssid_check_required = not RNAT_ENABLE
                bssid_not_in_ap_list = node.bssid not in ap_mac_list

                # the father was not found, or the bssid is not in the ap list, clear relations
                if not father_node or (bssid_check_required and bssid_not_in_ap_list):
                    if node.relation_line is not None:
                        node.relation_line = None
                    if node.relation_line_mark:
                        node.relation_line_mark = None

                    continue

                # if we reached here, this means that this node has a valid father

                # apply the link to the father node
                node.father_node = father_node

                # after setting the father node, we need to update the father's children list
                if node in father_node.children:
                    pass
                else:
                    # we can only have one father for this node, so remove from other fathers' children list
                    for other_father in self.nodes.values():
                        if node in other_father.children:
                            other_father.children.remove(node)
                    
                    # finally, add to the correct father's children list
                    father_node.children.append(node)

                if node.relation_line is not None:
                    # update the relation to the father
                    pass
                else:
                    node.relation_line = True # placeholder because this is drawn in tkinter
                
                if node.score:
                    try:
                        scores = node.score.split(', ')
                        father_part = scores[0] if len(scores) > 0 else None
                        candidate_part = scores[1] if len(scores) > 1 else None
                        mac, score = father_part[:2], father_part[2:]
                        mac = mac.strip()
                        if candidate_part:
                            score += f"/{candidate_part[2:]}"

                    except ValueError:
                        pass
                else:
                    node.relation_line_mark = None

