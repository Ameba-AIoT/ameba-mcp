# WiFi Diagnostic MCP Wrapper

## Introduction / Features

A Model Context Protocol (MCP) server that provides WiFi diagnostic tools for IoT devices through MQTT communication.

- **Device Status Monitoring** - Get current WiFi status from IoT devices
- **Signal Strength Analysis** - Monitor RSSI values for connection quality assessment
- **WiFi Event Monitoring** - Retrieve WiFi events history and diagnostics
- **WiFi Connection Status Tracking** - Detailed state transition monitoring with timestamp history
- **Network Performance Testing** - iPerf throughput testing and ping latency measurement
- **Video Streaming Assessment** - Evaluate network suitability for real-time video transmission
- **MQTT Integration** - Communicate with devices through MQTT broker
- **Dual Compatibility** - Works with both Claude Desktop and HTTP wrapper systems

### WiFi Connection States

The system tracks complete WiFi connection lifecycle with detailed state transitions:

| State | Code | Description |
|-------|------|-------------|
| UNKNOWN | 0 | Unknown state |
| STARTING | 1 | WiFi connection starting |
| SCANNING | 2 | Scanning for access points |
| SCANN_DONE | 3 | Scan completed |
| AUTHENTICATING | 4 | Authenticating with AP |
| AUTHENTICATED | 5 | Authentication successful |
| ASSOCIATING | 6 | Associating with AP |
| ASSOCIATED | 7 | Association successful |
| 4WAY_HANDSHAKING | 8 | Performing 4-way handshake |
| 4WAY_HANDSHAKE_DONE | 9 | 4-way handshake completed |
| SUCCESS | 10 | Successfully connected to WiFi |
| FAIL | 11 | Connection failed |
| DISCONNECT | 12 | Disconnected from WiFi |
| REJECT_CONNECTION_SECURITY | 13 | Rejected due to security settings |
| SCANNING_EXTERNAL | 14 | External scanning in progress |
| REJECT_UNSUPPORT_SECURITY | 15 | Unsupported security type |
| TIMEOUT | 16 | Connection timeout |
| STATUS_CODE_FAIL | 17 | Failed with status code error |

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

### HTTP Wrapper Setup with audio server system
For integration with MCP Wrapper systems:

1. **Integrate with mcp_wrapper configuration file** (`mcp_wrapper/config.json`):

```json
{
  "port": 8082,
  "host": "0.0.0.0",
  "timeout": 30,
  "max_body_size": 10485760,
  "servers": [
    {
      "name": "wifi_diagnostics",
      "command": "./examples/wifi-diagnostic-mcp-wrapper/wifi_diagnostic_server.py",
      "args": [],
      "description": "Python-based wifi diagnostics MCP server"
    }
  ]
}
```

## Available Tools

### Basic Diagnostic Tools

#### 1. get_device_status
Retrieves comprehensive WiFi status information from a device.

**Parameters:**
- `device_id` (string): IoT device identifier
- `timeout` (integer, optional): Response timeout in seconds (default: 30)

#### 2. get_device_rssi
Gets the current RSSI (signal strength) from a device.

**Parameters:**
- `device_id` (string): IoT device identifier
- `timeout` (integer, optional): Response timeout in seconds (default: 30)

#### 3. get_wifi_event_log
Retrieves WiFi event logs and diagnostic information.

**Parameters:**
- `device_id` (string): IoT device identifier
- `timeout` (integer, optional): Response timeout in seconds (default: 30)

#### 4. clear_wifi_event_log
Clears the WiFi event log on the IoT device.

**WARNING:** This is a destructive operation that will permanently delete all WiFi event history. Use this to reset the log or free up memory on the device.

**Parameters:**
- `device_id` (string): IoT device identifier
- `timeout` (integer, optional): Response timeout in seconds (default: 30)

#### 5. get_wifi_connection_status
Retrieves WiFi connection status transition history from IoT device.

Returns a complete log of WiFi state changes with timestamps, showing the connection process. Each entry shows status transitions (e.g., SCANNING → AUTHENTICATING → SUCCESS). Also includes parameter validation errors (e.g., wrong password, invalid SSID). Useful for diagnosing connection issues, understanding why connections fail, and analyzing connection patterns.

**Parameters:**
- `device_id` (string): IoT device identifier
- `timeout` (integer, optional): Response timeout in seconds (default: 30)


#### 6. clear_wifi_connection_status
Clears the WiFi connection status log on the IoT device.

**WARNING:** This is a destructive operation that will permanently delete all WiFi status history. Use this to reset the log or free up memory on the device.

