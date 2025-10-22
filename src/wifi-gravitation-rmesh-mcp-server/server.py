#!/usr/bin/env python3
"""
MCP (Model Context Protocol) Server Skeleton
Implements JSON-RPC 2.0 communication protocol
"""

# Pick your MCP server implementation by uncommenting the desired import line
#from fastmcp import FastMCP as MCPServerProvider
from rtktool_server import MCPServer as MCPServerProvider

from typing import Dict, Any, List
from gravitation.utils import *
from gravitation_nogui import GravitationServer

mcp = MCPServerProvider("Gravitation R-Mesh MCP Server")

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

def get_relations() -> List[Dict[str, Any]]:
    """Helper function to get relations for internal use"""
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

@mcp.tool
def rmesh_list_relations() -> List[Dict[str, Any]]:
    """List relationships between R-MESH nodes, such as each node and its parent node"""
    return get_relations()

@mcp.tool
def rmesh_display_graph() -> str:
    """
    Generates a Mermaid flowchart from R-MESH network data. The caller should create a new artifact to display the graph
    Node 0 is always the root node.

    This tool should not be chained with other tools. It must only be called standalone
    """

    def generate_mermaid_graph(data):
        mermaid_lines = ["graph TD"]
        # Create a mapping of MAC addresses to node info
        mac_to_info = {}
        for node in data:
            mac = node['node_mac']
            name = node['node_name'] if node['node_name'] else f"Node_{node['node_index']}"
            # Clean name for Mermaid (remove spaces and special chars)
            clean_name = name.replace(" ", "_").replace("-", "_")
            mac_to_info[mac] = {
                'index': node['node_index'],
                'name': name,
                'clean_name': clean_name,
                'mac': mac
            }
        
        # Add node definitions with styling
        for node in data:
            mac = node['node_mac']
            info = mac_to_info[mac]
            node_id = f"node_{info['index']}"
            
            # Create label with name and MAC
            label = f"{info['name']}<br/>{info['mac']}"
            
            # Style root node differently
            if info['index'] == 0:
                mermaid_lines.append(f'    {node_id}["{label}"]')
                mermaid_lines.append(f'    style {node_id} fill:#ff6b6b,stroke:#2c3e50,stroke-width:3px,color:#000')
            else:
                mermaid_lines.append(f'    {node_id}["{label}"]')
                mermaid_lines.append(f'    style {node_id} fill:#4ecdc4,stroke:#2c3e50,stroke-width:3px,color:#000')
        
        # Add blank line for readability
        mermaid_lines.append("")
        
        # Add edges (connections) with RSSI labels
        for node in data:
            if node['parent'] is not None:
                parent_mac = node['parent']
                child_mac = node['node_mac']
                
                # Find parent and child node indices
                parent_info = mac_to_info[parent_mac]
                child_info = mac_to_info[child_mac]
                
                parent_id = f"node_{parent_info['index']}"
                child_id = f"node_{child_info['index']}"
                
                # Add edge with RSSI label
                rssi = node.get('rssi_to_parent', 'N/A')
                if rssi != 'N/A':
                    mermaid_lines.append(f'    {parent_id} -->|"RSSI: {rssi} dBm"| {child_id}')
                else:
                    mermaid_lines.append(f'    {parent_id} --> {child_id}')

        return "\n".join(mermaid_lines)

    return generate_mermaid_graph(get_relations())

# Server startup
if __name__ == "__main__":
    for interface in get_interfaces():
        if interface == "Wi-Fi" or interface.startswith("wl"):
            chosen_iface = interface
            break
    gravitation = GravitationServer(chosen_iface=chosen_iface)

    try:
        # these transport only apply for FastMCP, rtktool_server will default to stdio transport!
        mcp.run(transport="streamable-http")
        #mcp.run(transport="stdio")
    except KeyboardInterrupt:
        print("Server stopped by user", file=sys.stderr)
        os._exit(0)
