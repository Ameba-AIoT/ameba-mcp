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

TODO