from .connection_manager import ConnectionManager
from .connection_module import ConnectionModule
from .feature_module import FeatureModule
from typing import Any, Dict, List, Optional, Protocol
from mcp.types import Tool
import asyncio
import json

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
