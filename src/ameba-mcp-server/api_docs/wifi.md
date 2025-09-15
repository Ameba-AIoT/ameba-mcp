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