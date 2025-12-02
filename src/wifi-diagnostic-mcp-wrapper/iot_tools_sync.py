from typing import Any, Dict, List, Optional
from datetime import datetime, timezone
import logging
import time

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
                "name": "get_device_info",
                "description": "Get current WiFi information from IoT device using ATW? command",
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
                "description": "Get WiFi event log from IoT device using WIFIEVENTLOG command",
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
                "name": "clear_wifi_event_log",
                "description": """Clear the WiFi event log on the IoT device.
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
                "name": "run_iperf_tx_test",
                "description": """Run iPerf TCP transmit test to measure network throughput.
                Tests upload speed by sending data to an iPerf server.
                Returns periodic throughput measurements and overall statistics.""",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "device_id": {
                            "type": "string",
                            "description": "IoT device identifier"
                        },
                        "server_ip": {
                            "type": "string",
                            "description": "iPerf server IP address"
                        },
                        "duration": {
                            "type": "integer",
                            "description": "Test duration in seconds",
                            "default": 30
                        },
                        "interval": {
                            "type": "integer",
                            "description": "Report interval in seconds",
                            "default": 1
                        },
                        "timeout": {
                            "type": "integer",
                            "description": "Response timeout in seconds",
                            "default": 60
                        }
                    },
                    "required": ["device_id", "server_ip"]
                }
            },
            {
                "name": "get_tx_rate",
                "description": """Get current WiFi TX (transmit) rate and MCS information.
                Shows the actual data rate being used for transmissions.""",
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
                "name": "get_wifi_clm_info",
                "description": """Get WiFi Channel Load Measurement (CLM) information.
                    Returns CLM ratio, NHM idle ratio, and NHM tx ratio.
                    CLM > 65% indicates network congestion.""",
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
                "name": "trigger_jammer",
                "description": """Trigger 2.4GHz wifi clm updated test.
                    Sends iPerf command to jammer device to create 2.4GHz interference.
                    Camera will detect CLM congestion and auto-switch to 5GHz.
                    Returns the wifi clm updated event when camera completes switching.""",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "timeout": {
                            "type": "integer",
                            "description": "Timeout waiting for wifi clm updated event (seconds)",
                            "default": 60
                        }
                    }
                }
            },
            {
                "name": "connect_wifi",
                "description": """Connect to a new WiFi network with specified SSID and password.
                This will disconnect the device from current network.
                The device will reconnect to MQTT after WiFi connection is established.""",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "device_id": {
                            "type": "string",
                            "description": "IoT device identifier"
                        },
                        "ssid": {
                            "type": "string",
                            "description": "WiFi network SSID"
                        },
                        "password": {
                            "type": "string",
                            "description": "WiFi network password"
                        },
                        "timeout": {
                            "type": "integer",
                            "description": "Response timeout in seconds",
                            "default": 45
                        }
                    },
                    "required": ["device_id", "ssid", "password"]
                }
            },
            {
                "name": "ping_test",
                "description": """Run ping test to check network connectivity and latency.
                Tests connection to specified IP address (usually gateway or PC).
                Returns packet loss statistics and latency measurements.""",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "device_id": {
                            "type": "string",
                            "description": "IoT device identifier"
                        },
                        "target_ip": {
                            "type": "string",
                            "description": "Target IP address (PC or gateway)"
                        },
                        "timeout": {
                            "type": "integer",
                            "description": "Response timeout in seconds",
                            "default": 30
                        }
                    },
                    "required": ["device_id", "target_ip"]
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
    
    def get_device_info(self, device_id: str, timeout: int = 30) -> Dict[str, Any]:
        """Get current WiFi status from IoT device using ATW? command"""
        try:
            if not device_id:
                return {"error": "Missing device_id parameter"}
            
            if not self.mqtt_handler.is_connected():
                return {"error": "MQTT not connected. Use configure_mqtt first."}
            
            response = self.mqtt_handler.send_command("get_device_info", device_id, {}, timeout)
            raw_response = response.get("payload", {}).get("result", {}).get("response", "")
            
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
            
            response = self.mqtt_handler.send_command("get_device_rssi", device_id, {}, timeout)
            raw_response = response.get("payload", {}).get("result", {}).get("response", "")
            
            return {
                "status": "success",
                "message": f"ATWR Response from {device_id}",
                "device_id": device_id,
                "raw_response": raw_response,
                "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
            }
        except Exception as e:
            return {"error": str(e)}
        
    def get_wifi_clm_info(self, device_id: str, timeout: int = 30) -> Dict[str, Any]:
        """Get WiFi CLM (Channel Load Measurement) information"""
        try:
            if not device_id:
                return {"error": "Missing device_id parameter"}
            
            if not self.mqtt_handler.is_connected():
                return {"error": "MQTT not connected. Use configure_mqtt first."}
            
            response = self.mqtt_handler.send_command("get_wifi_clm_info", device_id, {}, timeout)
            raw_response = response.get("payload", {}).get("result", {}).get("response", "")
            
            # Parse CLM info from response
            clm_info = self._parse_clm_info(raw_response)
            
            return {
                "status": "success",
                "message": f"CLM info from {device_id}",
                "device_id": device_id,
                "clm_info": clm_info,
                "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
            }
        except Exception as e:
            return {"error": str(e)}

    def _parse_clm_info(self, raw_response: str) -> Dict[str, Any]:
        """Parse CLM info from raw response"""
        clm_info = {
            "clm_ratio": None,
            "nhm_idle_ratio": None,
            "nhm_tx_ratio": None,
            "congestion_level": "unknown"
        }
        
        try:
            # Parse: "CLM ratio: 45%, NHM idle: 30%, NHM tx: 25%"
            import re
            clm_match = re.search(r'CLM ratio:\s*(\d+)', raw_response)
            nhm_idle_match = re.search(r'NHM idle:\s*(\d+)', raw_response)
            nhm_tx_match = re.search(r'NHM tx:\s*(\d+)', raw_response)
            
            if clm_match:
                clm_info["clm_ratio"] = int(clm_match.group(1))
            if nhm_idle_match:
                clm_info["nhm_idle_ratio"] = int(nhm_idle_match.group(1))
            if nhm_tx_match:
                clm_info["nhm_tx_ratio"] = int(nhm_tx_match.group(1))
            
            # Determine congestion level
            if clm_info["clm_ratio"] is not None:
                clm = clm_info["clm_ratio"]
                if clm < 30:
                    clm_info["congestion_level"] = "low"
                elif clm < 65:
                    clm_info["congestion_level"] = "moderate"
                else:
                    clm_info["congestion_level"] = "high"
        except Exception as e:
            pass
        
        return clm_info

    def get_wifi_event_log(self, device_id: str, timeout: int = 30) -> Dict[str, Any]:
        """Get WiFi connection log from IoT device using WIFIEVENTLOG command"""
        try:
            if not device_id:
                return {"error": "Missing device_id parameter"}
            
            if not self.mqtt_handler.is_connected():
                return {"error": "MQTT not connected. Use configure_mqtt first."}
            
            response = self.mqtt_handler.send_command("get_wifi_event_log", device_id, {}, timeout)
            raw_response = response.get("payload", {}).get("result", {}).get("response", "")
            
            return {
                "status": "success",
                "message": f"WIFIEVENTLOG Response from {device_id}",
                "device_id": device_id,
                "raw_response": raw_response,
                "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
            }
        except Exception as e:
            return {"error": str(e)}

    def clear_wifi_event_log(self, device_id: str, timeout: int = 30) -> Dict[str, Any]:
        """Clear WiFi connection status log on the device"""
        try:
            if not device_id:
                return {"error": "Missing device_id parameter"}
            
            if not self.mqtt_handler.is_connected():
                return {"error": "MQTT not connected. Use configure_mqtt first."}
            
            response = self.mqtt_handler.send_command("clear_wifi_event_log", device_id, {}, timeout)
            raw_response = response.get("payload", {}).get("result", {}).get("response", "")
            
            return {
                "status": "success",
                "message": f"WiFi event log cleared on {device_id}",
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
        
        recent_attempts = attempts
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
            
            response = self.mqtt_handler.send_command("get_wifi_connection_status", device_id, {}, timeout)
            raw_response = response.get("payload", {}).get("result", {}).get("response", "")
            
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
            
            response = self.mqtt_handler.send_command("clear_wifi_connection_status", device_id, {}, timeout)
            raw_response = response.get("payload", {}).get("result", {}).get("response", "")
            
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
    
    def run_iperf_tx_test(self, device_id: str, server_ip: str, duration: int = 30, 
                      interval: int = 1, timeout: int = 60) -> Dict[str, Any]:
        """Run iPerf TCP transmit test"""
        try:
            if not device_id or not server_ip:
                return {"error": "Missing required parameters"}
            
            if not self.mqtt_handler.is_connected():
                return {"error": "MQTT not connected. Use configure_mqtt first."}
            
            # Build iPerf command: ATWT=-c,server_IP,-t,duration,-i,interval
            # UDP mode is more stable: ATWU=-c,server_IP,-t,duration,-i,interval,-b,bandwidth(ex. 10m)
            args = {
                "server_ip": server_ip,
                "duration_s": duration
            }
            response = self.mqtt_handler.send_command("run_iperf_tx_test", device_id, args, timeout)
            raw_response = response.get("payload", {}).get("result", {}).get("response", "")
            
            # Parse iPerf results
            parsed_results = self._parse_iperf_results(raw_response)
            
            video_assessment = self._assess_video_streaming(parsed_results)
            return {
                "status": "success",
                "message": f"iPerf TX test completed for {device_id}",
                "device_id": device_id,
                "server_ip": server_ip,
                "test_duration": duration,
                "results": parsed_results,
                "video_streaming_assessment": video_assessment,
                "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
            }
        except Exception as e:
            return {"error": str(e)}

    def get_tx_rate(self, device_id: str, timeout: int = 30) -> Dict[str, Any]:
        """Get current WiFi TX rate and MCS information"""
        try:
            if not device_id:
                return {"error": "Missing device_id parameter"}
            
            if not self.mqtt_handler.is_connected():
                return {"error": "MQTT not connected. Use configure_mqtt first."}
            
            response = self.mqtt_handler.send_command("get_tx_rate", device_id, {}, timeout)
            raw_response = response.get("payload", {}).get("result", {}).get("response", "")
            
            # Parse TX rate from response
            tx_info = self._parse_tx_rate(raw_response)
            
            return {
                "status": "success",
                "message": f"TX rate information from {device_id}",
                "device_id": device_id,
                "tx_info": tx_info,
                "raw_response": raw_response,
                "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
            }
        except Exception as e:
            return {"error": str(e)}

    def connect_wifi(self, device_id: str, ssid: str, password: str, 
                    timeout: int = 45) -> Dict[str, Any]:
        """Connect to a new WiFi network"""
        try:
            if not device_id or not ssid or not password:
                return {"error": "Missing required parameters"}
            
            if not self.mqtt_handler.is_connected():
                return {"error": "MQTT not connected. Use configure_mqtt first."}
            
            args = {
                "ssid": ssid,
                "password": password
            }
            
            # Step 3: Connect (ATWC)
            response = self.mqtt_handler.send_command("connect_wifi", device_id, args, timeout)
            raw_response = response.get("payload", {}).get("result", {}).get("response", "")
            
            return {
                "status": "success",
                "message": f"WiFi connection initiated on {device_id}",
                "device_id": device_id,
                "ssid": ssid,
                "raw_response": raw_response,
                "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
            }
        except Exception as e:
            return {"error": str(e)}

    def ping_test(self, device_id: str, target_ip: str, timeout: int = 30) -> Dict[str, Any]:
        """Run ping test to check network connectivity"""
        try:
            if not device_id or not target_ip:
                return {"error": "Missing required parameters"}
            
            if not self.mqtt_handler.is_connected():
                return {"error": "MQTT not connected. Use configure_mqtt first."}
            
            # Build args for ping test
            args = {
                "target_ip": target_ip
            }
            response = self.mqtt_handler.send_command("ping_test", device_id, args, timeout)
            raw_response = response.get("payload", {}).get("result", {}).get("response", "")
            
            # Parse ping results
            ping_stats = self._parse_ping_results(raw_response)
            ping_stats_assessment = self._assess_latency_for_video(ping_stats)
            
            return {
                "status": "success",
                "message": f"Ping test completed for {device_id}",
                "device_id": device_id,
                "target_ip": target_ip,
                "statistics": ping_stats,
                "latency_assessment": ping_stats_assessment,
                "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
            }
        except Exception as e:
            return {"error": str(e)}

    def trigger_jammer(self, timeout: int = 60) -> Dict[str, Any]:
        """Trigger 2.4GHz congestion demo and wait for band switch event"""
        try:
            if not self.mqtt_handler.is_connected():
                return {"error": "MQTT not connected. Use configure_mqtt first."}
            
            jammer_device_id = "jammer"
            iperf_server_ip = "192.168.0.100"
            iperf_duration = 30
            
            # Clear previous events
            self.mqtt_handler.received_events.clear()
            
            # Start iPerf on jammer device
            args = {
                "server_ip": iperf_server_ip,
                "duration_s": iperf_duration
            }
            self.mqtt_handler.send_command_no_wait("run_iperf_tx_test", jammer_device_id, args)
            logger.info(f"[DEMO] Interference triggered")
            
            # Wait for wifi clm updated event
            logger.info(f"[DEMO] Waiting for wifi clm updated event...")
            
            start_time = time.time()
            while (time.time() - start_time) < timeout:
                for event in self.mqtt_handler.received_events:
                    payload = event.get("payload", {})
                    if payload.get("event_type") == "wifi_clm_updated":
                        # Return event directly (already JSON format from device)
                        return event
                time.sleep(0.5)
            
            return {
                "status": "timeout",
                "message": "Wifi clm updated event not received within timeout",
                "hint": "Camera may not have detected enough congestion, or CLM threshold not reached",
                "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
            }
            
        except Exception as e:
            return {"error": str(e)}

    def _assess_video_streaming(self, iperf_results: Dict[str, Any]) -> Dict[str, Any]:
        """Assess if network conditions are suitable for video streaming"""
        avg_kbps = iperf_results.get("average_kbps", 0)
        avg_mbps = avg_kbps / 1000.0
        
        assessment = {
            "throughput_mbps": round(avg_mbps, 2),
            "suitable_for_video": False,
            "quality_level": "unsuitable",
            "recommendation": ""
        }
        
        if avg_mbps < 5:
            assessment["suitable_for_video"] = False
            assessment["quality_level"] = "unsuitable"
            assessment["recommendation"] = "Current network conditions are NOT suitable for video transmission. Throughput is below 5 Mbps."
        elif avg_mbps < 10:
            assessment["suitable_for_video"] = True
            assessment["quality_level"] = "basic"
            assessment["recommendation"] = "Network can support basic quality video streaming (5-10 Mbps). Consider lower resolution for stable transmission."
        elif avg_mbps < 40:
            assessment["suitable_for_video"] = True
            assessment["quality_level"] = "good"
            assessment["recommendation"] = "Good network conditions for video streaming (10-40 Mbps). Suitable for HD video transmission."
        else:
            assessment["suitable_for_video"] = True
            assessment["quality_level"] = "excellent"
            assessment["recommendation"] = "Excellent network conditions for video streaming (>40 Mbps). Optimal for high-quality video transmission."
        
        return assessment
    
    def _assess_latency_for_video(self, ping_stats: Dict[str, Any]) -> Dict[str, Any]:
        """Assess if latency is suitable for video streaming"""
        avg_ms = ping_stats.get("average_ms", 0)
        
        assessment = {
            "latency_ms": avg_ms,
            "suitable_for_video": False,
            "quality_level": "unsuitable",
            "recommendation": ""
        }
        
        if avg_ms < 50:
            assessment["suitable_for_video"] = True
            assessment["quality_level"] = "excellent"
            assessment["recommendation"] = f"Low latency ({avg_ms}ms < 50ms). Excellent for real-time video streaming."
        else:
            assessment["suitable_for_video"] = False
            assessment["quality_level"] = "high_latency"
            assessment["recommendation"] = f"High latency ({avg_ms}ms > 50ms). May affect real-time video quality."
        
        return assessment

    def _parse_iperf_results(self, raw_response: str) -> Dict[str, Any]:
        """Parse iPerf test results from raw response"""
        # results = {
        #     "intervals": [],
        #     "total_sent_kb": 0,
        #     "total_time_ms": 0,
        #     "average_kbps": 0,
        #     "min_kbps": 0,
        #     "max_kbps": 0
        # }
        results = {
            "total_sent_kb": 0,
            "total_time_ms": 0,
            "average_kbps": 0,
            "min_kbps": 0,
            "max_kbps": 0
        }
        
        try:
            lines = raw_response.split('\n')
            interval_kbps_list = []
            
            for line in lines:
                # Parse interval data: "tcp_client_func: Send 5360 KBytes in 1000 ms, 43916 Kbits/sec"
                if "udp_client_func:" in line and "KBytes" in line and "Kbits/sec" in line and ("Send" in line or "send" in line):
                    try:
                        parts = line.split()
                        # Find indices of key values
                        send_idx = -1
                        for i, part in enumerate(parts):
                            if part == "Send" or part == "send":
                                send_idx = i
                                break

                        if send_idx == -1:
                            continue
                            
                        in_idx = parts.index("in")

                        kb_sent = int(parts[send_idx + 1])
                        time_ms = int(parts[in_idx + 1])

                        # Find Kbits/sec value (last numeric value before "Kbits/sec")
                        kbps = 0
                        for i in range(len(parts)-1, -1, -1):
                            if "Kbits/sec" in parts[i]:
                                kbps = int(parts[i-1].replace(',', ''))
                                break

                        if "[END]" in line or "Totally" in line:
                            # This is the total summary
                            results["total_sent_kb"] = kb_sent
                            results["total_time_ms"] = time_ms
                            results["average_kbps"] = kbps
                        else:
                            # This is an interval measurement
                            # results["intervals"].append({
                            #     "sent_kb": kb_sent,
                            #     "time_ms": time_ms,
                            #     "kbps": kbps
                            # })
                            interval_kbps_list.append(kbps)
                    except (ValueError, IndexError) as e:
                        logger.warning(f"Failed to parse line: {line}, error: {e}")
                        continue
            
            # Calculate min/max from intervals
            if interval_kbps_list:
                results["min_kbps"] = min(interval_kbps_list)
                results["max_kbps"] = max(interval_kbps_list)
                
        except Exception as e:
            logger.warning(f"Failed to parse iPerf results: {e}")
        
        return results

    def _parse_tx_rate(self, raw_response: str) -> Dict[str, Any]:
        """Parse TX rate information from raw response"""
        tx_info = {
            "rate_index": None,
            "mcs_mode": None,
            "rate_description": None
        }
        
        try:
            # Parse: "[fATWd] Show Tx MCS Rate, tx_rate: 19[HT_MCS7]"
            if "tx_rate:" in raw_response:
                rate_part = raw_response.split("tx_rate:")[1].strip()
                # Extract rate index and MCS mode
                if "[" in rate_part and "]" in rate_part:
                    rate_index = rate_part.split("[")[0].strip()
                    mcs_mode = rate_part.split("[")[1].split("]")[0].strip()
                    
                    tx_info["rate_index"] = rate_index
                    tx_info["mcs_mode"] = mcs_mode
                    tx_info["rate_description"] = f"Rate index {rate_index} ({mcs_mode})"
        except Exception as e:
            logger.warning(f"Failed to parse TX rate: {e}")
        
        return tx_info

    def _parse_ping_results(self, raw_response: str) -> Dict[str, Any]:
        """Parse ping test results from raw response"""
        stats = {
            "packets_transmitted": 0,
            "packets_received": 0,
            "packet_loss_percent": 0,
            "average_ms": 0,
            "min_ms": 0,
            "max_ms": 0,
            "ping_responses": []
        }
        
        try:
            lines = raw_response.split('\n')
            for line in lines:
                # Parse individual ping responses: "[ping_test] 32 bytes from 192.168.0.1: icmp_seq=1 time=2 ms"
                if "bytes from" in line and "icmp_seq=" in line and "time=" in line:
                    parts = line.split()
                    for i, part in enumerate(parts):
                        if part.startswith("time="):
                            time_ms = int(part.split("=")[1])
                            stats["ping_responses"].append(time_ms)
                
                # Parse summary: "[ping_test] 4 packets transmitted, 4 received, 0% packet loss, average 1 ms"
                if "packets transmitted" in line:
                    parts = line.split()
                    for i, part in enumerate(parts):
                        if part == "packets" and i > 0 and parts[i-1].isdigit():
                            stats["packets_transmitted"] = int(parts[i-1])
                        if part == "received," and i > 0 and parts[i-1].isdigit():
                            stats["packets_received"] = int(parts[i-1])
                        if part.endswith("%") and "loss" in line:
                            stats["packet_loss_percent"] = float(part.rstrip("%"))
                        if part == "average" and i+1 < len(parts):
                            stats["average_ms"] = int(parts[i+1])
                
                # Parse min/max: "[ping_test] min: 0 ms, max: 2 ms"
                if "min:" in line and "max:" in line:
                    parts = line.split()
                    for i, part in enumerate(parts):
                        if part == "min:" and i+1 < len(parts):
                            stats["min_ms"] = int(parts[i+1])
                        if part == "max:" and i+1 < len(parts):
                            stats["max_ms"] = int(parts[i+1])
        except Exception as e:
            logger.warning(f"Failed to parse ping results: {e}")
        
        return stats

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