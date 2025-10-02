from enum import Enum

class ConnectionType(Enum):
    UART = "UART"
    SOCKET = "SOCKET"

class ConnectionProtocol(Enum):
    TCP = "TCP"
    UDP = "UDP"

class Direction(Enum):
    RIGHT = 'right'
    DOWN = 'down'
    LEFT = 'left'
    UP = 'up'
