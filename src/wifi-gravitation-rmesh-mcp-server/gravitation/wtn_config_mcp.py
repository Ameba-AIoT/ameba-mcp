import math
from .enums import ConnectionType, Direction, ConnectionProtocol

from .utils import optional_chain, ensure_user_config, load_config

logging_enabled = True
config_path = ensure_user_config()
user_config = load_config()
#user_config = {}

REMOTE_CONNECTION_PROTOCOL = ConnectionProtocol[optional_chain(user_config, 'basic', 'remote_connection_protocol') or ConnectionProtocol.UDP.value]
SCAN_LIST_REFRESH_PERIOD = 10
Node_Mode = ConnectionType[optional_chain(user_config, 'basic', 'node_mode') or ConnectionType.SOCKET.value]
# in second
REMOTE_NODE_TIMEOUT = optional_chain(user_config, 'basic', 'remote_connection_timeout') or 60
ap_mac_list = optional_chain(user_config, 'basic', 'ap_mac_list') or ["44:a5:6e:7c:75:7e"] #["44:a5:6e:7c:75:80"] # ["78:8c:b5:7b:1e:6e"]

RNAT_ENABLE = optional_chain(user_config, 'layout', 'rnat_enable') or False
cmd_prefix = "AT+WLDBG=wtn"

auto_add_timeout = 10
serial_port_scan_interval = 1000 # in ms
distance_per_grid = 1

ping_rtt_aver_window_size = optional_chain(user_config, 'ping', 'rtt_average_window_size') or 10
ping_interval = optional_chain(user_config, 'ping', 'interval') or 500
ping_packet_size = optional_chain(user_config, 'ping', 'packet_size') or 64
ping_timeout_sec = optional_chain(user_config, 'ping', 'timeout_sec') or 4

enable_all_mode = False

env_n = 2.5 #自由空间	2 全开放环境	2.5 半开放环境	3
band = "5G" # 2G or 5G
band_constant_map = {"2G": 40.225094, "5G": 47.249026}
band_constant = band_constant_map[band]
tx_power = 20 # 20 dbm

wall_attenuation = 10

def get_rssi_by_distance(cur_dis):
    return tx_power - (env_n * 10 * math.log(cur_dis, 10) + band_constant)
