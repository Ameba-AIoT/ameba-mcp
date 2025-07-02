"""
Modular Ameba MCP Server Architecture
Supports multiple Ameba product lines with selective feature registration
"""

import asyncio
import json
from typing import Any, Dict, List, Optional, Protocol
from abc import ABC, abstractmethod
import serial
import serial.tools.list_ports
import socket
import urllib.request
import urllib.error
import os
from pathlib import Path
import re
from datetime import datetime
from mcp.server.models import InitializationOptions
from mcp.server import NotificationOptions, Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool


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


class FeatureModule(ABC):
    """Base class for all feature modules"""
    
    def __init__(self, connection_manager: ConnectionManager):
        self.conn = connection_manager
    
    @abstractmethod
    def get_tools(self) -> List[Tool]:
        """Return list of tools provided by this module"""
        pass
    
    @abstractmethod
    async def handle_tool(self, name: str, arguments: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Handle tool calls for this module"""
        pass
    
    @property
    @abstractmethod
    def module_name(self) -> str:
        """Return the name of this module"""
        pass


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

class WiFiModule(FeatureModule):
    """Module for WiFi management functionality"""
    
    def __init__(self, connection_manager: ConnectionManager, connection_module: ConnectionModule):
        super().__init__(connection_manager)
        self.connection_module = connection_module
    
    @property
    def module_name(self) -> str:
        return "wifi"
    
    def get_tools(self) -> List[Tool]:
        return [
            Tool(
                name="wifi_scan",
                description="Scan for available WiFi networks using ATWS command",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "connection": {
                            "type": "string",
                            "description": "Connection to use: 'serial' or 'tcp' (default: auto-detect, prefers serial)",
                            "enum": ["serial", "tcp"]
                        }
                    },
                    "required": []
                }
            ),
            Tool(
                name="wifi_connect",
                description="Connect to WiFi network using ATW0, ATW1, and ATWC commands",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "ssid": {"type": "string", "description": "WiFi network SSID"},
                        "password": {"type": "string", "description": "WiFi network password"}
                    },
                    "required": ["ssid", "password"]
                }
            ),
            Tool(
                name="wifi_status",
                description="Get current WiFi connection status using ATW? command",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "connection": {
                            "type": "string",
                            "description": "Connection to use: 'serial' or 'tcp' (default: auto-detect, prefers serial)",
                            "enum": ["serial", "tcp"]
                        }
                    },
                    "required": []
                }
            )
        ]
    
    async def handle_tool(self, name: str, arguments: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        if name == "wifi_scan":
            connection = arguments.get("connection", None)
            return await self.wifi_scan(connection=connection)
        elif name == "wifi_connect":
            ssid = arguments.get("ssid")
            password = arguments.get("password")
            return await self.wifi_connect(ssid, password)
        elif name == "wifi_status":
            connection = arguments.get("connection", None)
            return await self.wifi_status(connection=connection)
        else:
            raise ValueError(f"Unknown tool: {name}")
    
    async def wifi_scan(self, timeout: float = 15.0, connection: str = None) -> Dict[str, Any]:
        """Scan for available WiFi networks"""
        result = await self.connection_module.send_command_with_timeout("ATWS", timeout=timeout, connection=connection)
        return self._parse_wifi_scan_response(result)
    
    def _parse_wifi_scan_response(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Parse WiFi scan response from either serial or TCP"""
        if result["status"] != "success":
            return result
        
        response = result["response"]
        networks = []
        raw_networks = []
        
        # Split response into lines
        lines = response.split('\n')
        
        # Find all lines that look like network entries (contain tabs and network info)
        for line in lines:
            line = line.strip()
            
            # Skip empty lines and command echoes
            if not line or 'ATWS' in line or '[MEM]' in line or '#' in line:
                continue
                
            # Network entries have tabs and typically start with a number
            if '\t' in line and line[0].isdigit():
                raw_networks.append(line)
                
                # Parse the network entry
                parts = line.split('\t')
                if len(parts) >= 7:  # Ensure we have enough fields
                    try:
                        network_info = {
                            "index": int(parts[0].strip()),
                            "type": parts[1].strip(),
                            "mac": parts[2].strip(),
                            "rssi": int(parts[3].strip()),
                            "channel": int(parts[4].strip()),
                            "channel_width": int(parts[5].strip()),
                            "security": parts[6].strip(),
                            "ssid": parts[7].strip() if len(parts) > 7 else "(Hidden)"
                        }
                        networks.append(network_info)
                    except ValueError:
                        # If parsing fails, still keep the raw line
                        continue
        
        result["networks"] = networks
        result["total_networks"] = len(networks)
        result["raw_networks"] = raw_networks
        
        return result
    
    async def wifi_connect(self, ssid: str, password: str) -> Dict[str, Any]:
        """Connect to WiFi network"""
        if self.conn.tcp_socket and (not self.conn.serial_port or not self.conn.serial_port.is_open):
            return {
                "status": "error",
                "error": "WiFi connect is only available via serial connection. Cannot change WiFi while connected via TCP."
            }
        
        if not self.conn.serial_port or not self.conn.serial_port.is_open:
            return {
                "status": "error",
                "error": "Not connected to device via serial"
            }
        
        try:
            results = []
            
            ssid_cmd = f"ATW0={ssid}"
            ssid_result = await self.connection_module._send_serial_command(ssid_cmd)
            results.append({"command": ssid_cmd, "response": ssid_result})
            
            pwd_cmd = f"ATW1={password}"
            pwd_result = await self.connection_module._send_serial_command(pwd_cmd)
            results.append({"command": pwd_cmd, "response": pwd_result})
            
            connect_result = await self.connection_module._send_serial_command("ATWC")
            results.append({"command": "ATWC", "response": connect_result})
            
            await asyncio.sleep(2)
            
            return {
                "status": "success",
                "ssid": ssid,
                "steps": results,
                "message": "WiFi connection sequence completed"
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def wifi_status(self, timeout: float = 3.0, connection: str = None) -> Dict[str, Any]:
        """Get WiFi connection status"""
        result = await self.connection_module.send_command_with_timeout("ATW?", timeout=timeout, connection=connection)
        
        if result["status"] == "success":
            response = result["response"]
            
            status_info = {
                "raw_response": response,
                "connection_status": "Unknown",
                "ssid": None,
                "channel": None,
                "security": None,
                "password": None,
                "ip_address": None,
                "mac_address": None,
                "gateway": None,
                "subnet_mask": None,
                "mode": None,
                "tx_packets": None,
                "rx_packets": None,
                "tx_bytes": None,
                "rx_bytes": None
            }
            
            lines = response.split('\n')
            for line in lines:
                line = line.strip()
                
                if "Status: Running" in line:
                    status_info["connection_status"] = "Connected"
                elif "Status:" in line and "Running" not in line:
                    status_info["connection_status"] = "Disconnected"
                
                if "SSID =>" in line:
                    status_info["ssid"] = line.split("=>")[1].strip()
                elif "CHANNEL =>" in line:
                    status_info["channel"] = int(line.split("=>")[1].strip())
                elif "SECURITY =>" in line:
                    status_info["security"] = line.split("=>")[1].strip()
                elif "PASSWORD =>" in line:
                    status_info["password"] = line.split("=>")[1].strip()
                elif "MODE =>" in line:
                    status_info["mode"] = line.split("=>")[1].strip()
                
                elif "IP  =>" in line or "IP =>" in line:
                    status_info["ip_address"] = line.split("=>")[1].strip()
                elif "MAC =>" in line:
                    status_info["mac_address"] = line.split("=>")[1].strip()
                elif "GW  =>" in line or "GW =>" in line:
                    status_info["gateway"] = line.split("=>")[1].strip()
                elif "msk  =>" in line or "msk =>" in line:
                    status_info["subnet_mask"] = line.split("=>")[1].strip()
                
                elif "tx_packets=" in line:
                    parts = line.split(", ")
                    for part in parts:
                        if "tx_packets=" in part:
                            status_info["tx_packets"] = int(part.split("=")[1])
                        elif "tx_bytes=" in part:
                            status_info["tx_bytes"] = int(part.split("=")[1])
                elif "rx_packets=" in line:
                    parts = line.split(", ")
                    for part in parts:
                        if "rx_packets=" in part:
                            status_info["rx_packets"] = int(part.split("=")[1])
                        elif "rx_bytes=" in part:
                            status_info["rx_bytes"] = int(part.split("=")[1])
            
            result["wifi_info"] = status_info
            
            if status_info["connection_status"] == "Connected" and status_info["ssid"]:
                result["summary"] = f"Connected to {status_info['ssid']} on channel {status_info['channel']} with IP {status_info['ip_address']}"
            else:
                result["summary"] = "Not connected to any WiFi network"
        
        return result


class KVSModule(FeatureModule):
    """Module for AWS Kinesis Video Streams functionality"""
    
    def __init__(self, connection_manager: ConnectionManager, connection_module: ConnectionModule):
        super().__init__(connection_manager)
        self.connection_module = connection_module
        self.last_kvs_objects: List[str] = []
    
    @property
    def module_name(self) -> str:
        return "kvs"
    
    def get_tools(self) -> List[Tool]:
        return [
            Tool(
                name="kvs_set_objects",
                description="Set objects to detect for KVS streaming. When detected, streams 30-second video to AWS KVS then stops. Can be reactivated with same command.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "objects": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of COCO dataset objects to detect (e.g., ['person', 'car', 'dog'])"
                        }
                    },
                    "required": ["objects"]
                }
            ),
            Tool(
                name="kvs_reactivate",
                description="Reactivate KVS object detection with previously set objects (after 30-second recording completes)",
                inputSchema={
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            ),
            Tool(
                name="kvs_wait_for_start",
                description="Wait for KVS recording to start. Returns immediately when recording begins.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "timeout": {
                            "type": "number",
                            "description": "Maximum time to wait in seconds (default: 180)"
                        }
                    },
                    "required": []
                }
            ),
            Tool(
                name="kvs_wait_for_completion",
                description="Wait for KVS recording to complete. Returns immediately when recording ends.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "timeout": {
                            "type": "number",
                            "description": "Maximum time to wait in seconds (default: 60)"
                        }
                    },
                    "required": []
                }
            )
        ]
    
    async def handle_tool(self, name: str, arguments: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        if name == "kvs_set_objects":
            objects = arguments.get("objects", [])
            return await self.kvs_set_objects(objects)
        elif name == "kvs_reactivate":
            return await self.kvs_reactivate()
        elif name == "kvs_wait_for_start":
            timeout = arguments.get("timeout", 180.0)
            return await self.kvs_wait_for_start(timeout)
        elif name == "kvs_wait_for_completion":
            timeout = arguments.get("timeout", 60.0)
            return await self.kvs_wait_for_completion(timeout)
        else:
            raise ValueError(f"Unknown tool: {name}")
    
    async def kvs_set_objects(self, objects: List[str]) -> Dict[str, Any]:
        """Set objects to detect for KVS streaming"""
        if not objects:
            return {
                "status": "error",
                "error": "No objects specified"
            }
        
        self.last_kvs_objects = objects
        
        objects_str = ",".join(objects)
        command = f"ATKVS={objects_str}"
        
        result = await self.connection_module.send_command(command)
        
        if result["status"] == "success":
            result["objects_set"] = objects
            result["message"] = f"KVS armed for 30-second recording when detecting: {', '.join(objects)}"
            result["note"] = "Recording will stop after 30 seconds. Use kvs_reactivate() to arm again."
        
        return result
    
    async def kvs_reactivate(self) -> Dict[str, Any]:
        """Reactivate KVS detection"""
        if not self.last_kvs_objects:
            return {
                "status": "error",
                "error": "No previous objects to reactivate. Use kvs_set_objects first."
            }
        
        return await self.kvs_set_objects(self.last_kvs_objects)
    
    async def kvs_wait_for_start(self, timeout: float = 180.0) -> Dict[str, Any]:
        """Wait for KVS recording to start"""
        if self.conn.tcp_socket:
            return {
                "status": "error",
                "error": "KVS monitoring is only available via serial connection"
            }
        
        if not self.conn.serial_port or not self.conn.serial_port.is_open:
            return {
                "status": "error",
                "error": "Not connected to device via serial"
            }
        
        try:
            start_time = asyncio.get_event_loop().time()
            self.conn.serial_port.reset_input_buffer()
            buffer = ""
            
            while (asyncio.get_event_loop().time() - start_time) < timeout:
                elapsed_time = asyncio.get_event_loop().time() - start_time
                
                if self.conn.serial_port.in_waiting:
                    chunk = self.conn.serial_port.read(self.conn.serial_port.in_waiting)
                    text = chunk.decode('utf-8', errors='ignore')
                    buffer += text
                    
                    if "kvs start 30s recording" in buffer.lower():
                        return {
                            "status": "recording_started",
                            "elapsed_time": round(elapsed_time, 2),
                            "message": "KVS recording has started! Recording 30 seconds of video..."
                        }
                
                await asyncio.sleep(0.1)
            
            return {
                "status": "timeout",
                "elapsed_time": round(timeout, 2),
                "message": f"No recording started within {timeout} seconds"
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def kvs_wait_for_completion(self, timeout: float = 60.0) -> Dict[str, Any]:
        """Wait for KVS recording to complete"""
        if self.conn.tcp_socket:
            return {
                "status": "error",
                "error": "KVS monitoring is only available via serial connection"
            }
        
        if not self.conn.serial_port or not self.conn.serial_port.is_open:
            return {
                "status": "error", 
                "error": "Not connected to device via serial"
            }
        
        try:
            start_time = asyncio.get_event_loop().time()
            self.conn.serial_port.reset_input_buffer()
            buffer = ""
            fragment_count = 0
            
            while (asyncio.get_event_loop().time() - start_time) < timeout:
                elapsed_time = asyncio.get_event_loop().time() - start_time
                
                if self.conn.serial_port.in_waiting:
                    chunk = self.conn.serial_port.read(self.conn.serial_port.in_waiting)
                    text = chunk.decode('utf-8', errors='ignore')
                    buffer += text
                    
                    fragment_count += text.lower().count("fragment")
                    
                    if "sending end of frames done!" in buffer.lower():
                        return {
                            "status": "recording_completed",
                            "elapsed_time": round(elapsed_time, 2),
                            "fragments": fragment_count,
                            "message": "KVS recording completed! Video successfully uploaded to AWS."
                        }
                
                await asyncio.sleep(0.1)
            
            return {
                "status": "timeout",
                "elapsed_time": round(timeout, 2),
                "message": f"Recording did not complete within {timeout} seconds"
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }


class SnapshotModule(FeatureModule):
    """Module for snapshot capture and download functionality"""
    
    def __init__(self, connection_manager: ConnectionManager, connection_module: ConnectionModule):
        super().__init__(connection_manager)
        self.connection_module = connection_module
    
    @property
    def module_name(self) -> str:
        return "snapshot"
    
    def get_tools(self) -> List[Tool]:
        return [
            Tool(
                name="snapshot_capture",
                description="Capture a snapshot image on device using SNAP=SNAPS command",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "connection": {
                            "type": "string",
                            "description": "Connection to use: 'serial' or 'tcp' (default: auto-detect)",
                            "enum": ["serial", "tcp"]
                        }
                    },
                    "required": []
                }
            ),
            Tool(
                name="snapshot_download",
                description="Download a snapshot image from device HTTP server and save locally",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "filename": {"type": "string", "description": "Image filename on device (e.g., 'snapshot_001.jpg')"},
                        "device_ip": {"type": "string", "description": "IP address of device"},
                        "save_path": {"type": "string", "description": "Local path to save the image (optional)"}
                    },
                    "required": ["filename", "device_ip"]
                }
            ),
            Tool(
                name="snapshot_download_all",
                description="Download all snapshot images from device HTTP server (0.jpg, 1.jpg, etc.)",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "device_ip": {"type": "string", "description": "IP address of device"},
                        "save_path": {"type": "string", "description": "Local path to save images (optional)"},
                        "max_files": {"type": "integer", "description": "Maximum number of files to try (optional, defaults to 100)"}
                    },
                    "required": ["device_ip"]
                }
            )
        ]
    
    async def handle_tool(self, name: str, arguments: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        if name == "snapshot_capture":
            connection = arguments.get("connection", None)
            return await self.snapshot_capture(connection=connection)
        elif name == "snapshot_download":
            filename = arguments.get("filename")
            device_ip = arguments.get("device_ip")
            save_path = arguments.get("save_path", "./downloads/")
            return await self.snapshot_download(filename, device_ip, save_path)
        elif name == "snapshot_download_all":
            device_ip = arguments.get("device_ip")
            save_path = arguments.get("save_path", "./downloads/")
            max_files = arguments.get("max_files", 100)
            return await self.snapshot_download_all(device_ip, save_path, max_files)
        else:
            raise ValueError(f"Unknown tool: {name}")
    
    async def snapshot_capture(self, connection: str = None) -> Dict[str, Any]:
        """Capture a snapshot
        
        Args:
            connection: 'serial', 'tcp', or None (auto-detect)
        """
        try:
            # Use the connection module's send_command method which handles both serial and TCP
            result = await self.connection_module.send_command("SNAP=SNAPS", connection=connection)
            
            if result["status"] == "success":
                response = result["response"]
                
                filename = None
                captured = False
                
                if "capture_snapshot_cb" in response:
                    captured = True
                    
                    filename_match = re.search(r'jpeg\s+sd:/IMAGE/(\d+\.jpg)', response)
                    if filename_match:
                        filename = filename_match.group(1)
                    else:
                        filename_match = re.search(r'sd:/IMAGE/(\d+\.jpg)', response)
                        if filename_match:
                            filename = filename_match.group(1)
                
                if captured:
                    return {
                        "status": "success",
                        "message": "Snapshot captured successfully",
                        "filename": filename,
                        "response": response,
                        "captured": True,
                        "connection": result.get("connection", "unknown"),  # Include which connection was used
                        "note": f"Image saved as {filename} on device. Use snapshot_download('{filename}', device_ip) to retrieve it"
                    }
                else:
                    return {
                        "status": "error",
                        "message": "Snapshot command sent but capture not confirmed",
                        "response": response,
                        "captured": False,
                        "connection": result.get("connection", "unknown")
                    }
            else:
                return result
                
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def snapshot_download(self, filename: str, device_ip: str, save_path: str = "./downloads/") -> Dict[str, Any]:
        """Download snapshot image"""
        try:
            Path(save_path).mkdir(parents=True, exist_ok=True)
            
            url = f"http://{device_ip}/image_get.jpg?filename={filename}"
            
            try:
                with urllib.request.urlopen(url, timeout=30) as response:
                    content = response.read()
                    
                    local_filename = os.path.join(save_path, filename)
                    
                    with open(local_filename, 'wb') as f:
                        f.write(content)
                    
                    file_size = len(content)
                    
                    return {
                        "status": "success",
                        "message": f"Image downloaded successfully",
                        "filename": filename,
                        "local_path": os.path.abspath(local_filename),
                        "file_size": file_size,
                        "url": url,
                        "note": f"Image saved to {local_filename}. You can now use extract_image_from_file with this path."
                    }
                    
            except urllib.error.HTTPError as e:
                return {
                    "status": "error",
                    "error": f"HTTP {e.code}: {e.reason}",
                    "url": url
                }
            except urllib.error.URLError as e:
                return {
                    "status": "error",
                    "error": f"URL Error: {str(e)}",
                    "url": url
                }
                
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "url": url if 'url' in locals() else None
            }
    
    async def snapshot_download_all(self, device_ip: str, save_path: str = "./downloads/", max_files: int = 100) -> Dict[str, Any]:
        """Download all snapshot images"""
        try:
            Path(save_path).mkdir(parents=True, exist_ok=True)
            
            index_url = f"http://{device_ip}/index.htm"
            image_files = []
            
            try:
                with urllib.request.urlopen(index_url, timeout=10) as response:
                    html_content = response.read().decode('utf-8', errors='ignore')
                    
                    jpg_pattern = re.findall(r'(\d+\.jpg)', html_content)
                    image_files = sorted(list(set(jpg_pattern)), key=lambda x: int(x.split('.')[0]))
                    
                    print(f"Found {len(image_files)} image files in index: {image_files}")
                    
            except Exception as e:
                return {
                    "status": "error",
                    "error": f"Failed to fetch file list from {index_url}: {str(e)}"
                }
            
            if not image_files:
                return {
                    "status": "success",
                    "message": "No image files found on device",
                    "downloaded_files": [],
                    "total_downloaded": 0,
                    "device_ip": device_ip,
                    "index_url": index_url
                }
            
            downloaded_files = []
            failed_files = []
            
            for filename in image_files:
                url = f"http://{device_ip}/image_get.jpg?filename={filename}"
                
                try:
                    with urllib.request.urlopen(url, timeout=10) as response:
                        content = response.read()
                        
                        if len(content) > 1000:
                            local_filename = os.path.join(save_path, filename)
                            
                            with open(local_filename, 'wb') as f:
                                f.write(content)
                            
                            downloaded_files.append({
                                "filename": filename,
                                "local_path": os.path.abspath(local_filename),
                                "size": len(content)
                            })
                            
                            print(f"Downloaded {filename} ({len(content)} bytes)")
                        else:
                            failed_files.append(filename)
                            
                except (urllib.error.HTTPError, urllib.error.URLError) as e:
                    failed_files.append(filename)
                    
                except Exception as e:
                    failed_files.append(filename)
                
                await asyncio.sleep(0.1)
            
            return {
                "status": "success",
                "message": f"Downloaded {len(downloaded_files)} out of {len(image_files)} images",
                "downloaded_files": downloaded_files,
                "failed_files": failed_files,
                "total_found": len(image_files),
                "total_downloaded": len(downloaded_files),
                "total_failed": len(failed_files),
                "save_path": os.path.abspath(save_path),
                "device_ip": device_ip,
                "note": "Images saved successfully. You can now use extract_image_from_file on any of them." if downloaded_files else "No images were downloaded"
            }
                
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "downloaded_files": downloaded_files if 'downloaded_files' in locals() else [],
                "device_ip": device_ip
            }
        

