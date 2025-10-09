#!/usr/bin/env python3
"""
MCP (Model Context Protocol) Server Skeleton
Implements JSON-RPC 2.0 communication protocol
"""

from fastmcp import FastMCP
from typing import Dict, Any, List
from gravitation.utils import *
from gravitation_nogui import GravitationServer

mcp = FastMCP("Gravitation R-Mesh MCP Server")

@mcp.tool
def rmesh_list_nodes() -> List[Any]:
    """List all stations participating in this R-MESH. This tool does not show the relationships between nodes"""
    return [
        {
            "node_index": node.id,
            "node_ip": node.ip,
            "node_sta_type": node.node_sta_type,
            "node_mac": node.mac,
            "node_name": node.node_name,
            "last_online": node.last_report_timestamp
        }
        for node in gravitation.nodes.values()
    ]

@mcp.tool
def rmesh_get_node_info(identifier: str) -> Dict[str, Any]:
    """Get the detailed information of a specific R-MESH node by its index or MAC address"""
    if identifier:
        # Check if identifier is an integer index
        if identifier.isdigit():
            index = int(identifier)
            node = gravitation.nodes.get(index)
            #wat(node)
            if node:
                return node.__dict__
            else:
                return {"error": f"No node found with index {index}"}
        else:
            # Assume identifier is a MAC address
            for node in gravitation.nodes.values():
                if node.mac.lower() == identifier.lower():
                    return node.__dict__
            return {"error": f"No node found with MAC address {identifier}"}
    return {"error": "Identifier is required"}

@mcp.tool
def rmesh_list_relations() -> List[Dict[str, Any]]:
    """List relationships between R-MESH nodes, such as each node and its parent node"""
    relations = []
    for node in gravitation.nodes.values():
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
            "node_name": node.node_name,
            "node_mac": node.mac,
            "parent": node.father_node.mac if node.father_node else None,
            "rssi_to_parent": parent_rssi,
            "children": [{
                "node_index": child.id,
                "node_name": child.node_name,
                "node_mac": child.mac
            } for child in node.children],
        })
    return relations

# Server startup
if __name__ == "__main__":
    for interface in get_interfaces():
        if interface == "Wi-Fi" or interface.startswith("wl"):
            chosen_iface = interface
            break
    gravitation = GravitationServer(chosen_iface=chosen_iface)
    
    try:
        #mcp.run(transport="streamable-http")
        mcp.run(transport="stdio")
    except KeyboardInterrupt:
        print("Server stopped by user")
        os._exit(0)