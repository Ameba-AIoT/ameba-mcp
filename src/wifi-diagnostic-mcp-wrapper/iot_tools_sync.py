from typing import Any, Dict, List, Optional
from datetime import datetime, timezone
import logging

logger = logging.getLogger("iot-tools-sync")

WIFI_JOIN_STATUS = {
    0: "UNKNOWN",
    1: "STARTING",
    2: "SCANNING",
    3: "SCANN_DONE",
    4: "AUTHENTICATING",
    5: "AUTHENTICATED",
    6: "ASSOCIATING",
    7: "ASSOCIATED",
    8: "4WAY_HANDSHAKING",
    9: "4WAY_HANDSHAKE_DONE",
    10: "SUCCESS",
    11: "FAIL",
    12: "DISCONNECT",
    13: "REJECT_CONNECTION_SECURITY",
    14: "SCANNING_EXTERNAL",
    15: "REJECT_UNSUPPORT_SECURITY",
    16: "TIMEOUT",
    17: "STATUS_CODE_FAIL"
}

WIFI_STATUS_DESCRIPTIONS = {
    0: "Unknown state",
    1: "WiFi connection starting",
    2: "Scanning for access points",
    3: "Scan completed",
    4: "Authenticating with AP",
    5: "Authentication successful",
    6: "Associating with AP",
    7: "Association successful",
    8: "Performing 4-way handshake",
    9: "4-way handshake completed",
    10: "Successfully connected to WiFi",
    11: "Connection failed",
    12: "Disconnected from WiFi",
    13: "Rejected due to security settings",
    14: "External scanning in progress",
    15: "Unsupported security type",
    16: "Connection timeout",
    17: "Failed with status code error"
}

