# RTK Gravitation / R-Mesh MCP Server

This is a Work-in-Progress!

This is a stdio MCP server that visualizes the mesh configuration of R-Mesh devices currently running on the network

As R-Mesh is a fully automatic protocol, this server only provides read capabilities

## Configuration

### Claude Desktop Setup
Add to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "gravitation-rmesh": {
      "command": "python3",
      "args": [
        "/path/to/wifi-gravitation-rmesh-mcp-server/server.py",
      ]
    }
  }
}
```

### HTTP Transport
WIP!

## Available Tools

### 1. rmesh_list_nodes
List all stations participating in this R-MESH. This tool does not show the relationships between nodes.

** Parameters:**
None

### 2. rmesh_list_relations
List relationships between R-MESH nodes, such as each node and its parent node. Root nodes are always connected to the Access Point. Station nodes are nodes whose parent does not share the MAC address of the Access Point. The Access Point itself is considered to be master node

** Parameters:**
None

### 3. rmesh_get_node_info
Get the detailed information of a specific R-MESH node by its node index or MAC address

** Parameters:**
- `identifier` (string): Node Index (1-255) or MAC address

## Usage Examples

### With Claude Desktop
Example Prompts:
- "List all nodes in my mesh network"
- "List the mesh topology of my network"
- "Display the mesh topology of my network"
- "Show me more information of the node with mac = 00:11:22:33:44:55"
- "Show me more information of the node with index 1"

### Testing use only (STDIO)
Run with python3 ./server.py, then paste these JSONRPC in to trigger the specific endpoints

- Run `rmesh_list_nodes`
```
{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"rmesh_list_nodes","arguments":{}}}
```

- Run `rmesh_list_relations`
```
{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"rmesh_list_relations","arguments":{}}}
```

- Run `rmesh_get_node_info`
```
{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"rmesh_get_node_info","arguments":{"identifier": "1"}}}
```
