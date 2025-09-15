import socket
import serial
from typing import Any, Dict, List, Optional, Protocol
from mcp.types import Tool
from .feature_module import FeatureModule
import asyncio
import json

class ConnectionModule(FeatureModule):
    """Module for basic connection functionality (Serial and TCP)"""
    
    @property
    def module_name(self) -> str:
        return "connection"
    
    def get_tools(self) -> List[Tool]:
        return [
            Tool(
                name="list_ports",
                description="List available serial ports",
                inputSchema={
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            ),
            Tool(
                name="connect",
                description="Connect to Ameba device via serial port",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "port": {"type": "string", "description": "Serial port name (e.g., COM3 or /dev/ttyUSB0)"},
                        "baudrate": {"type": "integer", "description": "Baud rate (default: 115200)"}
                    },
                    "required": ["port"]
                }
            ),
            Tool(
                name="tcp_connect",
                description="Connect to Ameba device via TCP/IP (Telnet on port 23)",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "host": {"type": "string", "description": "IP address or hostname"},
                        "port": {"type": "integer", "description": "TCP port (default: 23 for Telnet)"}
                    },
                    "required": ["host"]
                }
            ),
            Tool(
                name="disconnect",
                description="Disconnect from Ameba device (specify connection type)",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "connection_type": {
                            "type": "string", 
                            "description": "Connection type to disconnect: 'serial', 'tcp', or 'all' (default: 'all')",
                            "enum": ["serial", "tcp", "all"]
                        }
                    },
                    "required": []
                }
            ),
            Tool(
                name="connection_status",
                description="Get current connection status",
                inputSchema={
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            ),
            Tool(
                name="send_command",
                description="Send a command to Ameba device",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "command": {"type": "string", "description": "Command to send"},
                        "connection": {
                            "type": "string", 
                            "description": "Connection to use: 'serial' or 'tcp' (default: auto-detect)",
                            "enum": ["serial", "tcp"]
                        }
                    },
                    "required": ["command"]
                }
            )
        ]
    
    async def handle_tool(self, name: str, arguments: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        if name == "list_ports":
            return await self.list_serial_ports()
        elif name == "connect":
            port = arguments.get("port")
            baudrate = arguments.get("baudrate", 115200)
            return await self.connect_serial(port, baudrate)
        elif name == "tcp_connect":
            host = arguments.get("host")
            port = arguments.get("port", 23)
            return await self.connect_tcp(host, port)
        elif name == "disconnect":
            connection_type = arguments.get("connection_type", "all")
            return await self.disconnect(connection_type)
        elif name == "connection_status":
            return await self.get_connection_status()
        elif name == "send_command":
            command = arguments.get("command")
            connection = arguments.get("connection", None)
            return await self.send_command(command, connection)
        else:
            raise ValueError(f"Unknown tool: {name}")
    
    async def list_serial_ports(self) -> Dict[str, Any]:
        """List all available serial ports"""
        ports = serial.tools.list_ports.comports()
        port_list = []
        for port in ports:
            port_list.append({
                "device": port.device,
                "description": port.description,
                "hwid": port.hwid
            })
        return {"ports": port_list}
    
    async def connect_serial(self, port: str, baudrate: int = 115200) -> Dict[str, Any]:
        """Connect to Ameba device via serial port"""
        try:
            if self.conn.serial_port and self.conn.serial_port.is_open:
                return {
                    "status": "already_connected",
                    "connection_type": "serial",
                    "port": self.conn.serial_port_name,
                    "message": f"Already connected to {self.conn.serial_port_name}"
                }
            
            self.conn.serial_port = serial.Serial(
                port=port,
                baudrate=baudrate,
                timeout=1,
                write_timeout=1
            )
            self.conn.serial_port_name = port
            
            # Send initial command to verify connection
            self.conn.serial_port.write(b"AT\r\n")
            response = self.conn.serial_port.read(100).decode('utf-8', errors='ignore')
            
            return {
                "status": "connected",
                "connection_type": "serial",
                "port": port,
                "baudrate": baudrate,
                "response": response.strip()
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def connect_tcp(self, host: str, port: int = 23) -> Dict[str, Any]:
        """Connect to Ameba device via TCP/IP"""
        try:
            if self.conn.tcp_socket:
                return {
                    "status": "already_connected",
                    "connection_type": "tcp",
                    "host": self.conn.tcp_host,
                    "port": self.conn.tcp_port,
                    "message": f"Already connected to {self.conn.tcp_host}:{self.conn.tcp_port}"
                }
            
            self.conn.tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.conn.tcp_socket.settimeout(5.0)
            
            self.conn.tcp_socket.connect((host, port))
            self.conn.tcp_host = host
            self.conn.tcp_port = port
            
            if port == 23:
                await self._handle_telnet_negotiation()
            
            self.conn.tcp_socket.send(b"AT\r\n")
            
            try:
                response = await self._read_tcp_response(timeout=2.0)
            except socket.timeout:
                response = "Connected (no initial response)"
            
            return {
                "status": "connected",
                "connection_type": "tcp",
                "host": host,
                "port": port,
                "response": response.strip()
            }
        except Exception as e:
            self.conn.tcp_socket = None
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def disconnect(self, connection_type: str = "all") -> Dict[str, Any]:
        """Disconnect from Ameba device"""
        results = {}
        
        if connection_type in ["serial", "all"]:
            if self.conn.serial_port and self.conn.serial_port.is_open:
                try:
                    self.conn.serial_port.close()
                    self.conn.serial_port = None
                    self.conn.serial_port_name = None
                    results["serial"] = "disconnected"
                except Exception as e:
                    results["serial"] = f"error: {str(e)}"
            else:
                results["serial"] = "not_connected"
        
        if connection_type in ["tcp", "all"]:
            if self.conn.tcp_socket:
                try:
                    self.conn.tcp_socket.close()
                    self.conn.tcp_socket = None
                    self.conn.tcp_host = None
                    self.conn.tcp_port = None
                    results["tcp"] = "disconnected"
                except Exception as e:
                    results["tcp"] = f"error: {str(e)}"
            else:
                results["tcp"] = "not_connected"
        
        return {
            "status": "completed",
            "results": results
        }
    
    async def get_connection_status(self) -> Dict[str, Any]:
        """Get current connection status"""
        status = {
            "serial": {
                "connected": False,
                "port": None
            },
            "tcp": {
                "connected": False,
                "host": None,
                "port": None
            }
        }
        
        if self.conn.serial_port and self.conn.serial_port.is_open:
            status["serial"]["connected"] = True
            status["serial"]["port"] = self.conn.serial_port_name
        
        if self.conn.tcp_socket:
            try:
                self.conn.tcp_socket.send(b'')
                status["tcp"]["connected"] = True
                status["tcp"]["host"] = self.conn.tcp_host
                status["tcp"]["port"] = self.conn.tcp_port
            except:
                self.conn.tcp_socket = None
                self.conn.tcp_host = None
                self.conn.tcp_port = None
        
        connections = []
        if status["serial"]["connected"]:
            connections.append(f"Serial ({status['serial']['port']})")
        if status["tcp"]["connected"]:
            connections.append(f"TCP ({status['tcp']['host']}:{status['tcp']['port']})")
        
        status["summary"] = f"Connected: {', '.join(connections)}" if connections else "No connections"
        
        return status
    
    async def send_command(self, command: str, connection: str = None) -> Dict[str, Any]:
        """Send command to device
        
        Args:
            command: Command to send
            connection: 'serial', 'tcp', or None (auto-detect with serial priority)
        """
        if connection is None:
            # Changed: Prefer serial over TCP for auto-detection
            if self.conn.serial_port and self.conn.serial_port.is_open:
                connection = "serial"
            elif self.conn.tcp_socket:
                connection = "tcp"
            else:
                return {
                    "status": "error",
                    "error": "No active connection"
                }
        
        if connection == "serial":
            return await self._send_serial_command(command)
        elif connection == "tcp":
            return await self._send_tcp_command(command)
        else:
            return {
                "status": "error",
                "error": f"Invalid connection type: {connection}"
            }
    
    async def _send_serial_command(self, command: str) -> Dict[str, Any]:
        """Send command via serial"""
        if not self.conn.serial_port or not self.conn.serial_port.is_open:
            return {
                "status": "error",
                "error": "Serial not connected"
            }
        
        try:
            if not command.endswith('\r\n'):
                command += '\r\n'
            
            self.conn.serial_port.reset_input_buffer()
            self.conn.serial_port.write(command.encode())
            
            response = ""
            await asyncio.sleep(0.1)
            
            while self.conn.serial_port.in_waiting:
                chunk = self.conn.serial_port.read(self.conn.serial_port.in_waiting)
                response += chunk.decode('utf-8', errors='ignore')
                await asyncio.sleep(0.05)
            
            return {
                "status": "success",
                "connection": "serial",
                "command": command.strip(),
                "response": response.strip()
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def _send_tcp_command(self, command: str) -> Dict[str, Any]:
        """Send command via TCP"""
        if not self.conn.tcp_socket:
            return {
                "status": "error",
                "error": "TCP not connected"
            }
        
        try:
            if not command.endswith('\r\n'):
                command += '\r\n'
            
            # Clear any pending data first
            self.conn.tcp_socket.settimeout(0.01)
            try:
                while True:
                    self.conn.tcp_socket.recv(4096)
            except:
                pass
            
            self.conn.tcp_socket.send(command.encode())
            response = await self._read_tcp_response(timeout=2.0)
            
            return {
                "status": "success",
                "connection": "tcp",
                "command": command.strip(),
                "response": response
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def _handle_telnet_negotiation(self):
        """Handle Telnet IAC negotiation"""
        self.conn.tcp_socket.setblocking(False)
        await asyncio.sleep(0.1)
        
        try:
            data = self.conn.tcp_socket.recv(1024)
        except:
            pass
        
        self.conn.tcp_socket.setblocking(True)
    
    async def _read_tcp_response(self, timeout: float = 2.0, wait_for_prompt: bool = True, 
                       wait_for_pattern: str = None, collect_until_pattern: str = None) -> str:
        """Read response from TCP socket with improved handling"""
        if not self.conn.tcp_socket:
            return ""
        
        response = ""
        start_time = asyncio.get_event_loop().time()
        
        while (asyncio.get_event_loop().time() - start_time) < timeout:
            try:
                # Use appropriate timeout based on what we're waiting for
                read_timeout = 0.5 if wait_for_pattern else 0.1
                self.conn.tcp_socket.settimeout(read_timeout)
                data = self.conn.tcp_socket.recv(8192)
                
                if data:
                    decoded = data.decode('utf-8', errors='ignore')
                    response += decoded
                    
                    # Check for patterns if specified
                    if wait_for_pattern and wait_for_pattern in response:
                        if collect_until_pattern:
                            # Continue collecting until end pattern
                            if collect_until_pattern in response:
                                # Read a bit more to ensure we get everything
                                await asyncio.sleep(0.2)
                                try:
                                    extra = self.conn.tcp_socket.recv(8192)
                                    if extra:
                                        response += extra.decode('utf-8', errors='ignore')
                                except:
                                    pass
                                break
                        else:
                            # Pattern found, no end pattern specified
                            break
                    
                    # Check for prompt if waiting for it
                    if wait_for_prompt and response.endswith('#'):
                        break
                        
            except socket.timeout:
                # No data available, but continue if we haven't reached timeout
                pass
            except Exception as e:
                break
            
            await asyncio.sleep(0.01)
        
        return response

    # Helper method for WiFi module and others
    async def send_command_with_timeout(self, command: str, timeout: float = 2.0, connection: str = None) -> Dict[str, Any]:
        """Send command with custom timeout (needed by WiFi module)
        
        Args:
            command: Command to send
            timeout: Maximum time to wait for response
            connection: 'serial', 'tcp', or None (auto-detect with serial priority)
        """
        if connection is None:
            # Prefer serial for better streaming response handling
            if self.conn.serial_port and self.conn.serial_port.is_open:
                connection = "serial"
            elif self.conn.tcp_socket:
                connection = "tcp"
            else:
                return {
                    "status": "error",
                    "error": "No active connection"
                }
        
        if connection == "tcp":
            return await self._send_tcp_command_with_timeout(command, timeout)
        else:
            return await self._send_serial_command_with_timeout(command, timeout)
    
    async def _send_serial_command_with_timeout(self, command: str, timeout: float) -> Dict[str, Any]:
        """Send serial command with custom timeout"""
        if not self.conn.serial_port or not self.conn.serial_port.is_open:
            return {
                "status": "error",
                "error": "Not connected to device via serial"
            }
        
        try:
            if not command.endswith('\r\n'):
                command += '\r\n'
            
            self.conn.serial_port.reset_input_buffer()
            self.conn.serial_port.write(command.encode())
            
            response = ""
            await asyncio.sleep(0.5)
            
            start_time = asyncio.get_event_loop().time()
            
            while (asyncio.get_event_loop().time() - start_time) < timeout:
                if self.conn.serial_port.in_waiting:
                    chunk = self.conn.serial_port.read(self.conn.serial_port.in_waiting)
                    response += chunk.decode('utf-8', errors='ignore')
                await asyncio.sleep(0.05)
            
            return {
                "status": "success",
                "command": command.strip(),
                "response": response
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def _send_tcp_command_with_timeout(self, command: str, timeout: float) -> Dict[str, Any]:
        """Send TCP command with custom timeout and improved response handling"""
        if not self.conn.tcp_socket:
            return {
                "status": "error",
                "error": "Not connected to device via TCP"
            }
        
        try:
            if not command.endswith('\r\n'):
                command += '\r\n'
            
            # Clear any pending data first
            self.conn.tcp_socket.settimeout(0.1)
            try:
                while True:
                    self.conn.tcp_socket.recv(4096)
            except socket.timeout:
                pass
            
            # Send command
            self.conn.tcp_socket.send(command.encode())
            
            # Special handling for ATWS (WiFi scan)
            if command.strip().upper() == 'ATWS':
                print(f"Executing WiFi scan with {timeout}s timeout...")
                
                response = ""
                start_time = asyncio.get_event_loop().time()
                scan_started = False
                last_network_line_time = None
                network_count = 0
                
                # Give device time to start the scan
                await asyncio.sleep(0.3)
                
                while (asyncio.get_event_loop().time() - start_time) < timeout:
                    try:
                        # Use longer timeout for WiFi scan to ensure we get data
                        self.conn.tcp_socket.settimeout(1.0)  # Longer timeout for reads
                        data = self.conn.tcp_socket.recv(32768)  # Much larger buffer
                        
                        if data:
                            decoded = data.decode('utf-8', errors='ignore')
                            response += decoded
                            
                            # Check if scan has started
                            if "_AT_WLAN_SCAN_" in decoded:
                                scan_started = True
                                print("WiFi scan started...")
                            
                            # Count network entries (lines with tabs and starting with digits)
                            lines = decoded.split('\n')
                            for line in lines:
                                if '\t' in line and line.strip() and line.strip()[0].isdigit():
                                    network_count += 1
                                    last_network_line_time = asyncio.get_event_loop().time()
                                    print(f"Found network #{network_count}: {line.strip()[:100]}...")
                            
                            # If we've started receiving networks and haven't seen new ones for 1.5 seconds, we're done
                            if last_network_line_time and (asyncio.get_event_loop().time() - last_network_line_time) > 1.5:
                                print(f"No new networks for 1.5s, scan complete with {network_count} networks")
                                break
                                
                    except socket.timeout:
                        # If we've received networks and timeout, check if we should stop
                        if last_network_line_time and (asyncio.get_event_loop().time() - last_network_line_time) > 1.5:
                            print(f"Timeout with no new networks, scan complete with {network_count} networks")
                            break
                        # If scan started but no networks yet, keep waiting
                        elif scan_started:
                            print("Waiting for network data...")
                    
                    await asyncio.sleep(0.1)
                
                print(f"WiFi scan completed. Total response length: {len(response)} bytes")
                
            else:
                # Standard timeout-based reading for other commands
                response = await self._read_tcp_response(timeout=timeout, wait_for_prompt=True)
            
            return {
                "status": "success",
                "connection": "tcp",
                "command": command.strip(),
                "response": response
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }
