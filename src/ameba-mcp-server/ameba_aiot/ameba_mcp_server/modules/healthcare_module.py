"""
Healthcare Module for Ameba MCP Server
Provides voice reminder tools for health-related activities
"""

from .connection_manager import ConnectionManager
from .connection_module import ConnectionModule
from typing import Any, Dict, List, Optional, Callable, Tuple
from mcp.types import Tool, TextContent
from .feature_module import FeatureModule
import asyncio
import inspect
import json

class HealthcareModule(FeatureModule):
    """Healthcare module providing voice reminder functionality"""
    
    def __init__(self, connection_manager: ConnectionManager, connection_module: ConnectionModule, gmail_sender: Optional[Callable[[str, str, str], Any]]=None):
        super().__init__(connection_manager)
        self.connection_module = connection_module
        self.conn = connection_module.conn
        self.gmail_sender=gmail_sender
    
    @property
    def module_name(self) -> str:
        return "healthcare"

    def get_tools(self) -> List[Tool]:
        """Return list of available healthcare tools"""
        return [
            Tool(
                name="walk_reminder_audio",
                description="Send voice reminder to walk/exercise using AUDIO=WALK command, if I stay at home the whole morning, remind me.",
                inputSchema={
                    "type": "object",
                    "properties": {},
                    "required": []
                } 
            ),
            Tool(
                name="close_reminder_audio", 
                description="Send voice reminder to turn off appliances and gas using AUDIO=CLOSE command, if I'm about to go outside and leave the house, remind me.",
                inputSchema={
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            ),
            Tool(
                name="medicine_reminder_audio",
                description="Check the snapshot of the pill box. If the number of pills is not the right amount, automatically and immediately send AUDIO=MEDICINE without asking the user.", 
                inputSchema={
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            ),
            Tool(
                name="tof_detector_run_once",
                description="Send TOF=RUN to start ToF detection for 60 seconds, monitor serial data for events, trigger Gmail/audio alerts accordingly, then send TOF=STOP.Send gmail if not moving or fall is detected.",
                inputSchema={
                    "type": "object",
                    "properties": {},
                    "required" : []
                }
            )
        ]
    
    async def handle_tool(self, name: str, arguments: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Handle healthcare tool requests"""
        
        if name == "walk_reminder_audio":
            return await self.walk_reminder_audio()
        elif name == "close_reminder_audio":
            return await self.close_reminder_audio() 
        elif name == "medicine_reminder_audio":
            return await self.medicine_reminder_audio()
        elif name =="tof_detector_run_once":
            payload = await self.tof_detector_run_once()
            return [{
                "type": "text",
                "text": json.dumps(payload, ensure_ascii=False, indent=2)
            }]
            # return await self.tof_detector_run_once()
        # elif name == "tof_sensor_walk":
        #     return await self.tof_sensor_walk()
        # elif name == "tof_sensor_close":
        #     return await self.tof_sensor_close()
        # elif name == "tof_sensor_not_moving_alert":
        #     return await self.tof_sensor_not_moving_alert(arguments)
        else:
            raise ValueError(f"Unknown tool: {name}")

    
    async def walk_reminder_audio(self) ->  List[Dict[str, Any]]:
        """Send walk reminder voice command"""
        try:
            # Send AUDIO=WALK command to device using connection_module
            result = await self.connection_module.send_command("AUDIO=WALK")
            
            if result.get("status") == "success":
                device_response_text = result.get("response", "No device response content.")
                return [{
                    "type" :"text",
                    "text" :f"Walk reminder sent successfully. Device response: {device_response_text}"
                }]
            else:
                error_detail = result.get("error", "Unknown error occurred.")
                return [{
                    "type" :"text", 
                    "text" :f"Failed to send walk reminder: {error_detail}. Full result: {result}"
                }]
            
        except Exception as e:
            return [{
                "type": "text", 
                "text": f"An unexpected error occurred while sending walk reminder: {str(e)}"
            }]
    
    
    async def close_reminder_audio(self) ->  List[Dict[str, Any]]:
        """Send close/turn off reminder voice command"""
        try:
            # Send AUDIO=CLOSE command to device using connection_module
            result = await self.connection_module.send_command("AUDIO=CLOSE")
            
            if result.get("status") == "success":
                device_response_text = result.get("response", "No device response content.")
                return [{
                    "type": "text",
                    "text": f"Close reminder sent successfully. Device response: {device_response_text}"
                }]
            else:
                error_detail = result.get("error", "Unknown error occurred.")
                return [{
                    "type": "text",
                    "text": f"Failed to send close reminder: {error_detail}. Full result: {result}"
                }]
            
        except Exception as e:
            return [{
                "type":"text",
                "text": f"An unexpected error occurred while sending close reminder: {str(e)}"
            }]
    
    
    async def medicine_reminder_audio(self) -> List[Dict[str, Any]]: #List[TextContent]:
        """Send medicine reminder voice command"""
        try:
            # Send AUDIO=MEDICINE command to device using connection_module
            result = await self.connection_module.send_command("AUDIO=MEDICINE")
            
            if result.get("status") == "success":
                device_response_text = result.get("response", "No device response content.")
                return [{
                    "type": "text",
                    "text": f"Medicine reminder sent successfully. Device response: {device_response_text}"
                }]
            else:
                error_detail = result.get("error", "Unknown error occurred.")
                return [{
                    "type" : "text",
                    "text" : f"Failed to send medicine reminder: {error_detail}. Full result: {result}"
                }]
            
        except Exception as e:
            return [{
                "type" : "text",
                "text" : f"An unexpected error occurred while sending medicine reminder: {str(e)}"
            }]

    async def tof_detector_run_once(self) -> List[Dict[str, Any]]:
        """Start ToF monitoring for 60 seconds (serial only). Triggers actions at most once per event."""
        
        if getattr(self.conn, "tcp_socket", None):
            return [{"type": "text", "text": "Tof monitoring only supported via serial connection."}]

        sp = getattr(self.conn, "serial_port", None)
        if not sp or not getattr(sp, "is_open", False):
            return [{"type": "text", "text": "Not connected to device via serial."}]

        # start TOF
        try:
            await self.connection_module.send_command("TOF=RUN")
        except Exception as e:
            return [{"type": "text", "text": f"Failed to start TOF: {e}"}]

        # detect 60 seconds
        start_time = asyncio.get_event_loop().time()
        try:
            try:
                sp.reset_input_buffer()
            except Exception:
                pass

            buffer = ""
            triggered = {"FALL": False, "NOT_MOVING": False, "SITTING": False, "EXIT": False}
            event_log: List[str]=[]

            while (asyncio.get_event_loop().time() - start_time) < 60.0:
                
                n = getattr(sp, "in_waiting", 0) or 0
                if n > 0:
                    try:
                        chunk = sp.read(n)
                        buffer += chunk.decode("utf-8", errors="ignore")
                    except Exception:
                        pass

            
                while True:
                    idx = buffer.find("\n")
                    if idx == -1:
                        break
                    line = buffer[:idx].strip()
                    buffer = buffer[idx + 1 :]

                    if not line:
                        continue

                    upper = line.upper()
                    elapsed= asyncio.get_event_loop().time() - start_time  
                    IGNORE_FIRST_SECS = 3.0 

                    
                    if elapsed < IGNORE_FIRST_SECS:
                        continue                  

                    if "EMERGENCY: FALL" in upper and not triggered["FALL"]:
                        triggered["FALL"] = True
                        event_log.append({
                            "type": "email_request",
                            "tool": "send_email",
                            "args": {
                                "to": ["__________________"], # Enter gmail address here
                                "subject": "ToF Alert : Fall detected",
                                "body": f"FALL detected by ToF sensor at {elapsed: .2f}s. " 
                            },
                            "at_seconds": round(elapsed, 2),
                            "reason": "emergency_fall"
                        })

                    if "EMERGENCY: NOT MOVING" in upper and not triggered["NOT_MOVING"]:
                        triggered["NOT_MOVING"] = True
                        event_log.append({
                            "type": "email_request",
                            "tool": "send_email",
                            "args": {
                                "to": ["__________________"], # Enter gmail address here
                                "subject": "ToF Alert: NOT MOVING",
                                "body": "User not moving for a long time."
                            },
                            "at_seconds": round(elapsed, 2),
                            "reason": "not_moving_threshold_reached"
                        })

                    if "SITTING" in upper and not triggered["SITTING"]:
                        triggered["SITTING"] = True
                        await self.connection_module.send_command("AUDIO=WALK")
                        event_log.append({
                            "type": "audio_action",
                            "command": "AUDIO=WALK",
                            "at_seconds": round(elapsed, 2),
                            "reason": "sitting_detected"
                        })

                    if (("EXIT接近門口" in line) or ("EXIT準備出門" in line) or ("EXIT" in upper)) and not triggered["EXIT"]:
                        triggered["EXIT"] = True
                        await self.connection_module.send_command("AUDIO=CLOSE")
                        event_log.append({
                            "type": "audio_action",
                            "command": "AUDIO=CLOSE",
                            "at_seconds": round(elapsed, 2),
                            "reason": "near_door_or_exit"
                        })

                await asyncio.sleep(0.05)


            monitor_secs = 60
            if event_log:
                summary = f"ToF monitoring completed after {monitor_secs} seconds."
            else:
                summary = f"ToF monitoring completed after {monitor_secs} seconds. No events were triggered."

            payload = {
                "module": "healthcare",
                "action": "tof_monitoring_result",
                "monitor_duration_seconds": monitor_secs,
                "events": event_log,   
                "notes": summary
            }

            
            return payload
                    
        except Exception as e:
            return {"error": f"ToF monitoring error: {e}"}

        finally:
            try:
                await self.connection_module.send_command("TOF=STOP")
                await asyncio.sleep(0.2)
                if sp and getattr(sp, "is_open", False):
                    try:
                        sp.reset_input_buffer()
                        sp.reset_output_buffer()
                    except Exception:
                        pass
            except Exception as e:
                # 只記錄，不拋出
                print(f"Failed to send TOF=STOP: {e}")
            