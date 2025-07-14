# Ameba MCP Server

A Model Context Protocol (MCP) server for controlling Ameba IoT development boards. This server provides a unified interface for interacting with multiple Ameba product lines including Ameba Pro2 and Ameba D Plus.

## Features

### Supported Devices

| Device | Connection | WiFi | KVS Streaming | Snapshot | HEMS |
|--------|------------|------|---------------|----------|------|
| Ameba Pro2 | ✅ Serial/TCP | ✅ | ✅ | ✅ | ❌ |
| Ameba D Plus| ✅ Serial/TCP | ✅ | ❌ | ❌ | ✅ |


### Core Functionality

- **Dual Connection Support**: Connect via Serial (USB) or TCP/IP (Telnet)
- **WiFi Management**: Scan networks, connect, and check status
- **Snapshot Capture (Pro2 only)**: Capture and download images via HTTP
- **KVS Streaming (Pro2 only)**: AWS Kinesis Video Streams with object detection
- **HEMS Module (D Plus Only)**: Home Energy Management System functions for solar inverters and grid management.
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

Users can define product configurations and add modules specific to each product.

```python
PRODUCT_CONFIGS = {
    "ameba-pro2": {
        "name": "Ameba Pro2",
        "modules": ["connection", "wifi", "kvs", "snapshot"]
    },
    "ameba-d": {
        "name": "Ameba D",
        "modules": ["connection", "wifi", "hems"]
    }
}

```


### 3. Project Structure

```bash
ameba-mcp/
├── README.md              
├── api_docs/
│     ├── connection.md
│     ├── wifi.md    
│     ├── snapshot.md    
│     ├── kvs.md    
│     └── hems.md    
├── pyproject.toml        # UV package configuration
├── .gitignore            # Git ignore rules
├── src/
│   └── ameba_mcp/
│       ├── modules/      # Define each module
│            ├── __init__.py
│            ├── connection_manager.py 
│            ├── connection_module.py
│            ├── feature_module.py    
│            ├── hems_module.py      
│            ├── kvs_module.py      
│            ├── snapshot_module.py  
│            └── wifi_module.py   
│       ├── __init__.py
└──     └── server.py    # Pack each module into Ameba product server

```

### 4. Development

Adding new features

1. Create a new module class inheriting from FeatureModule
2. Implement required methods: get_tools(), handle_tool(), module_name
3. Add module to product configuration in PRODUCT_CONFIGS in server.py
4. Update module loading in ModularAmebaServer._load_modules()


## API Reference

### Connection Module

[Link to Connection Module](./api_docs/connection.md)

### WiFi Module

[Link to WiFi Module](./api_docs/wifi.md)

### Snapshot Module (Pro2 Only)

[Link to Snapshot Module](./api_docs/snapshot.md)

### KVS Module (Pro2 Only)

[Link to KVS Module](./api_docs/kvs.md)

### HEMS Module (D Plus Only)

[Link to HEMS Module](./api_docs/hems.md)

