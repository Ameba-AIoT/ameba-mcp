"""
Modular Ameba MCP Server Architecture
Supports multiple Ameba product lines with selective feature registration
"""

import asyncio
import json
from typing import Any, Dict, List, Optional, Protocol
from abc import ABC, abstractmethod
import serial
import serial.tools.list_ports
import socket
from datetime import datetime
from mcp.server.models import InitializationOptions
from mcp.server import NotificationOptions, Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool

from .modules import *

# Product configurations
PRODUCT_CONFIGS = {
    "ameba-pro2": {
        "name": "Ameba Pro2",
        "modules": ["connection", "wifi", "kvs", "snapshot"]
    },
    "ameba-d": {
        "name": "Ameba D",
        "modules": ["connection", "wifi", "hems"]
    },
    "ameba-arduino": {
        "name": "Ameba Arduino",
        "modules": ["connection", "wifi"]
    }
}

class ModularAmebaServer:
    """Main server class that manages modules based on product configuration"""
    
    def __init__(self, product: str = "ameba-pro2"):
        if product not in PRODUCT_CONFIGS:
            raise ValueError(f"Unknown product: {product}. Available: {list(PRODUCT_CONFIGS.keys())}")
        
        self.product = product
        self.config = PRODUCT_CONFIGS[product]
        self.connection_manager = ConnectionManager()
        self.modules: Dict[str, FeatureModule] = {}
        
        # Initialize MCP server with product name
        self.server = Server(f"{product}-mcp")
        
        # Load modules based on configuration
        self._load_modules()
        self.setup_handlers()
    
    def _load_modules(self):
        """Load modules based on product configuration"""
        # Connection module is always loaded first
        if "connection" in self.config["modules"]:
            self.modules["connection"] = ConnectionModule(self.connection_manager)
        
        # Load other modules that depend on connection
        connection_module = self.modules.get("connection")
        
        for module_name in self.config["modules"]:
            if module_name == "connection":
                continue  # Already loaded
            elif module_name == "wifi":
                self.modules["wifi"] = WiFiModule(self.connection_manager, connection_module)
            elif module_name == "kvs":
                self.modules["kvs"] = KVSModule(self.connection_manager, connection_module)
            elif module_name == "snapshot":
                self.modules["snapshot"] = SnapshotModule(self.connection_manager, connection_module)
            elif module_name == "hems":
                self.modules["hems"] = HEMSModule(self.connection_manager, connection_module)
    
    def setup_handlers(self):
        @self.server.list_tools()
        async def handle_list_tools() -> List[Tool]:
            tools = []
            for module in self.modules.values():
                tools.extend(module.get_tools())
            return tools
        
        @self.server.call_tool()
        async def handle_call_tool(name: str, arguments: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
            try:
                # Find which module handles this tool
                for module in self.modules.values():
                    tool_names = [tool.name for tool in module.get_tools()]
                    if name in tool_names:
                        result = await module.handle_tool(name, arguments)
                        return [{"type": "text", "text": json.dumps(result, indent=2)}]
                
                raise ValueError(f"Unknown tool: {name}")
                
            except Exception as e:
                return [{"type": "text", "text": f"Error: {str(e)}"}]
    
    async def run(self):
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name=f"{self.product}-mcp",
                    server_version="1.0.0",
                    capabilities=self.server.get_capabilities(
                        notification_options=NotificationOptions(),
                        experimental_capabilities={},
                    ),
                ),
            )


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Modular Ameba MCP Server')
    parser.add_argument('--product', type=str, default='ameba-pro2',
                        choices=list(PRODUCT_CONFIGS.keys()),
                        help='Ameba product line to use')
    
    args = parser.parse_args()
    
    print(f"Starting {args.product} MCP Server...")
    print(f"Loaded modules: {PRODUCT_CONFIGS[args.product]['modules']}")
    
    server = ModularAmebaServer(product=args.product)
    asyncio.run(server.run())


if __name__ == "__main__":
    main()