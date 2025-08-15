### How to run Snapshot FW on Pro2

User can follow the instructions in https://github.com/Ameba-AIoT/ameba-rtos-pro2?tab=readme-ov-file to build and flash image into pro2

```bash
# Please change the code in component/media/mmfv2/module_httpfs.c
define FAST_MP4    1 --> define FAST_MP4    0
define FAST_MP4_WITHOUT_FILE 1 --> define FAST_MP4_WITHOUT_FILE 0

# Please change the code in project/realtek_amebapro2_v0_example/src/mmfv2_video_example/video_example_media_framework.c
//mmf2_video_example_v1_init(); # Comment this example
mmf2_video_example_v1_shapshot_httpfs_init(); # Uncomment this example

# httpfs endpoints, snapshot is saved in sd card, user can access the snapshot file through http server
http://192.168.xxx.xxx/image_get.jpg?filename=x.jpg # Pro2 IP: 192.168.xxx.xxx, filename=0.jpg (1.jpg etc.)

# Compile and make
cmake .. -G "Unix Makefiles" -DCMAKE_TOOLCHAIN_FILE=../toolchain.cmake -DVIDEO_EXAMPLE=ON
cmake --build . --target flash -j4

# Flash Image
.\uartfwburn.exe -p COMX -f ..\project\realtek_amebapro2_v0_example\GCC-RELEASE\build\flash_ntz.bin -b 2000000 -n pro2 -U
```

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