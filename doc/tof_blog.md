Realize AI agent applications in healthcare scenarios with Realtek AmebaPro2
===
Introduction of Agentic AI
---
It is designed to achieve long-term goals and perform iterative problem solving. Unlike traditional AI, which requires direct human guidance to react to specific tasks, agentic AI systems act as proactive agents that are self-directed, dynamically interacting with the environment, models, or humans. They can set their own sub-goals and use tools to execute complex, end-to-end processes.  

Both AI agents and generative AI models such as ChatGPT exhibit creativity. However, they differ in many ways. For instance, AI agent systems make decisions rather than simply generating content. They do not rely on human prompts but autonomously work toward specific goals, such as increasing sales or enhancing customer satisfaction. In addition, they can independently update databases and initiate processes.  

Advances in LLMs, enhanced memory architectures, and the development of external APIs are driving the rise of agentic AI systems. This trend suggests that agentic AI will evolve from experimental prototypes into essential business infrastructure, unlocking new opportunities for productivity and innovation. For example, agentic AI is being used to streamline workflows across industries—from customer service to software development—reducing repetitive manual tasks. With greater interoperability, agentic AI can also coordinate across multiple platforms, enabling businesses to build complex multi-agent systems that collaborate efficiently.

MCP (Model Context Protocol)
---
MCP plays a critical role in advancing agentic AI by providing a standardized and secure way for agents to connect with external tools, data sources, and enterprise systems. By unifying access through a common protocol, MCP not only reduces integration complexity but also ensures stronger security and governance, preventing agents from exceeding their permissions. In addition, MCP enhances interoperability, enabling multiple agents to collaborate more effectively across diverse environments.

Walkthrough
---
This section outlines the steps for building and running healthcare scenarios.

### Prerequisites
- Hardware: Realtek AmebaPro2, SparkFun Qwiic ToF Imager-VL53L5CX, headphones, USB cable (for serial connection).
- Software: AmebaPro2 SDK (ameba-rtos-pro2), ameba-mcp, gmail-mcp, Claude.
- Internet connection: Required to download SDKs and upload them onto AmebaPro2 (for TCP connection).
- Knowledge: Basic familiarity with working in a Linux environment.

### Set up the environment

1. Refer to the following link: https://github.com/Ameba-AIoT/ameba-rtos-pro2.  
Download the SDK and check the Application Notes in the README to set up the GCC build environment on Linux.
2. Refer to the following link: https://github.com/Ameba-AIoT/ameba-mcp/tree/main.  
Download it and follow the Installation Guide in README.
3. Refer to the following link: https://github.com/GongRzhe/Gmail-MCP-Server to install Gmail MCP.

### Configure the sample that implements the healthcare scenarios in SDK

```bash
#Please change the code ameba-rtos-pro2-main/project/realtek_amebapro2_v0_example/src/mmf2_video_example/video_example_media_framework.c
//mmf2_video_example_v1_init(); #Comment this example
mmf2_video_example_snapshot_httpfs_audio_with_tof_init(); #Uncomment this example

#Please enter the Gmail address where you want to receive messages in ameba-mcp-main/src/modules/healthcare_module.py.
"to": ["__________________"] # Enter gmail address here
```
If MCP is installed successfully, the server will be visible running in Claude Desktop.

### Compile and build

```bash
#Compile and make
cmake .. -G "Unix Makefiles" -DCMAKE_TOOLCHAIN_FILE=../toolchain.cmake -DVIDEO_EXAMPLE=ON
cmake --build . --target flash -j4

# Flash Image
.\uartfwburn.exe -p COMX -f ..\project\realtek_amebapro2_v0_example\GCC-RELEASE\build\flash_ntz.bin -b 2000000 -n pro2 -U
```

### Verify the function on Claude

