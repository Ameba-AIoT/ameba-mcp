# RTK Gravitation / R-Mesh MCP Server

This is a Work-in-Progress!

This is a MCP server that visualizes the mesh configuration of R-Mesh devices currently running on the network

As R-Mesh is a fully automatic protocol, this server only provides read capabilities

## Configuration

Install the prerequisite libraries by running `python3 -m pip install -r requirements.txt`

Before usage, please modify `config.yaml` and place the MAC address of your AP under `ap_mac_list`. This will set up the root node of the Mesh graph

Note: This will not affect the operation of the R-Mesh, it will only affect the visualization of the mesh

```yaml
basic:
  ap_mac_list:
  - 00:11:22:33:44:55
```

### RTK Host Transport mode

Modify the following lines in server.py

```py
# Pick your MCP server implementation by uncommenting the desired import line
#from fastmcp import FastMCP as MCPServerProvider
from rtktool_server import MCPServer as MCPServerProvider
```

### STDIO Transport mode

Modify the following lines in server.py

```py
#mcp.run(transport="streamable-http")
mcp.run(transport="stdio")
```

### HTTP Transport mode

Modify the following lines in server.py

```py
mcp.run(transport="streamable-http")
#mcp.run(transport="stdio")
```

Start the server by running the following command:

```
python3 /path/to/wifi-gravitation-rmesh-mcp-server/server.py
```

### Claude Desktop Setup
Add to your `claude_desktop_config.json`:

#### If using STDIO Transport

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

#### If using HTTP Transport

Note: Please ensure that the server is started before starting Claude!

```json
{
  "mcpServers": {
    "gravitation-rmesh": {
      "command": "npx",
      "args": [
        "mcp-remote",
        "http://localhost:8000/mcp"
      ]
    },
  }
}
```

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

### Demonstration Firmware

Demonstration firmware has been provided for chipsets that support R-Mesh
- AmebaDplus
- AmebaGreen2

Please use the appropriate profile and follow the chipset's relevant Application Notes to flash the firmware for testing

After that, simply connect the boards to a common AP using `AT+WLCONN` ATCMD.

IMPORTANT: If attempting to use DPlus and Green2 chips interoperably with R-Mesh on 6 GHz band AP, please perform the following step. This step is not required if the AP is on 2.4G!

1. Disconnect from the AP with `AT+WLDISCONN`
2. Only on AmebaGreen2, use the following command `AT+WLDBG=wl_mode 4`
3. Reconnect to the AP with `AT+WLCONN`

To simulate a node switch, you may introduce attenuation to one of the nodes by e.g grabbing the antenna with your hand and releasing.

After that, check the reconfigured topology by using any of the listed prompts

On each of the firmware, HTTPD web server is enabled. You may use this to test the connectivity from a PC connected to the same AP, where the target node is behind 1 or more R-Mesh nodes.

#### Provided Debug Commands
- `AT+WLDBG=wtn nodename <name>`

Set a user-defined name for this node. Currently for demonstration purposes only and not part of the RTK R-Mesh spec!

- `AT+WLDBG=wtn get_nodename`

Display the node name, if any

- `AT+WLDBG=wtn fix_father <0/1> <00:11:22:33:44:55>`

Force this node to connect to a fixed parent R-Mesh node. Set the first argument to '0' to disable this feature

- `AT+WLDBG=wtn get_fix_father`

Display the forced father node's mac address, if set. Will not display if `fix_father` is set to '0'

### With Claude Desktop
Example Prompts:
- "List all nodes in my mesh network"
- "List the mesh topology of my network"
- "Display the mesh topology of my network"
- "Show me more information of the node with mac = 00:11:22:33:44:55"
- "Show me more information of the node with index 1"

### Testing use - HTTP Transport
This MCP Server supports the use of Postman to debug over Streamable-HTTP.

Simply connect Postman to this server by creating a new MCP workspace and enter the URL in: `http://localhost:8000/mcp`

### Testing use - STDIO
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
