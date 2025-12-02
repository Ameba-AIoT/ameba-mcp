import json
import logging
import os
import uuid
import time
from datetime import datetime, timezone
from typing import Dict, Optional, List
from dotenv import load_dotenv
import paho.mqtt.client as mqtt

logger = logging.getLogger("mqtt-handler-sync")

class SyncMQTTHandler:
    """Synchronous MQTT handler for MCP Wrapper compatibility"""
    
    def __init__(self):
        self.mqtt_client: Optional[mqtt.Client] = None
        self.device_responses: Dict[str, Dict] = {}
        self.pending_requests: Dict[str, bool] = {}
        self.received_events: List[Dict] = []
        load_dotenv()

        # Load configuration from environment variables
        self.mqtt_broker = os.getenv("MQTT_BROKER", "localhost")
        self.mqtt_port = int(os.getenv("MQTT_PORT", "1883"))
        self.mqtt_username = os.getenv("MQTT_USERNAME", "")
        self.mqtt_password = os.getenv("MQTT_PASSWORD", "")
        self.team_prefix = os.getenv("TEAM_PREFIX", "iot")
        
        # MQTT Topics
        self.base_topic = f"rtk/v1/rtk-home/living-room"
        self.command_counter = 0

        self.connected = False

    def connect(self):
        """Establish MQTT connection"""
        try:
            client_id = f"wifi_diagnostic_mcp_{self.team_prefix}_{uuid.uuid4().hex[:8]}"
            self.mqtt_client = mqtt.Client(client_id=client_id)
            
            if self.mqtt_username:
                self.mqtt_client.username_pw_set(self.mqtt_username, self.mqtt_password)
            
            # Setup callback functions
            self.mqtt_client.on_connect = self._on_connect
            self.mqtt_client.on_message = self._on_message
            self.mqtt_client.on_disconnect = self._on_disconnect
            
            # Connect to broker
            logger.info(f"Connecting to MQTT broker: {self.mqtt_broker}:{self.mqtt_port}")
            self.mqtt_client.connect(self.mqtt_broker, self.mqtt_port, 60)
            self.mqtt_client.loop_start()
            
            # Wait for connection
            timeout = 5
            while not self.connected and timeout > 0:
                time.sleep(0.1)
                timeout -= 0.1
            
            if not self.connected:
                raise Exception("Failed to connect to MQTT broker")
                
            logger.info("MQTT connection established")
            return True
                
        except Exception as e:
            logger.error(f"MQTT connection error: {e}")
            raise

    def disconnect(self):
        """Disconnect from MQTT broker"""
        if self.mqtt_client:
            self.mqtt_client.loop_stop()
            self.mqtt_client.disconnect()
            self.connected = False
            logger.info("MQTT connection closed")

    def is_connected(self) -> bool:
        """Check MQTT connection status"""
        return self.connected and self.mqtt_client is not None

    def _on_connect(self, client, userdata, flags, rc):
        """MQTT connection callback"""
        if rc == 0:
            self.connected = True
            logger.info("Connected to MQTT broker successfully")
            # Subscribe to response topics
            client.subscribe(f"{self.base_topic}/+/cmd/res")
            client.subscribe(f"{self.base_topic}/+/evt/#")
            logger.info(f"Subscribed to response and event topics")
        else:
            logger.error(f"Failed to connect to MQTT broker, return code: {rc}")

    def _on_message(self, client, userdata, msg):
        """MQTT message callback"""
        try:
            topic = msg.topic
            payload = json.loads(msg.payload.decode())
            logger.info(f"Received message on {topic}")
            
            if "/cmd/res" in topic:
                request_id = payload.get("payload", {}).get("id")
                if request_id and request_id in self.pending_requests:
                    self.device_responses[request_id] = payload
                    self.pending_requests[request_id] = True
            
            elif "/evt/" in topic:
                # Log event (band switch, etc.)
                self.received_events.append(payload)
                event_type = payload.get("payload", {}).get("event_type", "unknown")
                logger.info(f"[EVENT] Received: {event_type}")
                    
        except Exception as e:
            logger.error(f"Error processing MQTT message: {e}")

    def _on_disconnect(self, client, userdata, rc):
        """MQTT disconnect callback"""
        self.connected = False
        logger.warning(f"Disconnected from MQTT broker, return code: {rc}")

    def send_command_no_wait(self, op: str, device_id: str, args: dict = None) -> bool:
        """Send command without waiting for response (fire-and-forget)"""
        if not self.is_connected():
            return False
        
        self.command_counter += 1
        op_formatted = op.replace("_", "-")
        request_id = f"cmd-iot-{op_formatted}-{self.command_counter:03d}"
        
        device_command_topic = f"{self.base_topic}/{device_id}/cmd/req"
        
        payload = {
            "schema": f"cmd.iot.{op}/1.0",
            "ts": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
            "payload": {
                "id": request_id,
                "op": op,
                "args": args or {},
                "timeout_ms": 45000,
                "expect": "result"
            }
        }
        
        result = self.mqtt_client.publish(device_command_topic, json.dumps(payload))
        logger.info(f"Sent command '{op}' to device '{device_id}' (no wait)")
        
        return result.rc == mqtt.MQTT_ERR_SUCCESS

    def send_command(self, op: str, device_id: str, args: dict = None, timeout: int = 30) -> Dict:
        """Send command and wait for response (synchronous)"""
        if not self.is_connected():
            raise Exception("MQTT not connected")
        
        self.command_counter += 1
        op_formatted = op.replace("_", "-")
        request_id = f"cmd-iot-{op_formatted}-{self.command_counter:03d}"
        
        # Build device-specific command topic
        device_command_topic = f"{self.base_topic}/{device_id}/cmd/req"
        
        # Prepare command payload (RTK format)
        payload = {
            "schema": f"cmd.iot.{op}/1.0",
            "ts": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
            "payload": {
                "id": request_id,
                "op": op,
                "args": args or {},
                "timeout_ms": timeout * 1000,
                "expect": "result"
            }
        }
        
        # Initialize pending request
        self.pending_requests[request_id] = False
        
        try:
            # Send command
            result = self.mqtt_client.publish(device_command_topic, json.dumps(payload))
            
            if result.rc != mqtt.MQTT_ERR_SUCCESS:
                raise Exception(f"Failed to publish command: {result.rc}")
            
            logger.info(f"Sent command '{op}' to device '{device_id}'")
            
            # Wait for response (polling)
            elapsed = 0
            while elapsed < timeout:
                if self.pending_requests.get(request_id, False):
                    break
                time.sleep(0.1)
                elapsed += 0.1
            
            if not self.pending_requests.get(request_id, False):
                raise Exception(f"Timeout waiting for response from device {device_id}")
            
            # Get response
            response = self.device_responses.get(request_id)
            if not response:
                raise Exception("No response received from device")
            
            # Check response status
            status = response.get("payload", {}).get("status")
            if status == "failed":
                raise Exception("Device command failed")
            
            return response
            
        finally:
            # Cleanup
            if request_id in self.pending_requests:
                del self.pending_requests[request_id]
            if request_id in self.device_responses:
                del self.device_responses[request_id]

    def update_config(self, broker: str, port: int, username: str = "", password: str = ""):
        """Update MQTT configuration"""
        # Disconnect existing connection if any
        if self.is_connected():
            self.disconnect()
        
        # Update configuration
        self.mqtt_broker = broker
        self.mqtt_port = port
        self.mqtt_username = username
        self.mqtt_password = password
        
        # Clear cached client
        self.mqtt_client = None
        self.connected = False
        
        logger.info(f"MQTT configuration updated: {broker}:{port}")

    def get_connection_info(self) -> Dict:
        """Get connection information"""
        return {
            "broker": self.mqtt_broker,
            "port": self.mqtt_port,
            "team": self.team_prefix,
            "command_topic_pattern": f"{self.base_topic}/{{device_id}}/cmd/req",
            "response_topic_pattern": f"{self.base_topic}/{{device_id}}/cmd/res",
            "connected": self.is_connected()
        }