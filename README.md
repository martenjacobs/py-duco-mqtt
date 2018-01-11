# Python Ducobox MQTT bridge

This package allows for communication between a Ducobox ventilation unit and an MQTT service. It was tested using [Home Assistant](http://www.home-assistant.io)'s built-in MQTT broker.

## Supported Ducobox communication protocols
This package supports the use of a different communication protocol for reading of parameters and control of the unit.
Currently, only direct serial communication is supported for reading, and only GPIO is supported for control, but implementing further types is pretty easy. I'm open to pull requests.

# Connector cable
There is a 5-pins serial connector on the Ducobox main board. You can create a simple cable that allows for direct communication from a Raspberry Pi or a serial UART. The port is talked about in-depth in [this forum thread](https://gathering.tweakers.net/forum/list_messages/1724875) (in Dutch). Apparently the port uses 3.3V TTL, but is 5V tolerant. The pins are (from right to left):
1. TX (from Duco)
2. RX (to Duco)
3. Unknown
4. GND
5. Vcc (3.3V)

To build a cable, I used the following parts:
- 1x JST PHR-5 (connector)
- 5x JST SPH-002T-P0.5S (crimp socket)
- 1x MOLEX 50-57-9405 (connector)
- 5x MOLEX 16-02-0107 (crimp pin)
- ca 30 cm 3M 3365-10 (ribbon-kabel)

# Control from GPIO
Control of the box is not possible through the serial protocol (this was confirmed to me by Duco). So, to get around this, I added a two-channel relay board that emulates a manual 3-position switch (section 5A in the [Quick Start Guide](https://www.duco.eu/Wes/CDN/1/Attachments/Quick-Start-DucoBox-Silent-17xxxx_636506783259119017.pdf)). This allows setting the box to modes CNT1, CNT2 and CNT3. I wired it up like this:

![Wire diagram](wire-diagram.png?raw=true)

L1 goes to the power input that also goes to the main board of the ducobox, and L2 and L3 go to the 3-position switch ports, as found in the QSG. The relays are controlled by GPIO 17 and 27. With the board I'm using, the relays are active-low (they're flipped when the GPIO is driven low).

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
    "baudrate": 115200
  },
  "control": {
      "type": "gpio",
      "active_low": true,
      "states": {
          "CNT1" : {
              "17": 0,
              "27": 0
          },
          "CNT2" : {
              "17": 1,
              "27": 0
          },
          "CNT3" : {
              "17": 0,
              "27": 1
          }
      }
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

- value/duco _=> service on-line status_
- value/duco/network/1/stat _=> state_
- value/duco/network/1/info _=> info_
- value/duco/network/4/stts _=> stts_
- value/duco/network/1/%dbt _=> dbt (%)_
- value/duco/network/1/trgt _=> target value (???)_
- value/duco/network/1/cntdwn _=> countdown (s)_
- value/duco/temp _=> temperature (ºC)_
- value/duco/co2 _=> CO2 (ppm)_
- value/duco/humi _=> Humidity (%)_
- value/duco/fan/Filtered _=> filtered fan speed (rpm)_
- value/duco/fan/Actual _=> actual fan speed (rpm)_

> If you've changed the pub_topic_namespace value in the configuration, replace `value/duco` with your configured value.
> __TODO:__ Improve description of all topics

### Subscription topics
By default, the service listens to messages from the following MQTT topics:

- set/duco/state _=> state_

> If you've changed the sub_topic_namespace value in the configuration, replace `set/duco` with your configured value.
> __TODO:__ Improve description of all topics

# Home Assistant
The following configuration can be used in Home Assistant:
```yaml
sensor duco:
  - platform: mqtt
    state_topic: "value/duco"
    name: "DUCO service on-line"
  - platform: mqtt
    state_topic: "value/duco/network/1/stat"
    name: "DUCO state"
  - platform: mqtt
    state_topic: "value/duco/network/1/info"
    name: "DUCO info"
  - platform: mqtt
    state_topic: "value/duco/network/4/stts"
    name: "DUCO stts"
  - platform: mqtt
    state_topic: "value/duco/network/1/%dbt"
    name: "DUCO dbt"
    unit_of_measurement: '%'
  - platform: mqtt
    state_topic: "value/duco/network/1/trgt"
    name: "DUCO target value"
    unit_of_measurement: '???'
  - platform: mqtt
    state_topic: "value/duco/network/1/cntdwn"
    name: "DUCO countdown"
    unit_of_measurement: 's'
  - platform: mqtt
    state_topic: "value/duco/temp"
    name: "DUCO temperature"
    unit_of_measurement: 'ºC'
  - platform: mqtt
    state_topic: "value/duco/co2"
    name: "DUCO CO2"
    unit_of_measurement: 'ppm'
  - platform: mqtt
    state_topic: "value/duco/humi"
    name: "DUCO Humidity"
    unit_of_measurement: '%'
  - platform: mqtt
    state_topic: "value/duco/fan/Filtered"
    name: "DUCO filtered fan speed"
    unit_of_measurement: 'rpm'
  - platform: mqtt
    state_topic: "value/duco/fan/Actual"
    name: "DUCO actual fan speed"
    unit_of_measurement: 'rpm'

fan mqtt:
  - platform: mqtt
    name: "Ducobox"
    command_topic: "set/duco"
    state_topic: "value/duco"
    payload_on: "online"
    payload_off: "offline"
    speed_state_topic: "value/duco/network/1/stat"
    speed_command_topic: "set/duco/state"
    qos: 0
    payload_low_speed: "CNT1"
    payload_medium_speed: "CNT2"
    payload_high_speed: "CNT3"
    speeds:
      - low
      - medium
      - high
```
