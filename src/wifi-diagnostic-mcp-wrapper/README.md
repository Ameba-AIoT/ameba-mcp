# WiFi Diagnostic MCP Wrapper

A Model Context Protocol (MCP) server that provides WiFi diagnostic tools for IoT devices through MQTT communication.

## Features

- **Device Status Monitoring** - Get comprehensive WiFi status from IoT devices
- **Signal Strength Analysis** - Monitor RSSI values for connection quality assessment
- **Connection Logging** - Retrieve WiFi connection history and diagnostics
- **MQTT Integration** - Communicate with devices through MQTT broker
- **Dual Compatibility** - Works with both Claude Desktop and HTTP wrapper systems

## Architecture

### Claude Desktop (STDIO)
```
Claude Desktop ←STDIO→ WiFi Diagnostic MCP Server ←→ MQTT Broker ←→ IoT Devices
```
### MQTT Wrapper (HTTP)
```
MCP host ←HTTP→ MCP Wrapper ←STDIO→ WiFi Diagnostic MCP Server ←→ MQTT Broker ←→ IoT Devices
```


## Configuration

### Environment Variables
Set these environment variables for MQTT configuration:

```bash
export MQTT_BROKER=localhost
export MQTT_PORT=1883
export MQTT_USERNAME=
export MQTT_PASSWORD=
export TEAM_PREFIX=iot
```

### Claude Desktop Setup
Add to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "wifi-diagnostic": {
      "command": "uv",
      "args": [
        "--directory",
        "/path/to/wifi-diagnostic-mcp-wrapper",
        "run",
        "wifi_diagnostic_server.py"
      ]
    }
  }
}
```

### HTTP Wrapper Setup
For integration with MCP Wrapper systems:

1. **Create configuration file** (`wifi-diagnostic.json`):
   ```json
   {
     "port": 8082,
     "host": "localhost",
     "command": "uv",
     "args": ["--directory", "/path/to/wifi-diagnostic-mcp-wrapper", "run", "wifi_diagnostic_server.py"],
     "timeout": 30,
     "max_body_size": 10485760
   }
   ```

2. **Start MCP Wrapper**:
   ```bash
   mcp_wrapper -config wifi_diagnostic.json
   ```

## Available Tools

### 1. get_device_status
Retrieves comprehensive WiFi status information from a device.

**Parameters:**
- `device_id` (string): IoT device identifier
- `timeout` (integer, optional): Response timeout in seconds (default: 30)

### 2. get_device_rssi
Gets the current RSSI (signal strength) from a device.

**Parameters:**
- `device_id` (string): IoT device identifier
- `timeout` (integer, optional): Response timeout in seconds (default: 30)

### 3. get_wifi_log
Retrieves WiFi connection logs and diagnostic information.

**Parameters:**
- `device_id` (string): IoT device identifier
- `timeout` (integer, optional): Response timeout in seconds (default: 30)

### 4. configure_mqtt
Configures and connects to an MQTT broker.

**Parameters:**
- `broker` (string): MQTT broker hostname or IP address
- `port` (integer, optional): MQTT broker port (default: 1883)
- `username` (string, optional): MQTT username
- `password` (string, optional): MQTT password

### 5. mqtt_status
Checks the current MQTT connection status and configuration.

**Parameters:** None

## Usage Examples

### With Claude Desktop
Simply ask Claude natural language questions:
- "Check the WiFi status of device dv1"
- "What's the signal strength of dv1?"
- "Show me the WiFi logs for device dv1"

### With HTTP API (MCP Wrapper)
```bash
# List available tools
# 1. Health Check
curl -X GET http://localhost:8082/health

# 2. Initialize Server
curl -X POST http://localhost:8082/ -H "Content-Type: application/json" -d '{"jsonrpc":"2.0","method":"initialize","params":{},"id":0}'

# 3. List Available Tools
curl -X POST http://localhost:8082/ -H "Content-Type: application/json" -d '{"jsonrpc":"2.0","method":"tools/list","id":1}'

# 4. Test Device Status Query
curl -X POST http://localhost:8082/ -H "Content-Type: application/json" -d '{"jsonrpc":"2.0","method":"tools/call","params":{"name":"get_device_status","arguments":{"device_id":"dv1"}},"id":2}'

# 5. Test RSSI Query
curl -X POST http://localhost:8082/ -H "Content-Type: application/json" -d '{"jsonrpc":"2.0","method":"tools/call","params":{"name":"get_device_rssi","arguments":{"device_id":"dv1"}},"id":3}'

# 6. Test WiFi Log Query
curl -X POST http://localhost:8082/ -H "Content-Type: application/json" -d '{"jsonrpc":"2.0","method":"tools/call","params":{"name":"get_wifi_log","arguments":{"device_id":"dv1"}},"id":4}'

# 7. Test MQTT Status Query
curl -X POST http://localhost:8082/ -H "Content-Type: application/json" -d '{"jsonrpc":"2.0","method":"tools/call","params":{"name":"mqtt_status","arguments":{}},"id":5}'
```

## File Structure

```
wifi-diagnostic-mcp-wrapper/
├── wifi_diagnostic_server.py    # Main MCP server
├── mqtt_handler_sync.py         # MQTT communication handler
├── iot_tools_sync.py           # IoT diagnostic tools
├── requirements.txt            # Python dependencies
├── wifi-diagnostic.json        # MCP Wrapper configuration
└── README.md                   
```

## MQTT Topic Structure

- **Command Topic**: `wifi_diagnostic/{team_prefix}/{device_id}/command`
- **Response Topic**: `wifi_diagnostic/{team_prefix}/{device_id}/response`

## Troubleshooting

### MQTT Connection Issues
1. Verify broker address and port
2. Check username/password credentials
3. Ensure network connectivity to MQTT broker
4. Use `mqtt_status` tool to check current configuration

### Device Communication Issues
1. Confirm device is online and connected to MQTT
2. Verify device_id is correct
3. Check device is subscribed to command topic
4. Increase timeout value for slow devices

### MCP Integration Issues
1. Restart Claude Desktop after configuration changes
2. Check file paths in configuration
3. Verify all dependencies are installed
4. Check logs for detailed error messages

