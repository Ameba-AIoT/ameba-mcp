# Ameba MCP Server

A Model Context Protocol (MCP) server for controlling Ameba IoT development boards. This server provides a unified interface for interacting with multiple Ameba product lines including Ameba Pro2, Ameba D, and Ameba Arduino.

## Features

### Supported Devices

| Device | Connection | WiFi | KVS Streaming | Snapshot |
|--------|------------|------|---------------|----------|
| Ameba Pro2 | ✅ Serial/TCP | ✅ | ✅ | ✅ |
| Ameba D | ✅ Serial/TCP | ✅ | ❌ | ❌ |
| Ameba Arduino | ✅ Serial/TCP | ✅ | ❌ | ❌ |

### Core Functionality

- **Dual Connection Support**: Connect via Serial (USB) or TCP/IP (Telnet)
- **WiFi Management**: Scan networks, connect, and check status
- **Snapshot Capture** (Pro2 only): Capture and download images via HTTP
- **KVS Streaming** (Pro2 only): AWS Kinesis Video Streams with object detection
- **Modular Architecture**: Load only the features supported by your device

## Prerequisites

- Python 3.10 or higher
- [UV](https://github.com/astral-sh/uv) package manager
- Ameba development board
- USB cable (for serial connection)
- Network connection (for TCP connection)

## Installation

### 1. Install UV on Windows

```bash
# On Windows
PowerShell 安裝
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
 
驗證安裝
uv --version
 
用uv安裝環境
cd D:\path\to\ameba-mcp
uv venv --python 3.10
.venv\Scripts\activate
uv pip install -e . (the dependencies is written in pyproject.toml)

```

### 2. Configuration for Claude Desktop

Add the following to your Claude Desktop configuration file:
Windows: %APPDATA%\Claude\claude_desktop_config.json

```json
{
  "mcpServers": {
    "ameba-pro2": {
      "command": "uv",
      "args": [
        "--directory",
        "C:\\path\\to\\ameba-mcp",
        "run",
        "ameba-mcp",
        "--product",
        "ameba-pro2"
      ]
    },
    "ameba-d": {
      "command": "uv",
      "args": [
        "--directory",
        "C:\\path\\to\\ameba-mcp",
        "run",
        "ameba-mcp",
        "--product",
        "ameba-d"
      ]
    }
  }
}

```

### 3. Project Structure

```bash
ameba-mcp/
├── README.md              # This file
├── LICENSE               # MIT license
├── pyproject.toml        # UV package configuration
├── .gitignore           # Git ignore rules
├── src/
│   └── ameba_mcp/
│       ├── __init__.py
└──       └── server.py    # Main server implementation

```

### 4. Development

Adding new features

1. Create a new module class inheriting from FeatureModule
2. Implement required methods: get_tools(), handle_tool(), module_name
3. Add module to product configuration in PRODUCT_CONFIGS
4. Update module loading in ModularAmebaServer._load_modules()


## API Reference

### Connection Module

Core functions for device connection management.

| Function | Description | Returns |
|----------|-------------|---------|
| `list_ports()` | List available serial ports | Dict with port list |
| `connect(port, baudrate=115200)` | Connect via serial | Connection status |
| `tcp_connect(host, port=23)` | Connect via TCP/Telnet | Connection status |
| `disconnect(connection_type="all")` | Close connections | Disconnect results |
| `connection_status()` | Check active connections | Status dict |
| `send_command(command, connection=None)` | Send AT command | Command response |

<details>
<summary>📘 Detailed Parameters</summary>

#### `connect(port, baudrate=115200)`
- **port** (str): Serial port name - "COM4" (Windows), "/dev/ttyUSB0" (Linux)
- **baudrate** (int): Communication speed - default 115200

#### `tcp_connect(host, port=23)`
- **host** (str): Device IP address - e.g., "192.168.0.102"
- **port** (int): TCP port - default 23 (Telnet)

#### `disconnect(connection_type="all")`
- **connection_type** (str): "serial", "tcp", or "all" - default "all"

#### `send_command(command, connection=None)`
- **command** (str): AT command to send
- **connection** (str|None): "serial", "tcp", or None for auto-detect

</details>

### WiFi Module

WiFi network management functions.

| Function | Description | Returns |
|----------|-------------|---------|
| `wifi_scan(connection=None)` | Scan for available networks | List of networks with RSSI |
| `wifi_connect(ssid, password)` | Connect to WiFi network | Connection result |
| `wifi_status(connection=None)` | Get current WiFi status | Status with IP, SSID, etc |

<details>
<summary>📘 Detailed Parameters</summary>

#### `wifi_scan(connection=None)`
- **connection** (str|None): Force "serial" or "tcp", None for auto-detect
- **Note**: TCP may truncate results with 60+ networks

#### `wifi_connect(ssid, password)`
- **ssid** (str): Network name to connect to
- **password** (str): Network password
- **Note**: Only works via serial connection

#### `wifi_status(connection=None)`
- **connection** (str|None): Force "serial" or "tcp", None for auto-detect

</details>

### Snapshot Module (Pro2 Only)

Image capture and download functions.

| Function | Description | Returns |
|----------|-------------|---------|
| `snapshot_capture(connection=None)` | Capture image on device | Capture status with filename |
| `snapshot_download(filename, device_ip, save_path)` | Download single image | Download status with path |
| `snapshot_download_all(device_ip, save_path, max_files)` | Download all images | List of downloaded files |

<details>
<summary>📘 Detailed Parameters</summary>

#### `snapshot_capture(connection=None)`
- **connection** (str|None): Force "serial" or "tcp", None for auto-detect
- **Returns**: Dict with filename and capture status

#### `snapshot_download(filename, device_ip, save_path="./downloads/")`
- **filename** (str): Image filename on device (e.g., "1.jpg")
- **device_ip** (str): Device IP address
- **save_path** (str): Local directory to save - default "./downloads/"

#### `snapshot_download_all(device_ip, save_path="./downloads/", max_files=100)`
- **device_ip** (str): Device IP address
- **save_path** (str): Local directory to save
- **max_files** (int): Maximum files to attempt - default 100

</details>

### KVS Module (Pro2 Only)

AWS Kinesis Video Streams with object detection.

| Function | Description | Returns |
|----------|-------------|---------|
| `kvs_set_objects(objects)` | Set objects to detect | Status with objects list |
| `kvs_reactivate()` | Reactivate with same objects | Reactivation status |
| `kvs_wait_for_start(timeout=180)` | Wait for recording to begin | Recording start status |
| `kvs_wait_for_completion(timeout=60)` | Wait for recording to end | Recording completion status |

<details>
<summary>📘 Detailed Parameters</summary>

#### `kvs_set_objects(objects)`
- **objects** (List[str]): COCO dataset objects - e.g., ["person", "car", "dog"]
- **Note**: Triggers 30-second recording when object detected

#### `kvs_reactivate()`
- No parameters - uses previously set objects
- **Note**: Use after recording completes to re-arm detection

#### `kvs_wait_for_start(timeout=180)`
- **timeout** (float): Maximum seconds to wait - default 180
- **Note**: Returns immediately when recording starts

#### `kvs_wait_for_completion(timeout=60)`
- **timeout** (float): Maximum seconds to wait - default 60
- **Note**: Returns immediately when recording completes

</details>

