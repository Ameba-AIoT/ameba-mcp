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