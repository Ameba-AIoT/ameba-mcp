### HEMS Module (D Plus Only)

Home Energy Management System functions for solar inverters and grid management.

| Function | Description | Returns |
|----------|-------------|---------|
| `hems_identify()` | Get device chipset identification | Device name |
| `hems_start_logging(device)` | Start logging to filesystem | Status with timestamp |
| `hems_stop_logging(device)` | Stop logging | Status with timestamp |
| `hems_download_logs(device, start_date, end_date)` | Download logs | List of log entries |
| `hems_get_alerts(device)` | Get system alerts | List of alerts |
| `hems_get_control_plan(device)` | Get current control plan | Current plan name |
| `hems_get_available_control_plans(device)` | List available plans | List of plan names |
| `hems_set_control_plan(device, control_plan)` | Set control plan | Status |
| `hems_get_statistics(device)` | Get system statistics | Grid and energy data |

<details>
<summary>📘 Detailed Parameters</summary>

#### `hems_identify()`
- **Returns**: Dict with device chipset name and firmware version

#### `hems_start_logging(device)`
- **device** (str): Device identification name - unique identifier for the HEMS unit
- **Returns**: Dict with status and start timestamp

#### `hems_stop_logging(device)`
- **device** (str): Device identification name
- **Returns**: Dict with status and stop timestamp

#### `hems_download_logs(device, start_date="", end_date="")`
- **device** (str): Device identification name
- **start_date** (str): Start date for log retrieval - format "YYYY-MM-DD" or "YYYY-MM-DD HH:MM:SS", empty for first entry
- **end_date** (str): End date for log retrieval - format "YYYY-MM-DD" or "YYYY-MM-DD HH:MM:SS", empty for last entry
- **Returns**: List of log entries with timestamps and events

#### `hems_get_alerts(device)`
- **device** (str): Device identification name
- **Returns**: List of system alerts requiring user attention

#### `hems_get_control_plan(device)`
- **device** (str): Device identification name
- **Returns**: Dict with current control plan name and settings

#### `hems_get_available_control_plans(device)`
- **device** (str): Device identification name
- **Returns**: List of available control plan names

#### `hems_set_control_plan(device, control_plan)`
- **device** (str): Device identification name
- **control_plan** (str): Control plan name - "At Home", "Out of Home", "Night Mode", "Quick Heating", "Quick Cooling"
- **Returns**: Dict with status and confirmation

#### `hems_get_statistics(device)`
- **device** (str): Device identification name
- **Returns**: Dict with grid voltage, power data, solar output, battery status, and energy metrics

</details>