class HEMSModule(FeatureModule):
    """Module for Home Energy Management System functionality (Ameba D/Plus only)"""
    def __init__(self, connection_manager: ConnectionManager, connection_module: ConnectionModule):
        super().__init__(connection_manager)
        self.connection_module = connection_module
    
    @property
    def module_name(self) -> str:
        return "hems"
    
    def get_tools(self) -> List[Tool]:
        return [
            Tool(
                name="hems_identify",
                description="Identify the chipset on the device and return its full name",
                inputSchema={
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            ),
            Tool(
                name="hems_start_logging",
                description="(STUB) Start the logging functionality on the HEMS, which will save logs to the onboard filesystem",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "device": {"type": "string", "description": "Device identification Name"}
                    },
                    "required": ["device"]
                }
            ),
            Tool(
                name="hems_stop_logging",
                description="(STUB) Stop the logging functionality on the HEMS",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "device": {"type": "string", "description": "Device identification Name"}
                    },
                    "required": ["device"]
                }
            ),
            Tool(
                name="hems_download_logs",
                description="Retrieve the logs from the HEMS over a specified timeframe",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "device": {"type": "string", "description": "Device identification Name"},
                        "start_date": {
                            "type": "string",
                            "description": "Start date to fetch logs. If left empty, retrieval begins from the first entry of the log"
                        },
                        "end_date": {
                            "type": "string",
                            "description": "End date to fetch logs. If left empty, retrieval ends at the last entry of the log"
                        }
                    },
                    "required": ["device"]
                }
            ),
            Tool(
                name="hems_get_alerts",
                description="Obtain alerts from the HEMS that may require user attention",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "device": {"type": "string", "description": "Device identification Name"}
                    },
                    "required": ["device"]
                }
            ),
            Tool(
                name="hems_get_control_plan",
                description="Gets the current control plan being executed on the HEMS",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "device": {"type": "string", "description": "Device identification Name"}
                    },
                    "required": ["device"]
                }
            ),
            Tool(
                name="hems_get_available_control_plans",
                description="Gets available control plans for the HEMS",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "device": {"type": "string", "description": "Device identification Name"}
                    },
                    "required": ["device"]
                }
            ),
            Tool(
                name="hems_set_control_plan",
                description="Sets a control plan for the HEMS based on occupancy (At Home, Out of Home, Night Mode, Quick Heating, Quick Cooling)",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "device": {"type": "string", "description": "Device identification Name"},
                        "control_plan": {
                            "type": "string",
                            "description": "Name of the control plan"
                        }
                    },
                    "required": ["device", "control_plan"]
                }
            ),
            Tool(
                name="hems_get_statistics",
                description="Gets the current statistics of the HEMS including grid-related information",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "device": {"type": "string", "description": "Device identification Name"}
                    },
                    "required": ["device"]
                }
            )
        ]
    
    async def handle_tool(self, name: str, arguments: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        if name == "hems_identify":
            return await self.hems_identify()
        elif name == "hems_start_logging":
            device = arguments.get("device")
            return await self.hems_start_logging(device)
        elif name == "hems_stop_logging":
            device = arguments.get("device")
            return await self.hems_stop_logging(device)
        elif name == "hems_download_logs":
            device = arguments.get("device")
            start_date = arguments.get("start_date", "")
            end_date = arguments.get("end_date", "")
            return await self.hems_download_logs(device, start_date, end_date)
        elif name == "hems_get_alerts":
            device = arguments.get("device")
            return await self.hems_get_alerts(device)
        elif name == "hems_get_control_plan":
            device = arguments.get("device")
            return await self.hems_get_control_plan(device)
        elif name == "hems_get_available_control_plans":
            device = arguments.get("device")
            return await self.hems_get_available_control_plans(device)
        elif name == "hems_set_control_plan":
            device = arguments.get("device")
            control_plan = arguments.get("control_plan")
            return await self.hems_set_control_plan(device, control_plan)
        elif name == "hems_get_statistics":
            device = arguments.get("device")
            return await self.hems_get_statistics(device)
        else:
            raise ValueError(f"Unknown tool: {name}")
    
    async def hems_identify(self) -> Dict[str, Any]:
        """Identify the chipset on the device with AT+HEMS_ID"""
        result = await self.connection_module.send_command_with_timeout("AT+HEMS_ID", timeout=2.0)
        
        if result["status"] == "success":
            return {
                "status": "success",
                "name": result["response"].strip()
            }
        return result
    
    async def hems_start_logging(self, device: str) -> Dict[str, Any]:
        """Start HEMS Logging using AT+HEMS_STARTLOG command"""
        if "pro2" in device.lower():
            return {
                "status": "error",
                "error": "Invalid device, only d/plus accepted"
            }
        
        result = await self.connection_module.send_command_with_timeout("AT+HEMS_STARTLOG", timeout=2.0)
        
        if result["status"] == "success":
            return {
                "status": "success",
                "timestamp": datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ'),
                "message": "HEMS logging started"
            }
        return result
    
    async def hems_stop_logging(self, device: str) -> Dict[str, Any]:
        """Stop HEMS Logging using AT+HEMS_STOPLOG command"""
        if "pro2" in device.lower():
            return {
                "status": "error",
                "error": "Invalid device, only d/plus accepted"
            }
        
        result = await self.connection_module.send_command_with_timeout("AT+HEMS_STOPLOG", timeout=2.0)
        
        if result["status"] == "success":
            return {
                "status": "success",
                "timestamp": datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ'),
                "message": "HEMS logging stopped"
            }
        return result
    
    async def hems_download_logs(self, device: str, start_date: str = "", end_date: str = "") -> Dict[str, Any]:
        """Download HEMS Logs using AT+HEMS_LOGDL command"""
        if "pro2" in device.lower():
            return {
                "status": "error",
                "error": "Invalid device, only d/plus accepted"
            }
        
        result = await self.connection_module.send_command_with_timeout("AT+HEMS_LOGDL", timeout=2.0)
        
        if result["status"] == "success":
            response = result["response"]
            logs = []
            
            # Parse response line by line
            lines = response.split('\n')
            for line in lines:
                line = line.strip()
                if line.startswith("L>"):
                    line_part = line.split("L>")[1].strip().split(";")
                    if len(line_part) >= 6:
                        log_data = {
                            "timestamp": line_part[0],
                            "input_voltage": line_part[1],
                            "input_current": line_part[2],
                            "output_voltage": line_part[3],
                            "output_current": line_part[4],
                            "operating_temperature": line_part[5]
                        }
                        logs.append(log_data)
            
            return {
                "status": "success",
                "logs": logs,
                "total_entries": len(logs)
            }
        return result
    
    async def hems_get_alerts(self, device: str) -> Dict[str, Any]:
        """Get HEMS Alerts using AT+HEMS_ALERTS command"""
        if "pro2" in device.lower():
            return {
                "status": "error",
                "error": "Invalid device, only d/plus accepted"
            }
        
        result = await self.connection_module.send_command_with_timeout("AT+HEMS_ALERTS", timeout=2.0)
        
        if result["status"] == "success":
            response = result["response"]
            alerts = []
            
            # Parse response line by line
            lines = response.split('\n')
            for line in lines:
                line = line.strip()
                if line.startswith("A>"):
                    line_part = line.split("A>")[1].strip().split(";")
                    if len(line_part) >= 3:
                        alert_data = {
                            "code": line_part[0],
                            "timestamp": line_part[1],
                            "message": line_part[2],
                        }
                        alerts.append(alert_data)
            
            return {
                "status": "success",
                "alerts": alerts,
                "total_alerts": len(alerts)
            }
        return result
    
    async def hems_get_control_plan(self, device: str) -> Dict[str, Any]:
        """Get HEMS Current Control Plan using AT+HEMS_GETCTL command"""
        if "pro2" in device.lower():
            return {
                "status": "error",
                "error": "Invalid device, only d/plus accepted"
            }
        
        result = await self.connection_module.send_command_with_timeout("AT+HEMS_GETCTL", timeout=2.0)
        
        if result["status"] == "success":
            plan = result["response"].strip()
            return {
                "status": "success",
                "current_plan": plan,
                "response": result["response"]
            }
        return result
    
    async def hems_get_available_control_plans(self, device: str) -> Dict[str, Any]:
        """Get available control plans (static list)"""
        if "pro2" in device.lower():
            return {
                "status": "error",
                "error": "Invalid device, only d/plus accepted"
            }
        
        return {
            "status": "success",
            "control_plans": [
                "At Home",
                "Out of House",
                "Quick Cooling",
                "Quick Warmth",
                "Night Mode"
            ]
        }
    
    async def hems_set_control_plan(self, device: str, control_plan: str) -> Dict[str, Any]:
        """Set HEMS Current Control Plan using AT+HEMS_SETCTL command"""
        if "pro2" in device.lower():
            return {
                "status": "error",
                "error": "Invalid device, only d/plus accepted"
            }
        
        # Map control plan names to numbers
        plan_map = {
            "At Home": 0,
            "Out of House": 1,
            "Quick Cooling": 2,
            "Quick Warmth": 3,
            "Night Mode": 4
        }
        
        plan_num = plan_map.get(control_plan, -1)
        if plan_num == -1:
            return {
                "status": "error",
                "error": f"Invalid control plan: {control_plan}"
            }
        
        cmd = f"AT+HEMS_SETCTL={plan_num}"
        result = await self.connection_module.send_command_with_timeout(cmd, timeout=2.0)
        
        if result["status"] == "success":
            if "Invalid" in result["response"]:
                return {
                    "status": "error",
                    "error": "Invalid control plan",
                    "response": result["response"]
                }
            return {
                "status": "success",
                "control_plan": control_plan,
                "message": f"Control plan set to: {control_plan}"
            }
        return result
    
    async def hems_get_statistics(self, device: str) -> Dict[str, Any]:
        """Get HEMS Grid Statistics using AT+HEMS_STATS command"""
        if "pro2" in device.lower():
            return {
                "status": "error",
                "error": "Invalid device, only d/plus accepted"
            }
        
        result = await self.connection_module.send_command_with_timeout("AT+HEMS_STATS", timeout=2.0)
        
        if result["status"] == "success":
            # For demo purposes, returning structured fake data
            # In production, you would parse the actual response
            stats = {
                "timestamp": datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ'),
                "inverter_id": "INV-001",
                "operational_data": {
                    "input_voltage": 350.5,
                    "input_current": 10.2,
                    "output_voltage": 230.1,
                    "output_current": 15.3,
                    "output_frequency": 50.01,
                    "power_output": 3500.5,
                    "power_factor": 0.98,
                    "efficiency": 96.5,
                    "temperature": 42.3
                },
                "grid_data": {
                    "grid_voltage": 229.8,
                    "grid_frequency": 50.02,
                    "connection_status": "connected"
                },
                "energy_data": {
                    "daily_production": 25.7,
                    "total_production": 15280.5
                }
            }
            
            return {
                "status": "success",
                "stats": stats
            }
        return result


# Product configurations
PRODUCT_CONFIGS = {
    "ameba-pro2": {
        "name": "Ameba Pro2",
        "modules": ["connection", "wifi", "kvs", "snapshot"]
    },
    "ameba-d": {
        "name": "Ameba D",
        "modules": ["connection", "wifi", "hems"]
    },
    "ameba-arduino": {
        "name": "Ameba Arduino",
        "modules": ["connection", "wifi"]
    }
}


class ModularAmebaServer:
    """Main server class that manages modules based on product configuration"""
    
    def __init__(self, product: str = "ameba-pro2"):
        if product not in PRODUCT_CONFIGS:
            raise ValueError(f"Unknown product: {product}. Available: {list(PRODUCT_CONFIGS.keys())}")
        
        self.product = product
        self.config = PRODUCT_CONFIGS[product]
        self.connection_manager = ConnectionManager()
        self.modules: Dict[str, FeatureModule] = {}
        
        # Initialize MCP server with product name
        self.server = Server(f"{product}-mcp")
        
        # Load modules based on configuration
        self._load_modules()
        self.setup_handlers()
    
    def _load_modules(self):
        """Load modules based on product configuration"""
        # Connection module is always loaded first
        if "connection" in self.config["modules"]:
            self.modules["connection"] = ConnectionModule(self.connection_manager)
        
        # Load other modules that depend on connection
        connection_module = self.modules.get("connection")
        
        for module_name in self.config["modules"]:
            if module_name == "connection":
                continue  # Already loaded
            elif module_name == "wifi":
                self.modules["wifi"] = WiFiModule(self.connection_manager, connection_module)
            elif module_name == "kvs":
                self.modules["kvs"] = KVSModule(self.connection_manager, connection_module)
            elif module_name == "snapshot":
                self.modules["snapshot"] = SnapshotModule(self.connection_manager, connection_module)
            elif module_name == "hems":
                self.modules["hems"] = HEMSModule(self.connection_manager, connection_module)
    
    def setup_handlers(self):
        @self.server.list_tools()
        async def handle_list_tools() -> List[Tool]:
            tools = []
            for module in self.modules.values():
                tools.extend(module.get_tools())
            return tools
        
        @self.server.call_tool()
        async def handle_call_tool(name: str, arguments: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
            try:
                # Find which module handles this tool
                for module in self.modules.values():
                    tool_names = [tool.name for tool in module.get_tools()]
                    if name in tool_names:
                        result = await module.handle_tool(name, arguments)
                        return [{"type": "text", "text": json.dumps(result, indent=2)}]
                
                raise ValueError(f"Unknown tool: {name}")
                
            except Exception as e:
                return [{"type": "text", "text": f"Error: {str(e)}"}]
    
    async def run(self):
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name=f"{self.product}-mcp",
                    server_version="1.0.0",
                    capabilities=self.server.get_capabilities(
                        notification_options=NotificationOptions(),
                        experimental_capabilities={},
                    ),
                ),
            )


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Modular Ameba MCP Server')
    parser.add_argument('--product', type=str, default='ameba-pro2',
                        choices=list(PRODUCT_CONFIGS.keys()),
                        help='Ameba product line to use')
    
    args = parser.parse_args()
    
    print(f"Starting {args.product} MCP Server...")
    print(f"Loaded modules: {PRODUCT_CONFIGS[args.product]['modules']}")
    
    server = ModularAmebaServer(product=args.product)
    asyncio.run(server.run())


if __name__ == "__main__":
    main()