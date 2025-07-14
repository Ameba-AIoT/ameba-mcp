# Home Assistant Setup with Realtek Ameba + MCP

Home Assistant is an open-source solution to control and manage IoT home setups using a wide range of communication protocols, network protocols and vendor support

Realtek Ameba goes a step further and provides the necessary tooling to control Ameba Devices via AI using Model Context Protocol

This guide details the development environment that demonstrates Ameba Control from an AI (e.g Claude, other Local AI)

## Introduction

The overall scenario will consist of 3 devices on a local network, belonging to the same subnet

1) The AP/Router on 192.168.XXX.A (For purposes of this demo, assume that the Router has AI capabilities, provided by Claude AI)

2) The Ameba Device on 192.168.XXX.B

3) The Server, running both Home Assistant & MQTT Broker on 192.168.XXX.C

There are 3 parts to this demonstration, which are:
- Home Assistant
- MCP Server
- Ameba Device

The MQTT Control path is defined as the following:

Ameba Device (Target) <---MQTT---> MQTT Broker <---MQTT---> Home Assistant <---MCP---> Agentic AI

The diff file provided is to be applied on top of ameba-rtos-1.1 SDK, then build the project with: python build.py -a mqtt

## Prerequisites

Ubuntu Linux 22.04

Python 3.10

Docker & Docker-Compose

NodeJS latest

## Setup Instructions for Home Assistant

For this demonstration, Home Assistant Core over Docker will be used

1) Pull the docker image

sudo docker pull homeassistant/home-assistant

2) Start the docker image

docker run -d –-name=hass -v your_home_directory:/config –-net=host homeassistant/home-assistant

your_home_directory refers to a directory on your environment's disk, and /config will be the folder that is mapped into the container. 

3) Check whether docker is running

Using Firefox/Chrome on your environment, browse to http://localhost:8123. On first login, the user will be asked to create an account, any username/password is fine

## Setup Instructions for Mosquitto MQTT Broker

Setup instructions are based on: https://github.com/sukesh-ak/setup-mosquitto-with-docker

Follow the instructions on the link above. However for the following steps, there are some modifications

Step 3: Remove the line "listener 9001" as this demonstration currently does not support MQTT over Websockets

Step 5: Remove the line "- "9001:9001" #default mqtt port for websockets" as this demonstration currently does not support MQTT over Websockets

Step 5.1: Skip this step as the MQTT Server is running locally

After creating an MQTT account for the user, user may test the MQTT Broker by the following commands

Publisher/Sender:

mosquitto_pub -L mqtt://user:password@localhost/Your/MQTT/Topic -m "AT+STATE"

Subscriber/Receiver:

mosquitto_sub -v -L mqtt://user:password@localhost/Your/MQTT/Topic

Expected output:

"Your/MQTT/Topic AT+STATE"

### Install MQTT integration on Home Assistant

Browse to Settings > Devices & Integrations > Add Integration

Search "MQTT" and install "MQTT"

Fill in the MQTT Broker details above

## Setup Instructions for MCP Server

This demonstration uses Claude in place of a local Agentic AI to perform the reasoning tasks. 

In order for the Agentic AI to dispatch MQTT commands directly from HASS to the Ameba Device, a MCP Server with HASS connectivity should be deployed

The MCP Server does the following:

1) Receive tool use request from Agent AI

2) Call the HASS tool to send MQTT command

3) Inside the MCP Server, the HASS tool will interface with HASS via backend API (https://developers.home-assistant.io/docs/api/rest/) and call the mqtt send command

### Obtain the Long-lived Token from HASS

Please see https://community.home-assistant.io/t/how-to-get-long-lived-access-token/162159/5 for how to obtain your long-lived token. Remember to copy it and keep it secure, as it will only be shown once!

### Setup MCP Server

The MCP Server to be used is https://github.com/liorfranko/home-assistant-mcp

Follow the instructions to setup the MCP Server, then in claude_desktop_config.json apply the following:

    "homeassistant": {
      "command": "node",
      "args": ["D:\\mcp\\home-assistant-mcp\\dist"],
      "env": {
        "HA_URL": "http://YOUR_HOME_ASSISTANT_URL:8123",
        "HA_WEBSOCKET_URL": "ws://YOUR_HOME_ASSISTANT_URL:8123/api/websocket",
        "HA_TOKEN": "YOUR_LONG_LIVED_HASS_TOKEN"
      }
    }

After this, restart Claude, and observe that the homeassistant tools have appeared in the "Tools" window

## Demo Instructions

After setting up the environment and flashing the Ameba DPlus with the image, simply issue the prompt to Claude:

"publish the following message to the topic Ameba/DPlus/ATCMD/Request via Home Assistant: AT+STATE"

Claude will call the MCP tool to PUBLISH the required MQTT command "AT+STATE" to the Ameba DPlus on the topic "Ameba/DPlus/ATCMD/Request"

The Ameba DPlus device will send the output of "AT+STATE" AT Command over MQTT, on the topic "Ameba/DPlus/ATCMD/Response" for any SUBSCRIBErs