**Parameters:**
- `device_id` (string): IoT device identifier
- `timeout` (integer, optional): Response timeout in seconds (default: 30)

### Network Performance Testing Tools

#### 7. run_iperf_tx_test
Measures device network upload throughput to evaluate WiFi performance and video transmission capability.

**Parameters:**
- `device_id` (string): IoT device identifier
- `server_ip` (string): iPerf server IP address
- `duration` (integer, optional): Test duration in seconds (default: 30)
- `interval` (integer, optional): Report interval in seconds (default: 1)
- `timeout` (integer, optional): Response timeout in seconds (default: duration + 60)

**Video Streaming Performance Criteria:**
- **< 5 Mbps**: ❌ Not suitable for video transmission
- **5-10 Mbps**: ⚠️ Basic quality video streaming
- **10-40 Mbps**: ✅ Good for video transmission
- **> 40 Mbps**: 🏆 Excellent performance

**Usage:**
```bash
# Start iPerf server on PC first
./iperf.exe -s -i 1

# Then ask LLM
"Please run iperf tx test for device dv1, server ip: 192.168.0.102, duration 15 sec, time interval 1 sec"
```

#### 8. get_tx_rate
Queries current WiFi transmission rate and MCS (Modulation and Coding Scheme) information.

**Parameters:**
- `device_id` (string): IoT device identifier
- `timeout` (integer, optional): Response timeout in seconds (default: 30)

#### 9. ping_test
Tests network connectivity quality and latency to evaluate real-time video streaming suitability.

**Parameters:**
- `device_id` (string): IoT device identifier
- `target_ip` (string): Target IP address (typically gateway or PC)
- `timeout` (integer, optional): Response timeout in seconds (default: 30)

**Latency Criteria for Video Streaming:**
- **< 50 ms**: ✅ Suitable for real-time video transmission
- **> 50 ms**: ⚠️ May affect real-time video quality

**Usage:**
```
"Please execute ping test for device dv1 with gateway"
```

### WiFi Management Tools

#### 10. connect_wifi
Connects device to a new WiFi network with specified SSID and password.

**Parameters:**
- `device_id` (string): IoT device identifier
- `ssid` (string): WiFi network SSID
- `password` (string): WiFi network password
- `timeout` (integer, optional): Response timeout in seconds (default: 30)

**Usage:**
```
"Please connect device dv1 to WiFi network 'MyNetwork' with password 'XXX'"
```


### Configuration Tools

### 11. configure_mqtt
Configures and connects to an MQTT broker.

**Parameters:**
- `broker` (string): MQTT broker hostname or IP address
- `port` (integer, optional): MQTT broker port (default: 1883)
- `username` (string, optional): MQTT username
- `password` (string, optional): MQTT password

### 12. mqtt_status
Checks the current MQTT connection status and configuration.

**Parameters:** None


## Usage Examples

### With Claude Desktop

**Basic Diagnostics:**
- "Check the WiFi status of device dv1"
- "What's the signal strength of dv1?"
- "I want to check if there are wifi events for device dv1"
- "Show me the wifi connection history of dv1"
- "Please check the detail connection information of device dv1"

**Network Performance Testing:**
- "Please run iperf tx test for device dv1, server ip: 192.168.0.102, duration 15 sec"
- "Please get the tx rate for device dv1"
- "Please execute ping test for device dv1 with gateway"


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
curl -X POST http://localhost:8082/ -H "Content-Type: application/json" -d '{"jsonrpc":"2.0","method":"tools/call","params":{"name":"get_wifi_event_log","arguments":{"device_id":"dv1"}},"id":4}'

# 7. Get WiFi Connection Status
curl -X POST http://localhost:8082/ -H "Content-Type: application/json" -d '{"jsonrpc":"2.0","method":"tools/call","params":{"name":"get_wifi_connection_status","arguments":{"device_id":"dv1"}},"id":5}'

# 8. Clear WiFi Connection Status
curl -X POST http://localhost:8082/ -H "Content-Type: application/json" -d '{"jsonrpc":"2.0","method":"tools/call","params":{"name":"clear_wifi_connection_status","arguments":{"device_id":"dv1"}},"id":6}'

# 9. Run iPerf TX Test
curl -X POST http://localhost:8082/ -H "Content-Type: application/json" -d '{"jsonrpc":"2.0","method":"tools/call","params":{"name":"run_iperf_tx_test","arguments":{"device_id":"dv1","server_ip":"192.168.0.102","duration":15}},"id":7}'

# 10. Get TX Rate
curl -X POST http://localhost:8082/ -H "Content-Type: application/json" -d '{"jsonrpc":"2.0","method":"tools/call","params":{"name":"get_tx_rate","arguments":{"device_id":"dv1"}},"id":8}'

