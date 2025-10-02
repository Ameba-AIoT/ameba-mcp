import struct
import socket
from enum import Enum, IntEnum
from typing import Callable, Any, Dict, List, Tuple
import random


# =============================================================================
#  SECTION 1: R-MESH PAYLOAD PARSER & PACKER (业务负载层)
#  - 由数据结构驱动，遵循TLV格式，逻辑通用。
# =============================================================================

class PayloadType(Enum):
    """业务负载类型定义"""
    NODE_REPORT = 1
    TOOL_ANNOUNCE = 2
    OTA_REQUEST = 3
    ZRPP_AGREE = 4


# --- Helper Functions for Data Conversion (Unpacking) ---
# 这些是通用的、原子化的解析器，可被复用

def _format_mac(mac_bytes: bytes) -> str:
    """将6字节的MAC地址转换为 xx:xx:xx:xx:xx:xx 格式的字符串。"""
    return ":".join(f"{b:02x}" for b in mac_bytes)


def _bytes_to_ip(ip_bytes: bytes) -> str:
    """将4字节的IP地址转换为 xxx.xxx.xxx.xxx 格式的字符串。"""
    return socket.inet_ntoa(ip_bytes)


def _parse_s8(value_bytes: bytes) -> int:
    """解析一个单字节有符号整数。"""
    return struct.unpack('!b', value_bytes)[0]


def _parse_u16(value_bytes: bytes) -> int:
    """解析一个大端序2字节无符号整数。"""
    return struct.unpack('!H', value_bytes)[0]


def _parse_u32(value_bytes: bytes) -> int:
    """解析一个大端序4字节无符号整数。"""
    return struct.unpack('!I', value_bytes)[0]


def _parse_bool(value_bytes: bytes) -> bool:
    """解析一个单字节布尔值。"""
    return bool(value_bytes[0])


def _parse_utf8(value_bytes: bytes) -> str:
    """将字节解析为UTF-8字符串。"""
    return value_bytes.decode('utf-8')


def _parse_utf8_from_fixed_buffer(value_bytes: bytes) -> str:
    """
    从一个固定长度的字节缓冲区中解析一个以 null ('\x00') 结尾的UTF-8字符串。
    这适用于C语言风格的字符串填充在固定大小char数组中的情况。
    """
    # 查找第一个 null 字符的位置
    null_pos = value_bytes.find(b'\x00')

    # 如果找到了 null 字符，则只截取它之前的部分
    if null_pos != -1:
        effective_bytes = value_bytes[:null_pos]
    else:
        # 如果没有找到 null (不规范，但做兼容处理)，则假定整个缓冲区都是有效内容
        effective_bytes = value_bytes

    # 将有效字节部分解码为UTF-8字符串
    return effective_bytes.decode('utf-8')


def _parse_node_list(value_bytes: bytes) -> list:
    """
    解析 Type1 Node Report 中的 Node list 字段 (ID 12)。
    结构: (1 byte mac[5] + 1 byte score + 1 byte can_help_num) * n
    """
    node_list = []
    entry_size = 3  # 每个条目3字节
    for i in range(0, len(value_bytes), entry_size):
        entry_bytes = value_bytes[i:i + entry_size]
        if len(entry_bytes) == entry_size:
            mac_last_byte = entry_bytes[0]
            score = struct.unpack('!b', entry_bytes[1:2])[0]  # score 是有符号整数
            can_help_num = entry_bytes[2]
            node_list.append({
                'mac_last_byte': f"{mac_last_byte:02x}",
                'score': score,
                'can_help_num': can_help_num
            })
    return node_list


def _parse_mac_list(value_bytes: bytes) -> list:
    """解析由多个6字节MAC地址组成的列表。"""
    mac_list = []
    mac_size = 6
    for i in range(0, len(value_bytes), mac_size):
        mac_bytes = value_bytes[i:i + mac_size]
        if len(mac_bytes) == mac_size:
            mac_list.append(_format_mac(mac_bytes))
    return mac_list


