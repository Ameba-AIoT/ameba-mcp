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
    8: "Performing 4-way handshake, ",
    9: "4-way handshake completed, password authentiating",
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
                "name": "get_wifi_event_log",
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
    
    def get_wifi_event_log(self, device_id: str, timeout: int = 30) -> Dict[str, Any]:
        """Get WiFi connection log from IoT device using WIFILOG command"""
        try:
            if not device_id:
                return {"error": "Missing device_id parameter"}
            
            if not self.mqtt_handler.is_connected():
                return {"error": "MQTT not connected. Use configure_mqtt first."}
            
            response = self.mqtt_handler.send_command("WIFIEVENTLOG", device_id, timeout)
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

    def _identify_connection_attempts(self, parsed_log: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Identify and summarize connection attempts from the log"""
        attempts = []
        current_attempt = None
        
        for entry in parsed_log:
            entry_type = entry.get("type")
            current_status = entry.get("current_status")
            last_status = entry.get("last_status")
            
            # Handle error entries
            if entry_type == "error":
                if current_attempt:
                    current_attempt["end_time"] = entry["timestamp"]
                    current_attempt["end_status"] = "ERROR"
                    current_attempt["result"] = "error"
                    current_attempt["error"] = entry.get("error_name")
                    current_attempt["duration_ms"] = entry["timestamp"] - current_attempt["start_time"]
                    attempts.append(current_attempt)
                    current_attempt = None
                continue
            
            # Start of new attempt (STARTING state)
            if current_status == 1:
                # 如果之前有正在進行的 attempt，先結束它
                if current_attempt:
                    attempts.append(current_attempt)
                
                current_attempt = {
                    "start_time": entry["timestamp"],
                    "result": "in_progress",
                    "duration_ms": 0,
                    "failure_stage": None,
                    "error": None
                }
            
            # SUCCESS: 成功連接
            if current_attempt and current_status == 10:
                current_attempt["end_time"] = entry["timestamp"]
                current_attempt["duration_ms"] = entry["timestamp"] - current_attempt["start_time"]
                current_attempt["result"] = "success"
                attempts.append(current_attempt)
                current_attempt = None  # 結束這次 attempt
            
            # FAIL: 連接失敗
            elif current_attempt and current_status == 11:
                current_attempt["end_time"] = entry["timestamp"]
                current_attempt["duration_ms"] = entry["timestamp"] - current_attempt["start_time"]
                current_attempt["result"] = "failed"
                current_attempt["failure_stage"] = entry["last_status_name"]
                attempts.append(current_attempt)
                current_attempt = None  # 結束這次 attempt
            
            # DISCONNECT: 記錄但不算在 attempt 裡
            # (因為 disconnect 是從 SUCCESS 狀態斷線，不是一次新的連接嘗試)
        
        # 如果還有未完成的 attempt
        if current_attempt:
            attempts.append(current_attempt)
        
        return attempts

    def _generate_diagnostics(self, attempts: List[Dict], parsed_log: List[Dict]) -> Dict[str, Any]:
        """Generate diagnostic insights from connection data"""
        if not attempts:
            return {
                "issue_detected": False,
                "pattern": "no_data",
                "recommendation": "No connection attempts recorded"
            }
        
        recent_attempts = attempts[-5:]
        failed = [a for a in recent_attempts if a["result"] == "failed"]
        errors = [a for a in recent_attempts if a["result"] == "error"]
        
        current_connected = parsed_log[-1].get("current_status") == 10 if parsed_log else False
        
        # Check for errors first
        if errors:
            error = errors[-1].get("error", "UNKNOWN")
            if error == "PASSWORD_WRONG":
                return {
                    "issue_detected": True,
                    "pattern": "password_error",
                    "problem": "WiFi password is incorrect",
                    "likely_cause": "Wrong password configured",
                    "recommendation": "Verify and update the WiFi password",
                }
            elif error == "SSID_TOO_LONG":
                return {
                    "issue_detected": True,
                    "pattern": "ssid_error",
                    "problem": "SSID length is invalid",
                    "likely_cause": "SSID configuration error",
                    "recommendation": "Check SSID configuration",
                }
        
        # Check failure patterns
        if failed:
            failure_stages = {}
            for att in failed:
                stage = att.get("failure_stage", "UNKNOWN")
                failure_stages[stage] = failure_stages.get(stage, 0) + 1
            
            most_common = max(failure_stages, key=failure_stages.get)
            
            if most_common == "SCANN_DONE":
                return {
                    "issue_detected": True,
                    "pattern": "scan_failure",
                    "problem": "AP not found after scanning",
                    "likely_cause": "SSID mismatch, AP offline, or weak signal",
                    "recommendation": "Verify SSID, ensure AP is online, and check RSSI strength",
                }
            elif most_common in ["AUTHENTICATING", "AUTHENTICATED"]:
                return {
                    "issue_detected": True,
                    "pattern": "auth_failure",
                    "problem": "Stuck in authentication phase",
                    "likely_cause": "AP not responding or 802.1X/EAP issue",
                    "recommendation": "Check AP response or enterprise authentication settings",
                }
            elif most_common in ["ASSOCIATING", "ASSOCIATED"]:
                return {
                    "issue_detected": True,
                    "pattern": "association_failure",
                    "problem": "Cannot associate with AP",
                    "likely_cause": "AP capacity full or MAC filtering",
                    "recommendation": "Check router capacity, MAC filtering, and configuration",
                }
            elif most_common in ["4WAY_HANDSHAKING", "4WAY_HANDSHAKE_DONE"]:
                return {
                    "issue_detected": True,
                    "pattern": "handshake_failure",
                    "problem": "Security handshake failed",
                    "likely_cause": "Wrong password or security settings",
                    "recommendation": "Verify WiFi password and ensure AP supports WPA/WPA2/WPA3 mode used by the device",
                }
        
        # Check if currently connected
        if current_connected:
            return {
                "issue_detected": False,
                "pattern": "stable",
                "problem": None,
                "likely_cause": None,
                "recommendation": "Device is currently connected and stable",
            }
        else:
            return {
                "issue_detected": True,
                "pattern": "disconnected",
                "problem": "Device is not connected",
                "likely_cause": "Connection lost or never established",
                "recommendation": "Check recent connection attempts and signal stability",
            }

    def _get_attempts_pattern(self, attempts: List[Dict]) -> str:
        """Generate a simple pattern string for last attempts (e.g., 'SFFFS')"""
        pattern = ""
        for att in attempts:
            result = att.get("result", "U")
            if result == "success":
                pattern += "S"
            elif result == "failed":
                pattern += "F"
            elif result == "error":
                pattern += "E"
            elif result == "disconnected":
                pattern += "D"
            else:
                pattern += "U"
        return pattern if pattern else "N/A"    
    
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

            # Identify connection attempts
            attempts = self._identify_connection_attempts(parsed_log)
            current_state = parsed_log[-1]


            success_count = sum(1 for att in attempts if att["result"] == "success")
            fail_count = sum(1 for att in attempts if att["result"] == "failed")
            error_count = sum(1 for att in attempts if att["result"] == "error")

            # Count disconnects from parsed_log (they're not in attempts)
            disconnect_count = sum(1 for item in parsed_log if item.get("current_status") == 12)
            
            # Generate diagnostics
            diagnostics = self._generate_diagnostics(attempts, parsed_log)

            # Calculate attempts pattern
            last_pattern = self._get_attempts_pattern(attempts)
            

            # Build summary
            summary = {
                "is_connected": current_state.get("current_status") == 10,
                "total_attempts": len(attempts),
                "successful": success_count,
                "failed": fail_count,
                "errors": error_count,
                "disconnections": disconnect_count,
                "last_attempts": last_pattern
            }

            # Build recent attempts
            all_attempts = [
                {
                    "attempt": i + 1,
                    "result": att["result"],
                    "duration_ms": att.get("duration_ms", 0),
                    "failure_stage": att.get("failure_stage"),
                    "error": att.get("error")
                }
                for i, att in enumerate(attempts)
            ]

            return {
                "status": "success",
                "message": f"WiFi Connection Status from {device_id}",
                "device_id": device_id,
                "summary": summary,
                "diagnostics": diagnostics,
                "recent_attempts": all_attempts,
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