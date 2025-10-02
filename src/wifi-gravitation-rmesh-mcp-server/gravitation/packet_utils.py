import struct
from enum import IntEnum
from typing import Tuple

# -----------------------------------------------------------------------------
# 1. 协议常量定义 (Protocol Constants Definition)
#    - 将协议规范中的“魔术数字”定义为常量，增强可读性和可维护性。
#    - 明确定义网络字节序（大端），确保跨平台一致性。
# -----------------------------------------------------------------------------

MAGIC_CODE: bytes = b'R-MESH'  # 6-byte Magic Code: 52 2d 4d 45 53 48
PROTOCOL_VERSION: int = 0  # 1-byte Version

# 头部结构格式: > (Big-Endian) 6s (6-byte str) B (u_char) B (u_char) H (u_short)
HEADER_FORMAT: str = '>6sBBH'
HEADER_LENGTH: int = struct.calcsize(HEADER_FORMAT)  # 计算得到 10 bytes

MAX_PAYLOAD_SIZE: int = 65535  # 由2字节的Packet Length决定


# -----------------------------------------------------------------------------
# 2. 包类型枚举 (Packet Type Enumeration)
#    - 使用 IntEnum 替代字典或普通的整数，代码更清晰，类型更安全。
# -----------------------------------------------------------------------------

class PacketType(IntEnum):
    """R-MESH数据包类型"""
    NODE_REPORT = 1
    TOOL_ANNOUNCE = 2
    OTA_REQUEST = 3
    ZRPP_AGREE = 4


# -----------------------------------------------------------------------------
# 3. 核心封包函数 (Core Packing Function)
#    - 单一、通用的函数处理所有类型的包，消除了特例。
#    - 直接、高效，专注于数据转换。
# -----------------------------------------------------------------------------

def pack_rmesh_packet(packet_type: PacketType, payload: bytes = b'') -> bytes:
    """
    将给定的数据封装成一个标准的 R-MESH 数据包。

    这个函数是整个封包逻辑的核心，它遵循一个通用的逻辑来构建数据包头部，
    然后将负载附加在后面。这种设计消除了为不同包类型编写特殊处理代码的需要。

    Args:
        packet_type (PacketType): 数据包的类型，从 PacketType 枚举中选择。
        payload (bytes): 数据包的负载内容。默认为空字节串。

    Returns:
        bytes: 完整的数据包字节串。

    Raises:
        ValueError: 如果负载的长度超过了协议定义的最大值 (65535 字节)。
    """
    payload_len = len(payload)
    if payload_len > MAX_PAYLOAD_SIZE:
        raise ValueError(f"Payload size {payload_len} exceeds maximum of {MAX_PAYLOAD_SIZE} bytes.")

    # 1. 直接使用 struct.pack 构建头部。
    #    这是处理二进制数据最直接、性能最高的方式。
    #    数据流: Python原生类型 -> 二进制头部
    header = struct.pack(
        HEADER_FORMAT,
        MAGIC_CODE,
        PROTOCOL_VERSION,
        packet_type.value,  # 直接使用IntEnum的值
        payload_len
    )

    # 2. 拼接头部和负载，返回最终数据包。
    return header + payload


# -----------------------------------------------------------------------------
# 4. 核心解包函数 (Core Unpacking Function)
#    - 新增的函数，用于解析收到的字节流。
#    - 包含完整的验证逻辑，确保数据包的完整性和有效性。
# -----------------------------------------------------------------------------

def unpack_rmesh_packet(data: bytes) -> Tuple[PacketType, bytes]:
    """
    解析一个 R-MESH 数据包字节串，返回其类型和负载。

    该函数执行以下步骤：
    1. 检查数据长度是否足以包含一个完整的头部。
    2. 解析头部以获取 Magic Code、版本、类型和负载长度。
    3. 验证 Magic Code 和协议版本是否正确。
    4. 检查数据包的实际总长度是否与头部中声明的长度相符。
    5. 将整型的包类型转换为 PacketType 枚举。
    6. 提取并返回负载。

    Args:
        data (bytes): 收到的原始数据包字节串。

    Returns:
        Tuple[PacketType, bytes]: 一个元组，包含解析出的包类型(PacketType)和负载(bytes)。

    Raises:
        ValueError: 如果数据包无效（例如，太短、Magic Code错误、长度不匹配、版本不兼容或类型未知）。
    """
    # 1. 验证数据长度是否至少包含一个头部
    if len(data) < HEADER_LENGTH:
        raise ValueError(f"Invalid packet: data length {len(data)} is shorter than header length {HEADER_LENGTH}.")

    # 2. 解包头部
    header_tuple = struct.unpack(HEADER_FORMAT, data[:HEADER_LENGTH])
    magic_code, version, packet_type_val, payload_len = header_tuple

    # 3. 验证字段
    if magic_code != MAGIC_CODE:
        raise ValueError(f"Invalid packet: incorrect magic code '{magic_code.decode(errors='ignore')}'.")

    if version != PROTOCOL_VERSION:
        raise ValueError(f"Invalid packet: version mismatch. Expected {PROTOCOL_VERSION}, got {version}.")

    # 4. 验证数据包总长度
    expected_total_len = HEADER_LENGTH + payload_len
    if len(data) != expected_total_len:
        raise ValueError(f"Invalid packet: length mismatch. Header indicates {payload_len} payload bytes "
                         f"(total {expected_total_len}), but received {len(data)} bytes.")

    # 5. 转换并验证包类型
    try:
        packet_type = PacketType(packet_type_val)
    except ValueError:
        raise ValueError(f"Invalid packet: unknown packet type value {packet_type_val}.")

    # 6. 提取负载
    payload = data[HEADER_LENGTH:]

    return packet_type, payload
