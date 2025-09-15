from typing import Any, Dict, List, Optional, Protocol
import socket
import serial

class ConnectionManager:
    """Manages serial and TCP connections for Ameba devices"""
    def __init__(self):
        # Serial connection
        self.serial_port: Optional[serial.Serial] = None
        self.serial_port_name: Optional[str] = None
        
        # TCP connection
        self.tcp_socket: Optional[socket.socket] = None
        self.tcp_host: Optional[str] = None
        self.tcp_port: Optional[int] = None
    
    async def disconnect_all(self):
        """Disconnect all connections"""
        if self.serial_port and self.serial_port.is_open:
            self.serial_port.close()
            self.serial_port = None
            self.serial_port_name = None
        
        if self.tcp_socket:
            self.tcp_socket.close()
            self.tcp_socket = None
            self.tcp_host = None
            self.tcp_port = None