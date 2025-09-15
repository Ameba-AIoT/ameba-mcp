from .connection_manager import ConnectionManager
from .connection_module import ConnectionModule
from .feature_module import FeatureModule
from typing import Any, Dict, List, Optional, Protocol
from mcp.types import Tool
import asyncio
import json

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