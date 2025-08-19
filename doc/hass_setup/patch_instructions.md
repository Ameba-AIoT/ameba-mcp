# Patch Instructions

## Ameba DPlus

Please apply the dplus_mqtt_with_atcmd.patch on top of commit https://github.com/Ameba-AIoT/ameba-rtos/commit/347af9133679eacb10b368010f9ce5e143ff1643

```
git clone https://github.com/Ameba-AIoT/ameba-rtos.git -b release/v1.1
git checkout 347af9133679eacb10b368010f9ce5e143ff1643
git apply dplus_mqtt_with_atcmd.patch
```

AT Commands added:

```
AT+MQTTCLIENT - Set Client ID
AT+MQTTUSER - Set Username to connect to broker
AT+MQTTPASS - Set Password to connect to broker
AT+MQTTADDR - Set Broker Address 
AT+MQTTPORT - Set Broker Port
AT+MQTTPUBTOPIC - Set ATCMD Publish Topic: This is where the output of ATCMD will be written to
AT+MQTTSUBTOPIC - Set ATCMD Subscribe Topic: This is where the ATCMD will be received from the sender, e.g AT+STATE
AT+MQTTSTATUS - Return configuration status
```

After applying, please use menuconfig to enable the option 

CONFIG APPLICATION > [*] Enable ATCMD over MQTT

## Ameba Pro2

The FW code is in https://github.com/Ameba-AIoT/ameba-rtos-pro2

```bash
# Compile and make
cmake .. -G "Unix Makefiles" -DCMAKE_TOOLCHAIN_FILE=../toolchain.cmake -DEXAMPLE=mqtt -DUSE_ATCMD_MQTT=ON
cmake --build . --target flash -j4

# Flash Image
.\uartfwburn.exe -p COMX -f ..\project\realtek_amebapro2_v0_example\GCC-RELEASE\build\flash_ntz.bin -b 2000000 -n pro2 -U
```

AT Commands added:

```
MQTTCLIENT=<CLIENT_ID> - Set Client ID
MQTTUSER=<Username> - Set Username to connect to broker
MQTTPASS=<Password> - Set Password to connect to broker
MQTTADDR=<Address> - Set Broker Address 
MQTTPORT=<Port> - Set Broker Port, default 1883
MQTTPUB=<Pub Topic> - Set ATCMD Publish Topic: This is where the output of ATCMD will be published to
MQTTSUB=<Sub Topic> - Set ATCMD Subscribe Topic: This is where the ATCMD will be received from the sender, e.g ATW?
MQTTSTATUS - Return configuration status
```

User can also set the mqtt_config in component/example/mqtt/example_mqtt.c, by setting the information in advanced, user don't need to use ATcmd to set mqtt information
```c
static mqtt_config_t mqtt_config = {
	.clientID = "",
	.username = "",
	.password = "",
	.address = "",
	.pub_topic = "",
	.sub_topic = "",
	.port = 1883,
	.configured = 0
};
```
