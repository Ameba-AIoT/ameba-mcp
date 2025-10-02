import struct
import logging


# =========================================================================
# 以下的辅助函数和常量定义保持不变，因为它们独立于 PacketModel 的实现
def format_mac_address(mac):
    if len(mac) != 12:
        raise ValueError("MAC地址必须是12个字符的字符串")

    formatted_mac = ':'.join(mac[i:i + 2] for i in range(0, 12, 2))

    return formatted_mac


ETH_ALEN = 6
BUILD_LEN = 19
OTA_VER_LEN = 21


# =========================================================================


class PacketModel:
    def __init__(self, parsed_dict: dict):
        """
        [重构后] 构造函数，使用一个已经解析好的字典来初始化对象属性。
        这扮演了一个适配器的角色，将新的字典格式数据适配到旧的对象属性接口。

        :param parsed_dict: 由 rmesh_protocol.parse_payload 生成的数据字典。
        """
        # 从字典中获取值并赋给实例属性。使用 .get() 方法可以安全地处理可选字段。
        # 注意：字典中的键名需要与 rmesh_protocol.py 中 PAYLOAD_DEFINITIONS 定义的 'name' 一致。

        # 为了兼容旧的属性名，这里我们将新字典的键名映射到旧的属性名上。
        self.packet_type = parsed_dict.get('packet_type', 0)  # packet_type 现在由外部传入
        self.self_mac = parsed_dict.get('self_mac', '00:00:00:00:00:00')
        self.father_mac = parsed_dict.get('father_mac', '00:00:00:00:00:00')
        self.candidate_mac = parsed_dict.get('candidate_mac', '00:00:00:00:00:00')
        self.father_score = parsed_dict.get('father_score', -128)
        self.candidate_score = parsed_dict.get('candidate_score', -128)
        self.self_ip = parsed_dict.get('self_ip', '0.0.0.0')
        self.self_aid = parsed_dict.get('self_aid', 0)
        self.bssid = parsed_dict.get('ap_bssid', '00:00:00:00:00:00')

        # 键名映射：新标准中是 'compile_time'，旧模型是 'build'
        self.build = parsed_dict.get('compile_time', '')

        # 键名映射：新标准中是 'is_rnat' (布尔值)，旧模型是 'rnat_flag'
        self.rnat_flag = parsed_dict.get('is_rnat', False)

        # 新标准中是 'ota_version'，旧模型也是 'ota_version'
        self.ota_version = parsed_dict.get('ota_version', '')

        self.node_name = parsed_dict.get('node_name', '')

        # scan_list 的结构是兼容的
        self.scan_list = parsed_dict.get('node_list', [])

        # 补充的额外字段
        self.scan_total = len(self.scan_list)

    def __repr__(self):
        attributes = ", ".join(f"{key}={value!r}" for key, value in self.__dict__.items())
        return f"{self.__class__.__name__}({attributes})"

