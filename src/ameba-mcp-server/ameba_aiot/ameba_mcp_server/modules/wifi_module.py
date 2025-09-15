from .connection_manager import ConnectionManager
from .connection_module import ConnectionModule
from .feature_module import FeatureModule
from typing import Any, Dict, List, Optional, Protocol
from mcp.types import Tool
import asyncio
import json

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
