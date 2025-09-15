from typing import Any, Dict, List, Optional
from datetime import datetime, timezone
import logging

logger = logging.getLogger("iot-tools-sync")

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