#!/usr/bin/env python3
"""
WiFi Diagnostic MCP Server - Compatible with MCP Wrapper
STDIO version for direct use or HTTP wrapping
"""

import sys
import json
import logging
from typing import Dict, Any

# Import our modules
from mqtt_handler_sync import SyncMQTTHandler
from iot_tools_sync import IoTWiFiTools

# Configure logging to stderr
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stderr)]
)
logger = logging.getLogger(__name__)


class WiFiDiagnosticServer:
    """WiFi Diagnostic MCP Server - Compatible with MCP Wrapper"""
    
    def __init__(self):
        # Initialize components
        self.mqtt_handler = SyncMQTTHandler()
        self.iot_tools = IoTWiFiTools(self.mqtt_handler)
        
        # Create tools mapping
        self.tools = {
            "get_device_status": self.iot_tools.get_device_status,
            "get_device_rssi": self.iot_tools.get_device_rssi,
            "get_wifi_event_log": self.iot_tools.get_wifi_event_log,
            "clear_wifi_event_log": self.iot_tools.clear_wifi_event_log,
            "get_wifi_connection_status": self.iot_tools.get_wifi_connection_status,
            "clear_wifi_connection_status": self.iot_tools.clear_wifi_connection_status,
            "run_iperf_tx_test": self.iot_tools.run_iperf_tx_test, 
            "get_tx_rate": self.iot_tools.get_tx_rate, 
            "connect_wifi": self.iot_tools.connect_wifi,  
            "ping_test": self.iot_tools.ping_test,
            "configure_mqtt": self.iot_tools.configure_mqtt,
            "mqtt_status": self.iot_tools.mqtt_status,
        }
        
        # Try to connect to MQTT on startup
        try:
            self.mqtt_handler.connect()
            logger.info("MQTT connected on startup")
        except Exception as e:
            logger.warning(f"MQTT connection failed on startup: {e}. Use configure_mqtt to connect later.")
    
    def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle JSON-RPC request"""
        try:
            method = request.get("method")
            params = request.get("params", {})
            request_id = request.get("id")
            
            # Handle standard MCP methods
            if method == "initialize":
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {
                        "protocolVersion": "2025-06-18",
                        "capabilities": {
                            "tools": {}
                        },
                        "serverInfo": {
                            "name": "wifi-diagnostic-server",
                            "version": "1.0.0"
                        }
                    }
                }
            
            elif method == "notifications/initialized":
                logger.info("Client initialized")
                return None

            elif method == "tools/list":
                tools_list = self.iot_tools.get_tools_definitions()
                
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {
                        "tools": tools_list
                    }
                }
            
            elif method == "prompts/list":
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {
                        "prompts": []
                    }
                }
            
            elif method == "resources/list":
                return {
                    "jsonrpc": "2.0", 
                    "id": request_id,
                    "result": {
                        "resources": []
                    }
                }

            elif method == "tools/call":
                tool_name = params.get("name")
                tool_args = params.get("arguments", {})
                
                if tool_name in self.tools:
                    result = self.tools[tool_name](**tool_args)
                    return {
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "result": {
                            "content": [
                                {
                                    "type": "text",
                                    "text": json.dumps(result, indent=2)
                                }
                            ]
                        }
                    }
                else:
                    return {
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "error": {
                            "code": -32601,
                            "message": f"Unknown tool: {tool_name}"
                        }
                    }
            
            else:
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "error": {
                        "code": -32601,
                        "message": f"Method not found: {method}"
                    }
                }
                
        except Exception as e:
            logger.error(f"Error handling request: {e}")
            return {
                "jsonrpc": "2.0",
                "id": request.get("id"),
                "error": {
                    "code": -32603,
                    "message": str(e)
                }
            }
    
    def run(self):
        """Run the MCP server, reading from stdin and writing to stdout"""
        logger.info("WiFi Diagnostic MCP Server started")
        
        while True:
            try:
                # Read line from stdin
                line = sys.stdin.readline()
                if not line:
                    break
                
                # Parse JSON request
                request = json.loads(line.strip())
                logger.info(f"Received request: {request.get('method')}")
                
                # Handle request
                response = self.handle_request(request)

                # Write response to stdout
                if response is not None:
                    sys.stdout.write(json.dumps(response) + "\n")
                    sys.stdout.flush()
                
            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON: {e}")
                error_response = {
                    "jsonrpc": "2.0",
                    "id": None,
                    "error": {
                        "code": -32700,
                        "message": "Parse error"
                    }
                }
                sys.stdout.write(json.dumps(error_response) + "\n")
                sys.stdout.flush()
            except KeyboardInterrupt:
                logger.info("Server interrupted")
                break
            except Exception as e:
                logger.error(f"Unexpected error: {e}")
                continue
        
        # Cleanup
        try:
            self.mqtt_handler.disconnect()
        except:
            pass
        
        logger.info("WiFi Diagnostic MCP Server stopped")


def main():
    """Entry point for uv script"""
    server = WiFiDiagnosticServer()
    server.run()

if __name__ == "__main__":
    main()