class IoTWiFiTools:
    """Module for IoT WiFi diagnostic functionality - Sync version"""
    
    def __init__(self, mqtt_handler):
        self.mqtt_handler = mqtt_handler
    
    def get_tools_definitions(self) -> List[Dict[str, Any]]:
        """Get tool definitions for MCP protocol"""
        return [
            {
                "name": "get_device_status",
                "description": "Get current WiFi status from IoT device using ATW? command",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "device_id": {
                            "type": "string",
                            "description": "IoT device identifier"
                        },
                        "timeout": {
                            "type": "integer",
                            "description": "Response timeout in seconds",
                            "default": 30
                        }
                    },
                    "required": ["device_id"]
                }
            },
            {
                "name": "get_device_rssi",
                "description": "Get device RSSI using ATWR command",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "device_id": {
                            "type": "string",
                            "description": "IoT device identifier"
                        },
                        "timeout": {
                            "type": "integer",
                            "description": "Response timeout in seconds",
                            "default": 30
                        }
                    },
                    "required": ["device_id"]
                }
            },
            {
                "name": "get_wifi_log",
                "description": "Get WiFi connection log from IoT device using WIFILOG command",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "device_id": {
                            "type": "string",
                            "description": "IoT device identifier"
                        },
                        "timeout": {
                            "type": "integer",
                            "description": "Response timeout in seconds",
                            "default": 30
                        }
                    },
                    "required": ["device_id"]
                }
            },
            {
                "name": "get_wifi_connection_status",
                "description": """Get WiFi connection status transition history from IoT device.
                Returns a complete log of WiFi state changes with timestamps, showing the connection process.
                Each entry shows status transitions (e.g., SCANNING -> AUTHENTICATING -> SUCCESS).
                Useful for diagnosing connection issues, understanding why connections fail, and analyzing connection patterns.
                Includes detailed status codes with human-readable descriptions.""",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "device_id": {
                            "type": "string",
                            "description": "IoT device identifier"
                        },
                        "timeout": {
                            "type": "integer",
                            "description": "Response timeout in seconds",
                            "default": 30
                        }
                    },
                    "required": ["device_id"]
                }
            },
            {
                "name": "clear_wifi_connection_status",
                "description": """Clear the WiFi connection status log on the IoT device.
                WARNING: This is a destructive operation that will permanently delete all WiFi status history.
                Use this to reset the log or free up memory on the device.
                The log will start recording again from scratch after clearing.""",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "device_id": {
                            "type": "string",
                            "description": "IoT device identifier"
                        },
                        "timeout": {
                            "type": "integer",
                            "description": "Response timeout in seconds",
                            "default": 30
                        }
                    },
                    "required": ["device_id"]
                }
            },
            {
                "name": "configure_mqtt",
                "description": "Configure and connect to MQTT broker",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "broker": {
                            "type": "string",
                            "description": "MQTT broker hostname or IP address"
                        },
                        "port": {
                            "type": "integer",
                            "description": "MQTT broker port",
                            "default": 1883
                        },
                        "username": {
                            "type": "string",
                            "description": "MQTT username (optional)"
                        },
                        "password": {
                            "type": "string",
                            "description": "MQTT password (optional)"
                        }
                    },
                    "required": ["broker"]
                }
            },
            {
                "name": "mqtt_status",
                "description": "Check MQTT connection status and configuration",
                "inputSchema": {
                    "type": "object",
                    "properties": {}
                }
            }
        ]
    
    def get_device_status(self, device_id: str, timeout: int = 30) -> Dict[str, Any]:
        """Get current WiFi status from IoT device using ATW? command"""
        try:
            if not device_id:
                return {"error": "Missing device_id parameter"}
            
            if not self.mqtt_handler.is_connected():
                return {"error": "MQTT not connected. Use configure_mqtt first."}
            
            response = self.mqtt_handler.send_command("ATW?", device_id, timeout)
            raw_response = response.get("data", {}).get("response", "")
            
            return {
                "status": "success",
                "message": f"ATW? Response from {device_id}",
                "device_id": device_id,
                "raw_response": raw_response,
                "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
            }
        except Exception as e:
            return {"error": str(e)}
    
    def get_device_rssi(self, device_id: str, timeout: int = 30) -> Dict[str, Any]:
        """Get device RSSI using ATWR command"""
        try:
            if not device_id:
                return {"error": "Missing device_id parameter"}
            
            if not self.mqtt_handler.is_connected():
                return {"error": "MQTT not connected. Use configure_mqtt first."}
            
            response = self.mqtt_handler.send_command("ATWR", device_id, timeout)
            raw_response = response.get("data", {}).get("response", "")
            
            return {
                "status": "success",
                "message": f"ATWR Response from {device_id}",
                "device_id": device_id,
                "raw_response": raw_response,
                "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
            }
        except Exception as e:
            return {"error": str(e)}
    
    def get_wifi_log(self, device_id: str, timeout: int = 30) -> Dict[str, Any]:
        """Get WiFi connection log from IoT device using WIFILOG command"""
        try:
            if not device_id:
                return {"error": "Missing device_id parameter"}
            
            if not self.mqtt_handler.is_connected():
                return {"error": "MQTT not connected. Use configure_mqtt first."}
            
            response = self.mqtt_handler.send_command("WIFILOG", device_id, timeout)
            #logger.info(f"Received response: {response}")
            raw_response = response.get("data", {}).get("response", "")
            
            return {
                "status": "success",
                "message": f"WIFILOG Response from {device_id}",
                "device_id": device_id,
                "raw_response": raw_response,
                "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
            }
        except Exception as e:
            return {"error": str(e)}
        
    def get_wifi_connection_status(self, device_id: str, timeout: int = 30) -> Dict[str, Any]:
        """Get WiFi connection status history from IoT device"""
        try:
            if not device_id:
                return {"error": "Missing device_id parameter"}
            
            if not self.mqtt_handler.is_connected():
                return {"error": "MQTT not connected. Use configure_mqtt first."}
            
            response = self.mqtt_handler.send_command("CONNECTINFO", device_id, timeout)
            raw_response = response.get("data", {}).get("response", "")
            
            parsed_log = self._parse_status_log(raw_response)
            
            return {
                "status": "success",
                "message": f"WiFi Connection Status from {device_id}",
                "device_id": device_id,
                "raw_response": raw_response,
                "parsed_log": parsed_log,
                "status_enum": WIFI_JOIN_STATUS,
                "status_descriptions": WIFI_STATUS_DESCRIPTIONS,
                "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
            }
        except Exception as e:
            return {"error": str(e)}
    
    def clear_wifi_connection_status(self, device_id: str, timeout: int = 30) -> Dict[str, Any]:
        """Clear WiFi connection status log on the device"""
        try:
            if not device_id:
                return {"error": "Missing device_id parameter"}
            
            if not self.mqtt_handler.is_connected():
                return {"error": "MQTT not connected. Use configure_mqtt first."}
            
            response = self.mqtt_handler.send_command("CONNECTINFO=CLEAR", device_id, timeout)
            raw_response = response.get("data", {}).get("response", "")
            
            return {
                "status": "success",
                "message": f"WiFi connection status log cleared on {device_id}",
                "device_id": device_id,
                "raw_response": raw_response,
                "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
            }
        except Exception as e:
            return {"error": str(e)}
    
    def _parse_status_log(self, raw_response: str) -> List[Dict[str, Any]]:
        """Parse the raw status log response"""
        parsed = []
        
        lines = raw_response.split('\n')
        for line in lines:
            if 'Time:' in line:
                try:
                    time_str = line.split(',')[0].split(':')[1].strip()
                    timestamp = int(time_str)
                    
                    # Check if it is error type
                    if 'Error:' in line:
                        error_str = line.split('Error:')[1].strip()
                        entry = {
                            "timestamp": timestamp,
                            "type": "error",
                            "error_name": error_str,
                            "error_desc": "Password length or format is incorrect" if error_str == "PASSWORD_WRONG" else "SSID length is invalid"
                        }
                    elif 'Status:' in line:
                        parts = line.split(',')
                        status_str = parts[1].split(':')[1].strip()
                        conn_time_str = parts[2].split(':')[1].strip()
                        
                        last_status, current_status = status_str.split('->')
                        last_status = int(last_status)
                        current_status = int(current_status)
                        
                        entry = {
                            "timestamp": timestamp,
                            "type": "status_transition",
                            "last_status": last_status,
                            "last_status_name": WIFI_JOIN_STATUS.get(last_status, "UNKNOWN"),
                            "last_status_desc": WIFI_STATUS_DESCRIPTIONS.get(last_status, "Unknown state"),
                            "current_status": current_status,
                            "current_status_name": WIFI_JOIN_STATUS.get(current_status, "UNKNOWN"),
                            "current_status_desc": WIFI_STATUS_DESCRIPTIONS.get(current_status, "Unknown state"),
                            "conn_time": int(conn_time_str),
                            "transition": f"{WIFI_JOIN_STATUS.get(last_status, 'UNKNOWN')} -> {WIFI_JOIN_STATUS.get(current_status, 'UNKNOWN')}"
                        }
                    else:
                        continue
                        
                    parsed.append(entry)
                except Exception as e:
                    logger.warning(f"Failed to parse line: {line}, error: {e}")
                    continue
        
        return parsed
    
    def configure_mqtt(self, broker: str, port: int = 1883, username: str = "", password: str = "") -> Dict[str, Any]:
        """Configure and connect to MQTT broker"""
        try:
            if not broker:
                return {"error": "Missing broker parameter"}
            
            self.mqtt_handler.update_config(broker, port, username, password)
            self.mqtt_handler.connect()
            
            return {
                "status": "success",
                "message": "MQTT configuration updated successfully",
                "broker": broker,
                "port": port,
                "connected": True
            }
        except Exception as e:
            return {"error": str(e)}
    
    def mqtt_status(self) -> Dict[str, Any]:
        """Check MQTT connection status and configuration"""
        try:
            conn_info = self.mqtt_handler.get_connection_info()
            
            return {
                "status": "success",
                "broker": conn_info["broker"],
                "port": conn_info["port"],
                "team": conn_info["team"],
                "connected": conn_info["connected"],
                "command_topic_pattern": conn_info["command_topic_pattern"],
                "response_topic_pattern": conn_info["response_topic_pattern"]
            }
        except Exception as e:
            return {"error": str(e)}