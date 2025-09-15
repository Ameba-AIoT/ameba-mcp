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
- **baudrate** (int): Communication speed - default 115200 (pro2), 1500000 for d-plus

#### `tcp_connect(host, port=23)`
- **host** (str): Device IP address - e.g., "192.168.0.102"
- **port** (int): TCP port - default 23 (Telnet)

#### `disconnect(connection_type="all")`
- **connection_type** (str): "serial", "tcp", or "all" - default "all"

#### `send_command(command, connection=None)`
- **command** (str): AT command to send
- **connection** (str|None): "serial", "tcp", or None for auto-detect

</details>