Open Claude and send the system instruction to your project
<p>System instruction:</p>
<pre><code>Whenever the Ameba MCP server returns JSON containing an “email_request” event. Please automatically call the tool specified in”tool” using the provided “args” as parameters. Do not ask for confirmation.</code></pre>
When the above process is complete, ask Claude to connect to AmebaPro2. You can then simulate the healthcare scenarios by entering specific commands. These scenarios will be introduced in the next section.

Healthcare scenarios
---
### Audio reminders with snapshot
Check how many pills the pillbox contains. If the number of pills is different from the expected amount, return medicine_reminder, which plays an audio message reminding the user to take the medicine.

![1_scenario](images/ameba-mcp_scenario.png)


Here's a practical example:
![eg1](images/1eg1.png)
![eg2](images/1eg2.png)

### Tof sensor detection
- Emergency Gmail messages:  
Ask Claude to start the ToF sensor detection. If the ToF sensor detects a “fall” or “no movement,” a Gmail alert will be sent to the Gmail address specified in the healthcare module.

![2_scenario](images/mcp2.png)

- Audio reminders with ToF sensor:  
Ask Claude to start the ToF sensor detection. If the ToF sensor detects “sitting” or “close to the door,” the walk_reminder audio and the close_reminder audio will be played, respectively.

![3_scenario](images/mcp3.png)

Here's a practical example:

![eg1](images/3eg1.png)
![eg2](images/3eg2.png)
![eg3](images/3eg3.png)

Then you'll recieve a Gmail message:

![eg4](images/3eg4.png)

Technical deep dive
---
The way to identify “falling,” “not moving,” “sitting,” or “close to door” using ToF sensor detection is through the following algorithm — Center of Mass Tracking.

The purpose of this approach is to track a person’s location and observe their dynamic movements, making center-of-mass tracking an effective choice. Assume that the ToF sensor is located on the ceiling of a living room. By calculating the center of mass, we can approximate the object’s overall position.

In practice, the overhead space is divided into an 8×8 two-dimensional grid with 64 coordinate points, each corresponding to the distance measured by the sensor. A weighted average of these distances is then computed, where shorter distances are given greater weight. The resulting coordinates (cx, cy) represent the center of mass, which indicates the object’s position.

Based on (cx, cy) and the associated distance values, different scenarios can be identified, including prolonged sitting, remaining still, approaching a specific area, or falling.

Algorithm

![algorithm](images/algorithm.png)

- Falling: The depth corresponding to the centroid increases sharply within one second.
- Not moving: The hotspot centroid does not change over a period of time.
- Prolonged sitting: The centroid variation stays below a certain threshold over an extended period.
- Approaching doorway: Set the doorway at the bottom-left corner of the room in the top view, with the condition: cx > cx_threshold and cy > cy_threshold.
For more detail of the algorithm, please refer to mmf2_video_example_snapshot_httpfs_audio_with_tof_init()

Discussion and Conclusion
---
There may be some challenges with this algorithm. One challenge is that if furniture in the room is taller than a person, the heat map may be influenced by these objects, preventing the hotspot from being centered on the human body. This can be addressed by collecting long-term ToF data from the static environment to build a background model and remove it, thereby filtering out furniture or ignoring regions that are too close.

Another issue is that a stationary center of mass may also occur when a person is sleeping; in this case, detecting normal breathing can help distinguish between the two situations. Finally, a person standing near the doorway might be mistakenly interpreted as leaving the room. To resolve this, additional sensors can be placed on the doorknob or outside the door to confirm whether it has actually been opened.

A ToF sensor can play a valuable role in both healthcare and smart home scenarios. In elderly care, it can estimate a person’s center of gravity to enable fall detection, provide reminders for prolonged sitting, and track daily activity levels. In smart home and safety applications, the same sensor can be integrated with IoT systems to automatically shut off appliances or gas for accident prevention, while also functioning as part of an anti-intrusion alarm system.

In the follow-up procedure, I will refine the algorithm and invest more time in collecting sensing data for machine learning, which will improve detection accuracy. In addition, I will create a trend chart of center-of-gravity changes between “not moving” and “sitting” to better visualize the differences.
