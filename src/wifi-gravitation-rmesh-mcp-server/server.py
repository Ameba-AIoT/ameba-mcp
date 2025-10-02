#!/usr/bin/env python3
"""
MCP (Model Context Protocol) Server Skeleton
Implements JSON-RPC 2.0 communication protocol
"""

import asyncio
from mcpserver import MCPServer, Tool, Resource, Prompt
#from fastmcp import FastMCP
from abc import ABC, abstractmethod
from typing import Dict, Any, List
from gravitation.utils import *
from gravitation_nogui import GravitationServer
#import wat

# Example usage and server initialization
class ExampleMCPServer(MCPServer):
    """Example MCP Server implementation"""
    gravitation = None
    
    def __init__(self, gravitation):
        super().__init__("gravitation-rmesh-mcp-server", "1.0.0")
        self.gravitation = gravitation

        # Register example tools
        self.register_tool(Tool(
            name="echo",
            description="Echo back the input text",
            inputSchema={
                "type": "object",
                "properties": {
                    "text": {
                        "type": "string",
                        "description": "Text to echo back"
                    }
                },
                "required": ["text"]
            }
        ))

        # Register R-Mesh Tools
        self.register_tool(Tool(
            name="rmesh_list_nodes",
            description="List all stations participating in this R-MESH. This tool does not show the relationships between nodes.",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ))

        self.register_tool(Tool(
            name="rmesh_get_node_info",
            description="Get the detailed information of a specific R-MESH node by its node index or MAC address",
            inputSchema={
                "type": "object",
                "properties": {
                    "identifier": {
                        "type": "string",
                        "description": "Node index (integer as string) or MAC address (format: XX:XX:XX:XX:XX:XX)"
                    }
                },
                "required": []
            }
        ))

        self.register_tool(Tool(
            name="rmesh_list_relations",
            description="List relationships between R-MESH nodes, such as each node and its parent node. Root nodes are always connected to the Access Point. The Access Point itself is considered to be master node",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ))

        # Register example resources
        # self.register_resource(Resource(
        #     uri="example://hello",
        #     name="Hello Resource",
        #     description="A simple hello world resource",
        #     mimeType="text/plain"
        # ))
        
        # Register example prompts
        # self.register_prompt(Prompt(
        #     name="greeting",
        #     description="Generate a greeting message",
        #     arguments=[
        #         {
        #             "name": "name",
        #             "description": "Name to greet",
        #             "required": True
        #         }
        #     ]
        # ))
    
    async def _execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """Override tool execution"""
        # if tool_name == "echo":
        #     return arguments.get("text", "")
        match tool_name:
            case "echo":
                return arguments.get("text", "")
            case "rmesh_list_nodes":
                return [
                    {
                        "node_name": node.node_name,
                        "last_online": node.last_report_timestamp
                    }
                    for node in gravitation.nodes.values()
                ]
            case "rmesh_list_relations":
                relations = []
                for node in self.gravitation.nodes.values():
                    #father_mac = node.father_node.mac if node.father_node else None
                    if node.father_node is not None:
                        parent_rssi = "N/A" # not found 
                        for entry in node.scan_list:
                            if entry['mac_last_byte'] == node.father_mac.split(":")[-1]:
                                parent_rssi = entry['score']
                                break
                    else:
                        parent_rssi = "N/A"
                    
                    relations.append({
                        "node_index": node.id,
                        "node_mac": node.mac,
                        "parent": node.father_node.node_name if node.father_node else None,
                        "rssi_to_parent": parent_rssi,
                        "children": [child.node_name for child in node.children],
                    })
                return relations
            case "rmesh_get_node_info":
                identifier = arguments.get("identifier", "")
                if identifier:
                    # Check if identifier is an integer index
                    if identifier.isdigit():
                        index = int(identifier)
                        node = self.gravitation.nodes.get(index)
                        wat(node)
                        if node:
                            return node.__dict__
                        else:
                            return {"error": f"No node found with index {index}"}
                    else:
                        # Assume identifier is a MAC address
                        for node in self.gravitation.nodes.values():
                            if node.mac.lower() == identifier.lower():
                                return node.__dict__
                        return {"error": f"No node found with MAC address {identifier}"}
        return await super()._execute_tool(tool_name, arguments)
    
    # async def _read_resource(self, uri: str) -> str:
    #     """Override resource reading"""
    #     if uri == "example://hello":
    #         return "Hello, World! This is an example resource."
    #     return await super()._read_resource(uri)
    
    # async def _get_prompt(self, prompt_name: str, arguments: Dict[str, Any]) -> List[Dict[str, Any]]:
    #     """Override prompt generation"""
    #     if prompt_name == "greeting":
    #         name = arguments.get("name", "World")
    #         return [
    #             {
    #                 "role": "user",
    #                 "content": {
    #                     "type": "text",
    #                     "text": f"Please generate a friendly greeting for {name}."
    #                 }
    #             }
    #         ]
    #     return await super()._get_prompt(prompt_name, arguments)

# mcp = FastMCP("Gravitation R-Mesh MCP Server")

# @mcp.tool
# def rmesh_list_nodes() -> List[str]:
#     """List all stations participating in this R-MESH. This tool does not show the relationships between nodes"""
#     return [
#         {
#             "node_name": node.node_name,
#             "last_online": node.last_report_timestamp
#         }
#         for node in gravitation.nodes.values()
#     ]

# @mcp.tool
# def rmesh_get_node_info(identifier: str) -> Dict[str, Any]:
#     """Get the detailed information of a specific R-MESH node by its index or MAC address"""
#     if identifier:
#         # Check if identifier is an integer index
#         if identifier.isdigit():
#             index = int(identifier)
#             node = gravitation.nodes.get(index)
#             wat(node)
#             if node:
#                 return node.__dict__
#             else:
#                 return {"error": f"No node found with index {index}"}
#         else:
#             # Assume identifier is a MAC address
#             for node in gravitation.nodes.values():
#                 if node.mac.lower() == identifier.lower():
#                     return node.__dict__
#             return {"error": f"No node found with MAC address {identifier}"}
#     return {"error": "Identifier is required"}

# @mcp.tool
# def rmesh_list_relations() -> List[Dict[str, Any]]:
#     """List relationships between R-MESH nodes, such as each node and its parent node"""
#     relations = []
#     for node in gravitation.nodes.values():
#         #father_mac = node.father_node.mac if node.father_node else None
#         if node.father_node is not None:
#             #parent_rssi = node.scan_list[]
#             parent_rssi = node.scan_list[node.father_mac.split(":")[-1]].score
#         else:
#             parent_rssi = "N/A"
#         relations.append({
#             "node_index": node.id,
#             "node_mac": node.mac,
#             "parent": node.father_node.node_name if node.father_node else None,
#             "rssi_to_parent": parent_rssi,
#             "children": [child.node_name for child in node.children],
#         })
#     return relations

# Server startup
if __name__ == "__main__":
    for interface in get_interfaces():
        if interface == "Wi-Fi" or interface.startswith("wl"):
            chosen_iface = interface
            break
    gravitation = GravitationServer(chosen_iface=chosen_iface)
    #mcp.run(transport="stdio")
    try:
        server = ExampleMCPServer(gravitation=gravitation)
        asyncio.run(server.run())
    except KeyboardInterrupt:
        print("Server stopped by user")
        os._exit(0)