import serial
import re
import json
import sys
import logging
import paho.mqtt.client as mqtt
from datetime import datetime
from time import sleep
from threading import Thread

from utils import pathify, changes
# TODO: clean this up
from commands import *

# Set up logging
logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

_running = None
settings = None
mqtt_client = None
conn = None
ctrl = None
topic_namespace = None

def init():
    global _running, settings, mqtt_client, conn, topic_namespace, ctrl
    # Default settings
    settings = {
        "duco" : {
            "type": "serial",
            "device": "/dev/serial0",
            "baudrate": 115200
        },
        "control": {
            "type": "gpio",
            "active_low": True,
            "states": {}
        },
        "mqtt" : {
            "client_id": "duco",
            "host": "127.0.0.1",
            "port": 1883,
            "keepalive": 60,
            "bind_address": "",
            "username": None,
            "password": None,
            "qos": 0,
            "pub_topic_namespace": "value/duco",
            "sub_topic_namespace": "set/duco",
            "retain": False
        }
    }
    # Update default settings from the settings file
    with open('config.json') as f:
        settings.update(json.load(f))

    # Set the namespace of the mqtt messages from the settings
    topic_namespace=settings['mqtt']['pub_topic_namespace']

    log.info("Initializing MQTT")

    # Set up paho-mqtt
    mqtt_client = mqtt.Client(
        client_id=settings['mqtt']['client_id'])
    mqtt_client.on_connect = on_mqtt_connect
    mqtt_client.on_message = on_mqtt_message

    if settings['mqtt']['username']:
        mqtt_client.username_pw_set(
            settings['mqtt']['username'],
            settings['mqtt']['password'])

    # The will makes sure the device registers as offline when the connection
    # is lost
    mqtt_client.will_set(
        topic=topic_namespace,
        payload="offline",
        qos=settings['mqtt']['qos'],
        retain=True)

    # Let's not wait for the connection, as it may not succeed if we're not
    # connected to the network or anything. Such is the beauty of MQTT
    mqtt_client.connect_async(
        host=settings['mqtt']['host'],
        port=settings['mqtt']['port'],
        keepalive=settings['mqtt']['keepalive'],
        bind_address=settings['mqtt']['bind_address'])
    mqtt_client.loop_start()

    log.info("Initializing Duco")

    duco_type = {
        "serial" : lambda: __import__('ducobox_serial',
                      globals(), locals(), ['DucoboxSerialClient'], 0) \
                      .DucoboxSerialClient,
    }[settings['duco']['type']]()

    conn = duco_type(settings['duco'])


    control_types = {
        "gpio" : lambda: __import__('control_gpio',
                      globals(), locals(), ['DucoboxGpioControl'], 0) \
                      .DucoboxGpioControl,
    }
    my_type = settings['control']['type']
    if my_type in control_types:
        control_type = control_types[my_type]()
        ctrl = control_type(settings['control'])

    _running = True


def main():
    init()
    # TODO: bleeegh
    global _running

    conn.open()
    if ctrl != None:
        ctrl.open()

    _worker = Thread(target=worker)
    _worker.start()
    try:
        while _running:
            sleep(60)
    except:
        log.warn("Handling exception")
        _running = False
        _worker.join()

    conn.close()
    if ctrl != None:
        ctrl.close()


def publish(topic, payload):
    mqtt_client.publish(
        topic=topic,
        payload=payload,
        qos=settings['mqtt']['qos'],
        retain=settings['mqtt']['retain'])


def worker():
    # TODO: clean this up
    global _running
    _running = True
    log.info("Reading initial data")
    while _running:
        try:
            netw = get_network_data(conn)
            for (t, v) in pathify(netw, "{}/network".format(topic_namespace)):
                if v is not None:
                    publish(t, v)
            fan  = get_fan_speed(conn)
            for (t, v) in pathify(fan, "{}/fan".format(topic_namespace)):
                publish(t, v)
            temp = get_temperature(conn)
            publish("{}/temp".format(topic_namespace), temp)
            co2  = get_co2(conn)
            publish("{}/co2".format(topic_namespace), co2)
            humi  = get_humidity(conn)
            publish("{}/humi".format(topic_namespace), humi)
        except Exception as e:
            log.warn("An exception occured, retry in 15 seconds", exc_info=True)
            sleep(15)
            continue
        break

    for _ in range(15):
        sleep(1)
        if not _running:
            break

    log.info("Starting read loop")
    while _running:
        try:
            _netw = get_network_data(conn)
            cnetw = changes(netw, _netw)
            netw  = _netw
            for (t, v) in pathify(cnetw, "{}/network".format(topic_namespace)):
                publish(t, v)
        except Exception as e:
            log.warn("An exception occured getting network, skipping", exc_info=True)

        try:
            _fan  = get_fan_speed(conn)
            cfan  = changes(fan, _fan)
            fan   = _fan
            for (t, v) in pathify(cfan, "{}/fan".format(topic_namespace)):
                publish(t, v)
        except Exception as e:
            log.warn("An exception occured getting fan speed, skipping", exc_info=True)

        try:
            _temp = get_temperature(conn)
            if _temp != temp:
                temp = _temp
                publish("{}/temp".format(topic_namespace), temp)
        except Exception as e:
            log.warn("An exception occured getting temp, skipping", exc_info=True)

        try:
            _co2  = get_co2(conn)
            if _co2 != co2:
                co2 = _co2
                publish("{}/co2".format(topic_namespace), co2)
        except Exception as e:
            log.warn("An exception occured getting CO2, skipping", exc_info=True)

        try:
            _humi  = get_humidity(conn)
            if _humi != humi:
                humi = _humi
                publish("{}/humi".format(topic_namespace), humi)
        except Exception as e:
            log.warn("An exception occured getting humidity, skipping", exc_info=True)

        for _ in range(15):
            sleep(1)
            if not _running:
                break



def on_mqtt_connect(client, userdata, flags, rc):
    # Subscribe to all topics in our namespace when we're connected. Send out
    # a message telling we're online
    log.info("Connected with result code "+str(rc))
    mqtt_client.subscribe('{}/#'.format(settings['mqtt']['sub_topic_namespace']))
    mqtt_client.subscribe('{}'.format(settings['mqtt']['sub_topic_namespace']))
    mqtt_client.publish(
        topic=topic_namespace,
        payload="online",
        qos=settings['mqtt']['qos'],
        retain=settings['mqtt']['retain'])

def on_mqtt_message(client, userdata, msg):
    # Handle incoming messages
    log.info("Received message on topic {} with payload {}".format(
                msg.topic, str(msg.payload)))
    namespace = settings['mqtt']['sub_topic_namespace']
    command_generators={
        "{}/state".format(namespace): \
            lambda _ :ctrl.set_state(_),
    }
    # Find the correct command generator from the dict above
    command = command_generators.get(msg.topic)
    if command:
        log.debug("Calling command")
        # Get the command and call it
        command(msg.payload)