# --- Core Data Structure: Protocol Definition ---
# 这是本次重构的核心。代码由数据驱动，而非冗长的if/else。
# 格式: { field_id: ('field_name_in_dict', parser_function) }
PAYLOAD_DEFINITIONS = {
    PayloadType.NODE_REPORT: {
        1: ('self_mac', _format_mac),
        2: ('father_mac', _format_mac),
        3: ('candidate_mac', _format_mac),
        4: ('father_score', _parse_s8),
        5: ('candidate_score', _parse_s8),
        6: ('self_ip', _bytes_to_ip),
        7: ('self_aid', _parse_u16),
        8: ('ap_bssid', _format_mac),
        9: ('compile_time', _parse_utf8),
        10: ('is_rnat', _parse_bool),
        11: ('ota_version', _parse_utf8_from_fixed_buffer),
        12: ('ota_duration_s', _parse_u16),
        13: ('node_list', _parse_node_list),
        14: ('request_pair_list', _parse_mac_list),
        100: ('node_name', _parse_utf8_from_fixed_buffer),
    },
    PayloadType.TOOL_ANNOUNCE: {
        1: ('random_byte', lambda b: b[0]),
        2: ('pc_ip', _bytes_to_ip),
        3: ('report_port', _parse_u16),  # 根据最新文档，端口长度为2字节
    },
    PayloadType.OTA_REQUEST: {
        1: ('request_seq', lambda b: b[0]),
        2: ('destination_mac', _format_mac),
        3: ('host_server_ip', _parse_utf8),
        4: ('host_server_port', _parse_u16),
        5: ('ota_file_name', _parse_utf8),
        6: ('ota_type', lambda b: b[0]),
    },
    PayloadType.ZRPP_AGREE: {
        1: ('agreed_devices_list', _parse_mac_list),
    }
}


# --- Main Payload Parser (Unpacking) ---

def parse_payload(payload_bytes: bytes, payload_type: PayloadType) -> Dict[str, Any]:
    """
    通用的 R-MESH 负载解析器。
    将遵循 TLV (Type-Length-Value) 格式的负载字节流解析为字典。
    此函数由 PAYLOAD_DEFINITIONS 数据结构驱动，简洁且易于扩展。

    :param payload_bytes: 从 R-MESH 包中提取的原始负载字节。
    :param payload_type: 负载的类型 (使用 PayloadType 枚举)。
    :return: 一个包含解析后数据的字典。
    :raises ValueError: 如果负载字节流格式不正确或残缺。
    """
    parsed_data = {}
    offset = 0
    payload_len = len(payload_bytes)

    definitions = PAYLOAD_DEFINITIONS.get(payload_type)
    if not definitions:
        raise ValueError(f"不支持的负载类型或未定义: {payload_type}")

    while offset < payload_len:
        if offset + 2 > payload_len:
            raise ValueError(f"数据包残缺：在偏移量 {offset} 处无法读取ID和Length。")

        field_id = payload_bytes[offset]
        field_len = payload_bytes[offset + 1]
        offset += 2

        if offset + field_len > payload_len:
            raise ValueError(f"ID {field_id} 的声明长度 {field_len} 超出数据包边界。")

        value_bytes = payload_bytes[offset: offset + field_len]
        offset += field_len

        rule = definitions.get(field_id)
        if rule:
            field_name, parser_func = rule
            try:
                parsed_data[field_name] = parser_func(value_bytes)
            except Exception as e:
                raise ValueError(f"解析ID {field_id} (字段'{field_name}')失败: {e}")
        else:
            parsed_data[f'unknown_id_{field_id}'] = value_bytes.hex()

    return parsed_data


# --- Packing Functions ---

def _build_tlv_entry(field_id: int, value_bytes: bytes) -> bytes:
    """一个通用的帮助函数，用于构建单个TLV条目。"""
    field_len = len(value_bytes)
    if not (0 <= field_id <= 255 and 0 <= field_len <= 255):
        raise ValueError(f"Field ID ({field_id}) or Length ({field_len}) out of byte range (0-255).")

    return bytes([field_id, field_len]) + value_bytes