# 11. Ping Test
curl -X POST http://localhost:8082/ -H "Content-Type: application/json" -d '{"jsonrpc":"2.0","method":"tools/call","params":{"name":"ping_test","arguments":{"device_id":"dv1","target_ip":"192.168.0.1"}},"id":9}'

# 12. Connect WiFi
curl -X POST http://localhost:8082/ -H "Content-Type: application/json" -d '{"jsonrpc":"2.0","method":"tools/call","params":{"name":"connect_wifi","arguments":{"device_id":"dv1","ssid":"MyNetwork","password":"12345678"}},"id":10}'

# 13. Get MQTT Status
curl -X POST http://localhost:8082/ -H "Content-Type: application/json" -d '{"jsonrpc":"2.0","method":"tools/call","params":{"name":"mqtt_status","arguments":{}},"id":11}'
```

## File Structure

```
wifi-diagnostic-mcp-wrapper/
├── wifi_diagnostic_server.py    # Main MCP server
├── mqtt_handler_sync.py         # MQTT communication handler
├── iot_tools_sync.py           # IoT diagnostic tools
├── requirements.txt            # Python dependencies
└── README.md                   
```

## MQTT Topic Structure

- **Command Topic**: `wifi_diagnostic/{team_prefix}/{device_id}/command`
- **Response Topic**: `wifi_diagnostic/{team_prefix}/{device_id}/response`

### Command/Response Flow

1. **MCP Server** sends command via MQTT:
```json
   {
     "request_id": "uuid",
     "command": "CONNECTINFO"
   }
```

2. **IoT Device** responds:
```json
   {
     "request_id": "uuid",
     "status": "success",
     "data": {
       "response": "Total status changes: 21\n..."
     }
   }
```


## Device-Side Implementation (Ameba Pro2)

### Status Logging Structure

```c
#define WIFI_STATUS_LOG_SIZE 50

typedef struct {
    uint32_t timestamp;      // System tick count
    uint8_t join_status;     // Current WiFi status (0-17)
    uint8_t last_status;     // Previous WiFi status
    int8_t conn_time;        // Connection attempt counter
    uint8_t valid;           // Entry validity flag
    uint8_t error_type;      // Error type (0=none, 1=password, 2=ssid)
} wifi_status_log_entry_t;
```

### AT Commands (Device Side)

The device responds to the following AT commands:

#### Basic Diagnostic Commands
```
ATW?               # Get WiFi status
ATWR               # Get RSSI
WIFIEVENTLOG       # Get WiFi event log
WIFIEVENTLOG=CLEAR # Clear WiFi event log
CONNECTINFO        # Get connection status history
CONNECTINFO=CLEAR  # Clear connection status log
```

#### Network Testing Commands
```
ATWT=-c,<server_ip>,-t,<duration>,-i,<interval>  # iPerf TX test
ATWd=0                                             # Get TX rate
ATWI=<target_ip>                                   # Ping test
```

#### WiFi Management Commands
```
ATW0=<ssid>       # Set SSID
ATW1=<password>   # Set password
ATWC              # Connect to WiFi
```

**Response Example (CONNECTINFO):**
```
Total status changes: 21
Recent status changes:
Time: 325, Status: 0->1, ConnTime: -1
Time: 339, Status: 1->2, ConnTime: 0
Time: 2480, Status: 9->10, ConnTime: 0
Time: 12345, Error: PASSWORD_WRONG
```

#### Clear Status Log
```
CONNECTINFO=CLEAR
```

**Response:**
```
WiFi status log cleared
```

### Important Notes

- **Log Persistence**: The status log is stored in RAM and will be cleared on system reboot
- **Log Size**: Limited to WIFI_STATUS_LOG_SIZE most recent entries (circular buffer)
- **Error Detection**: Invalid SSID/password errors are caught before connection attempts

**Example Conversations:**
```
User: "Why did dv1 fail to connect?"
Claude: *calls get_wifi_connection_status* 
        "Device dv1 failed because it couldn't find the AP. 
         The log shows SCANNING → SCANN_DONE → FAIL pattern,
         which indicates the AP's wireless was disabled or 
         the device is out of range."

User: "Is device dv1 suitable for video streaming?"
Claude: *runs iperf and ping tests*
        "Device dv1 shows excellent video streaming conditions:
         - Throughput: 49.2 Mbps (well above 40 Mbps threshold)
         - Latency: 0-1ms (excellent, below 50ms threshold)
         - RSSI: -35 dBm (excellent signal)
         The device is optimal for high-quality real-time video transmission."
```

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

