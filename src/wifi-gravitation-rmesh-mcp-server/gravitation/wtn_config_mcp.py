import math
from .enums import ConnectionType, Direction, ConnectionProtocol

from .utils import optional_chain, ensure_user_config, load_config

logging_enabled = True
config_path = ensure_user_config()
#user_config = load_config()
user_config = {}

REMOTE_CONNECTION_PROTOCOL = ConnectionProtocol[optional_chain(user_config, 'basic', 'remote_connection_protocol') or ConnectionProtocol.UDP.value]
SCAN_LIST_REFRESH_PERIOD = 10

PING_TEXT_ANGLE = 30
VERTICAL_LINK_LENGTH = optional_chain(user_config, 'layout', 'vertical_link_length') or 6
HORIZONTAL_LINK_LENGTH = optional_chain(user_config, 'layout', 'horizontal_link_length') or 13
ALLOW_DRAG_IN_REMOTE_MODE = True
Node_Mode = ConnectionType[optional_chain(user_config, 'basic', 'node_mode') or ConnectionType.SOCKET.value]
# in second
REMOTE_NODE_TIMEOUT = optional_chain(user_config, 'basic', 'remote_connection_timeout') or 60
#ap_mac_list = optional_chain(user_config, 'basic', 'ap_mac_list') or ["f4:2a:7d:c4:09:13", "f4:2a:7d:c4:09:11"]
ap_mac_list = optional_chain(user_config, 'basic', 'ap_mac_list') or ["78:8c:b5:7b:1e:6e"]
ssid = optional_chain(user_config, 'basic', 'ssid') or "WDR5620_5G"
password = optional_chain(user_config, 'basic', 'password') or "12345678"
ui_redraw_interval = optional_chain(user_config, 'basic', 'ui_redraw_interval') or 200
layout_on_demand = optional_chain(user_config, 'layout', 'layout_on_demand') or False
LAYOUT_MODE = optional_chain(user_config, 'layout', 'layout_mode') or "horizontal"
RNAT_ENABLE = optional_chain(user_config, 'layout', 'rnat_enable') or False
cmd_prefix = "AT+WLDBG=wtn"

auto_add_timeout = 10
serial_port_scan_interval = 1000 # in ms
distance_per_grid = 1

ping_rtt_aver_window_size = optional_chain(user_config, 'ping', 'rtt_average_window_size') or 10
ping_interval = optional_chain(user_config, 'ping', 'interval') or 500
ping_packet_size = optional_chain(user_config, 'ping', 'packet_size') or 64
ping_timeout_sec = optional_chain(user_config, 'ping', 'timeout_sec') or 4

clear_log_files = True
log_file_expire_threshold_in_ten_minutes = 3
keep_empty_line_in_log = False

# OTA Settings
OTA_RETRY_DELAY_S = optional_chain(user_config, 'ota', 'ota_retry_delay_s') or 3
OTA_RETRY_INTERVAL_S = optional_chain(user_config, 'ota', 'ota_retry_interval_s') or 2
ota_retry_max_attempts = optional_chain(user_config, 'ota', 'ota_retry_max_attempts') or 5

#location and move
ap_x = 20
ap_y = 25
#x,y,com index
node_locations_vs_ap = [
    [7, 10, 255],  [7, -10, 255], [20, 15, 255],  [20, -15, 255],  [30, 15, 255],  [30, -15, 255],
    [-7, 10, 255], [-7, -10, 255],[-20, 15, 255], [-20, -15, 255]
    ]
move_speed = 8
change_direction_move_count = 80  # Change direction after how many iteration
auto_move_interval = 2000  # ms
auto_move_top_margin = 7
auto_move_right_margin = 10

enable_all_mode = False

# RANDOM / PACE_HORIZONTALLY
movement_mode = "PACE_HORIZONTALLY"
first_link_ap = 0 # then close it, auto connect can work

env_n = 2.5 #自由空间	2 全开放环境	2.5 半开放环境	3
band = "5G" # 2G or 5G
band_constant_map = {"2G": 40.225094, "5G": 47.249026}
band_constant = band_constant_map[band]
tx_power = 20 # 20 dbm

wall_attenuation = 10

def get_rssi_by_distance(cur_dis):
    return tx_power - (env_n * 10 * math.log(cur_dis, 10) + band_constant)