def pack_tool_announce(random_byte: int, pc_ip: str, report_port: int) -> bytes:
    """打包一个 'Tool Announce' (Type 2) 负载。"""
    parts = [
        _build_tlv_entry(1, bytes([random_byte])),
        _build_tlv_entry(2, socket.inet_aton(pc_ip)),
        _build_tlv_entry(3, struct.pack('!H', report_port))  # !H for 2-byte port
    ]
    return b''.join(parts)


def pack_ota_request(request_seq: int, destination_mac: str, host_server_ip: str, host_server_port: int,
                     ota_file_name: str, ota_type: int) -> bytes:
    """打包一个 'OTA Request' (Type 3) 负载。"""
    if not (1 <= request_seq <= 255):
        raise ValueError("Request sequence must be between 1 and 255.")

    mac_bytes = bytes.fromhex(destination_mac.replace(":", ""))
    parts = [
        _build_tlv_entry(1, bytes([request_seq])),
        _build_tlv_entry(2, mac_bytes),
        _build_tlv_entry(3, host_server_ip.encode('utf-8')),
        _build_tlv_entry(4, struct.pack('!H', host_server_port)),
        _build_tlv_entry(5, ota_file_name.encode('utf-8')),
        _build_tlv_entry(6, bytes([ota_type]))
    ]
    return b''.join(parts)


def pack_zrpp_agree(mac_list: List[str]) -> bytes:
    """打包一个 'ZRPP Agree' (Type 4) 负载。"""
    if not mac_list:
        return _build_tlv_entry(1, b'')

    # 将所有MAC地址字符串转换为一个连续的字节块
    all_mac_bytes = b''.join(bytes.fromhex(mac.replace(':', '')) for mac in mac_list)

    return _build_tlv_entry(1, all_mac_bytes)


# =============================================================================
#  SECTION 2: R-MESH PACKET FRAMING (协议帧层)
#  - 这是您提供的代码，用于处理协议的头部和尾部，与业务负载层解耦。
# =============================================================================

MAGIC_CODE: bytes = b'R-MESH'
PROTOCOL_VERSION: int = 0
HEADER_FORMAT: str = '>6sBBH'  # Big-Endian: 6s B B H
HEADER_LENGTH: int = struct.calcsize(HEADER_FORMAT)  # 10 bytes
MAX_PAYLOAD_SIZE: int = 65535


class RmeshPacketType(IntEnum):
    """R-MESH数据包类型 (与业务层 PayloadType 保持一致)"""
    NODE_REPORT = 1
    TOOL_ANNOUNCE = 2
    OTA_REQUEST = 3
    ZRPP_AGREE = 4


def pack_rmesh_packet(packet_type: RmeshPacketType, payload: bytes = b'') -> bytes:
    """将给定的数据封装成一个标准的 R-MESH 数据包。"""
    payload_len = len(payload)
    if payload_len > MAX_PAYLOAD_SIZE:
        raise ValueError(f"Payload size {payload_len} exceeds maximum of {MAX_PAYLOAD_SIZE} bytes.")
    header = struct.pack(HEADER_FORMAT, MAGIC_CODE, PROTOCOL_VERSION, packet_type.value, payload_len)
    return header + payload


def unpack_rmesh_packet(data: bytes) -> Tuple[RmeshPacketType, bytes]:
    """解析一个 R-MESH 数据包字节串，返回其类型和负载。"""
    if len(data) < HEADER_LENGTH:
        raise ValueError(f"Invalid packet: data length {len(data)} is shorter than header length {HEADER_LENGTH}.")
    magic_code, version, packet_type_val, payload_len = struct.unpack(HEADER_FORMAT, data[:HEADER_LENGTH])
    if magic_code != MAGIC_CODE:
        raise ValueError(f"Invalid packet: incorrect magic code '{magic_code.decode(errors='ignore')}'.")
    if version != PROTOCOL_VERSION:
        raise ValueError(f"Invalid packet: version mismatch. Expected {PROTOCOL_VERSION}, got {version}.")
    expected_total_len = HEADER_LENGTH + payload_len
    if len(data) != expected_total_len:
        raise ValueError(
            f"Invalid packet: length mismatch. Header indicates {payload_len}, but received {len(data)} bytes total.")
    try:
        packet_type = RmeshPacketType(packet_type_val)
    except ValueError:
        raise ValueError(f"Invalid packet: unknown packet type value {packet_type_val}.")
    payload = data[HEADER_LENGTH:]
    return packet_type, payload


