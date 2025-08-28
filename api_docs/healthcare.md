### How to run Healthcare on Pro2

User can follow the instructions in https://github.com/Ameba-AIoT/ameba-rtos-pro2?tab=readme-ov-file to build and flash image into pro2

```bash
#Please change the code ameba-rtos-pro2-main/project/realtek_amebapro2_v0_example/src/mmf2_video_example/video_example_media_framework.c
//mmf2_video_example_v1_init(); #Comment this example
mmf2_video_example_snapshot_httpfs_audio_with_tof_init(); #Uncomment this example


#Compile and make
cmake .. -G "Unix Makefiles" -DCMAKE_TOOLCHAIN_FILE=../toolchain.cmake -DVIDEO_EXAMPLE=ON
cmake --build . --target flash -j4

# Flash Image
.\uartfwburn.exe -p COMX -f ..\project\realtek_amebapro2_v0_example\GCC-RELEASE\build\flash_ntz.bin -b 2000000 -n pro2 -U
```

### How to use Tof sensor

Please refer to the link for the ToF sensor specifications and usage instructions.
https://www.sparkfun.com/sparkfun-qwiic-tof-imager-vl53l5cx.html

Pin connection:
| Tof sensor | Pro2 |
|----------|-------------|
| GND | J18 |
| 3V3 | J17 | 
| SDA | GPIOE6 | 
| SCL | GPIOE5 | 


### Gmail MCP
Please refer to https://github.com/GongRzhe/Gmail-MCP-Server

```bash
# Please enter the Gmail address where you want to receive messages in ameba-mcp-main/src/modules/healthcare_module.py
"to": ["__________________"] # Enter gmail address here
```
In this workflow, you should provide a system instruction before issuing the command.
<p>System instruction:</p>
<pre><code>Whenever the Ameba MCP server returns JSON containing an “email_request” event. Please automatically call the tool specified in”tool” using the provided “args” as parameters. Do not ask for confirmation.</code></pre>



### Healthcare Module (Pro2 Only)

Play the audio reminders and detect using Tof sensors.

| Function | Description | Returns |
|----------|-------------|---------|
| `walk_reminder_audio()` | play walk reminder | walk reminder audio 3 times |
| `close_reminder_audio()` | play close reminder | close reminder audio 3 times |
| `medicine_reminder_audio()` | play medicine reminder | medicine reminder audio 3 times |
| `tof_detector_run_once()` | detects 60sec. | trigger actions(play audios or send gmails) |

The ways to trigger these functions are in the discription from ameba-mcp-main/src/modules/healthcare_module.py

<details>
<summary> details for tof detection </summary>

#### `What happens when tof sensor detect someone is...`
- **Not moving**: Send gmail messages
- **sitting**: Play walk reminder audio
- **Fall down**: Send gmail messages
- **Near the door**: Play close reminder audio
