# Python Ducobox MQTT bridge

This package allows for communication between a Ducobox ventilation unit and an MQTT service. It was tested using [Home Assistant](http://www.home-assistant.io)'s built-in MQTT broker.

## Supported Ducobox communication protocols
Currently, only direct serial communication is supported, but implementing further types is pretty easy. I'm open to pull requests.

# Control
At the moment, there is no way to control the box from the service. Setting of the power level will be added in the near future. It will be implemented using GPIO and a relay board.

## Supported MQTT brokers
The MQTT client used is [paho](https://www.eclipse.org/paho/). It's one of the most widely-used MQTT clients for Python, so it should work on most brokers. If you're having problems with a certain type, please open an issue or send me a pull request with a fix.

## Configuration
The configuration for the bridge is located in config.json.

### Example configuration
```json
{
  "duco" : {
    "type": "serial",
    "device": "/dev/serial0",
    "baudrate": 115200,
    "control": "gpio"
  },
  "mqtt" : {
      "client_id": "duco",
      "host": "127.0.0.1",
      "port": 1883,
      "keepalive": 60,
      "bind_address": "",
      "username": null,
      "password": null,
      "qos": 0,
      "pub_topic_namespace": "value/duco",
      "sub_topic_namespace": "set/duco",
      "retain": true
  }
}
```

## Installation
To install this script as a daemon, run the following commands (on a Debian-based distribution):

1. Install dependencies:
   ```bash
   sudo apt install python python-serial
   ```
2. Create a new folder, for example:
   ```bash
   sudo mkdir -p /usr/lib/py-duco-mqtt
   cd /usr/lib/py-duco-mqtt
   ```
3. Clone this repository into the current directory:
   ```bash
   sudo git clone https://github.com/martenjacobs/py-duco-mqtt.git .
   ```
4. Change `config.json` with your favorite text editor
5. Copy the service file to the systemd directory. If you used a different folder name than `/usr/lib/py-duco-mqtt` you will need to change the `WorkingDirectory` in the file first.
   ```bash
   sudo cp ./py-duco-mqtt.service /etc/systemd/system/
   ```
6. Enable the service so it starts up on boot:
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable py-duco-mqtt.service
   ```
7. Start up the service
   ```bash
   sudo systemctl start py-duco-mqtt.service
   ```
8. View the log to see if everything works
   ```bash
   journalctl -u py-duco-mqtt.service -f
   ```

## Topics

### Publish topics
By default, the service publishes messages to the following MQTT topics:

> __TODO:__ make the list

> If you've changed the pub_topic_namespace value in the configuration, replace `value/duco` with your configured value.
> __TODO:__ Add description of all topics

### Subscription topics
By default, the service listens to messages from the following MQTT topics:

> __TODO:__ make the list

> If you've changed the pub_topic_namespace value in the configuration, replace `value/duco` with your configured value.
> __TODO:__ Add description of all topics