# =============================================================================
#  SECTION 3: 如何使用与集成 (Usage and Integration Example)
# =============================================================================
if __name__ == "__main__":

    print("--- 场景1: Tool发送 'Tool Announce' 数据包 ---")
    # 1a. 业务层: 打包负载 (Payload)
    tool_announce_payload = pack_tool_announce(
        random_byte=random.randint(1, 255),
        pc_ip="192.168.1.101",
        report_port=12346
    )
    print(f"业务负载 (Payload): {tool_announce_payload.hex(' ')}")

    # 1b. 协议帧层: 将负载封装成完整的数据包
    full_packet_tool = pack_rmesh_packet(
        packet_type=RmeshPacketType.TOOL_ANNOUNCE,
        payload=tool_announce_payload
    )
    print(f"完整数据包 (Full Packet): {full_packet_tool.hex(' ')}")
    print("-" * 50)

    print("--- 场景2: Tool发送 'ZRPP Agree' 数据包 ---")
    # 2a. 业务层: 打包负载
    zrpp_agree_payload = pack_zrpp_agree(
        mac_list=[
            "00:e0:4c:00:0d:4e",
            "00:e0:4c:00:0d:4f",
            "00:e0:4c:00:0d:50"
        ]
    )
    print(f"业务负载 (Payload): {zrpp_agree_payload.hex(' ')}")

    # 2b. 协议帧层: 封装
    full_packet_zrpp = pack_rmesh_packet(
        packet_type=RmeshPacketType.ZRPP_AGREE,
        payload=zrpp_agree_payload
    )
    print(f"完整数据包 (Full Packet): {full_packet_zrpp.hex(' ')}")
    print("-" * 50)

    print("--- 场景3: Tool接收并解析 'Node Report' 数据包 ---")
    # 3a. 模拟一个收到的 Node Report 完整数据包
    #     (通常这部分字节流来自 socket.recvfrom)
    sample_node_report_payload = bytes([
        1, 6, 0x00, 0xe0, 0x4c, 0x00, 0x0d, 0x4d,  # ID 1: Self MAC
        6, 4, 192, 168, 1, 101,  # ID 6: Self IP
        4, 1, 0xde,  # ID 4: Father Score (-34)
        9, 19, *b'2025-03-05 09:00:39',  # ID 9: Compile Time
        12, 6, 0x1b, 0xde, 0x03, 0x1c, 0xde, 0x04  # ID 12: Node List (2 entries)
    ])
    full_packet_report = pack_rmesh_packet(RmeshPacketType.NODE_REPORT, sample_node_report_payload)
    print(f"收到的原始数据包: {full_packet_report.hex(' ')}")

    # 3b. 协议帧层: 解包，分离出头部信息和负载
    try:
        unpacked_type, received_payload = unpack_rmesh_packet(full_packet_report)
        print(f"解包成功: Type={unpacked_type.name}, Payload Length={len(received_payload)}")

        # 3c. 业务层: 解析负载
        if unpacked_type == RmeshPacketType.NODE_REPORT:
            # 将 RmeshPacketType 转换为 PayloadType, 虽然值一样，但这是好的实践
            payload_type_enum = PayloadType(unpacked_type.value)
            report_data = parse_payload(received_payload, payload_type_enum)

            # 3d. 业务逻辑: 使用解析好的数据
            print("\n解析后的业务数据:")
            import json

            print(json.dumps(report_data, indent=2))

    except ValueError as e:
        print(f"数据包处理失败: {e}")

