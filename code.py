'''
   Kirk Franks, hobby shack 2023

   This is the refactored leak detector code. I am creating modules for the
   hardware aspects of the system to simplify creation and maintenance of
   new and existing hardware.

   The new modules include support for:
   - i2c        (stemma qt and onboard)
   - neopixel   (onboard indicator)
   - aht20      (temp and humidity)
   - sht40      (temp and humidity)
   - bme280     (temp, humidity, pressure, and altitude)
   - bme680     (temp, humidity, pressure, altitude, and voc/gas)
   - ds3231     (timestamp, set via NTP)
   - wifi       (if present)
   - lc709203f  (feather2 s2/s3)
   - ina260     (option for testing)
   - 24lc32     (4kB EEPROM on the DS3231)
   - soil_probe (separate probe; power and analog input)
   - battery    (external battery voltage monitor...useful for solar chargers)

   The code accommodates adding hardware, detecting it, and using it automatically
   It also allows the hardware to be on existing I2C pins or a STEMMA QT connector.

   A typical hardware module initializes and readies the sensor, handles reading
   values and making them ready for the main code.

   The main code can upload values via WiFi or LoRa; modules exist for each.

   This code was built for CircuitPython 8.

   QtPy ESP32-S2
   >>> dir(board)
       ['__class__', '__name__', 'A0', 'A1', 'A2', 'A3', 'A4', 'A5', 'A6', 'A7',
       'BOOT0', 'BUTTON', 'D0', 'D16', 'D17', 'D18', 'D35', 'D36', 'D37', 'D40',
       'D41', 'D5', 'D6', 'D7', 'D8', 'D9', 'I2C', 'MISO', 'MOSI', 'NEOPIXEL',
       'NEOPIXEL_POWER', 'RX', 'SCK', 'SCL', 'SCL1', 'SDA', 'SDA1', 'SPI',
       'STEMMA_I2C', 'TX', 'UART', 'board_id']
>>>
'''

# SPDX-FileCopyrightText: 2021 ladyada for Adafruit Industries
# SPDX-License-Identifier: MIT
# standard libraries
import os
import re
import alarm
import time
import ssl
import socketpool

# standard CircuitPython libraries
import busio
import microcontroller
import watchdog
import wifi
import storage
import board
#from board import A0  # ADC/DAC, used as digital VCC for soil probe
from board import A1  # ADC/DAC 12v Battery monitor 12k-3k divider
from board import A2  # ADC QtPy BFF battery voltage
#from board import A3  # ADC for soil probe
import digitalio
from digitalio import DigitalInOut
import analogio
from analogio import AnalogIn

# Adafruit libraries
import adafruit_minimqtt.adafruit_minimqtt as MQTT
import adafruit_sdcard
import adafruit_logging as logging
from adafruit_logging import FileHandler
from adafruit_lc709203f import LC709203F
from adafruit_io.adafruit_io import IO_MQTT
from adafruit_simplemath import map_range

# my libraries
import mod_neopixel
import mod_i2c
import mod_aht20
import mod_sht40
import mod_bme280
import mod_bme680
import mod_ina260
import mod_ds3231
import mod_24lc32
import mod_soil_probe
import mod_battery_voltage


""" basic global variables ... very important!!! """
version = 8.4 # Working copy with sensors, RTC w/NTP, soil_probe, external battery probe, and talks to MQTT via Wifi
code_status = "work in progress"
sleep_time = 60 * 5 #  sleep_time = 60 * 5   .... or 60 for testing
watchdog_timeout = sleep_time + 30
debug = True
connect_to_wifi = True  # False for debugging
do_connect_to_broker = True
do_send_to_broker = True
ic2_connected = False
i2c_qwiic_connected = False
model = "qtpy"  # or qtpy/featherS2/featherS3
using_bff = True
test_watchdog = False
reset_wait_time = 300
reload_wait_time = 300
charger = "bff"  # or solar/bff
using_hardware_watchdog = True
hardware_reset_duration = 0.1
trigger_duration = 0.2
error_sleep = sleep_time
sd_card = False
soil_moisture_detector_used = True
battery_probe_used = True
sd_card_used = True
testing_wdt = False
set_ds3231 = False   # <<<<<<<<<<< IF YOU NEED TO SET THE RTC, USING NTP >>>>>>>>


""" FUNCTIONS """
# The print function....also logs
def my_print(level, message, end=''):
    U_level = level.upper()
    mod_message = "{}: {}".format(U_level, message)
    print("{}".format(mod_message))
    if sdcard_filesystem:
        if level == "debug":
            logger.debug(mod_message)
        elif level == "info":
            logger.info(mod_message)
        elif level == "warning":
            logger.warning(mod_message)
        elif level == "error":
            logger.error(mod_message)
        elif level == "critical":
            logger.critical(mod_message)
        else:
            logger.debug(mod_message)


# This helper function will print the contents of the SD
def print_directory(path, tabs=0):
    print("Files on filesystem:")
    print("====================")
    for file in os.listdir(path):
        stats = os.stat(path + "/" + file)
        filesize = stats[6]
        isdir = stats[0] & 0x4000

        if filesize < 1000:
            sizestr = str(filesize) + " bytes"
        elif filesize < 1000000:
            sizestr = "%0.1f KB" % (filesize / 1000)
        else:
            sizestr = "%0.1f MB" % (filesize / 1000000)

        prettyprintname = ""
        for _ in range(tabs):
            prettyprintname += "   "
        prettyprintname += file
        if isdir:
            prettyprintname += "/"
        print("{0:<40} Size: {1:>10}".format(prettyprintname, sizestr))

        # recursively print directory contents
        if isdir:
            print_directory(path + "/" + file, tabs + 1)


def get_voltage(pin):
    return (pin.value * 3.3) / 65536


def deep_sleep(this_sleep_time):
    """ Do a deep sleep to conserve battery and close logger file handle """
    # prepare and sleep
    time_alarm = alarm.time.TimeAlarm(monotonic_time=time.monotonic() + this_sleep_time)
    alarm.exit_and_deep_sleep_until_alarms(time_alarm)


""" MQTT related callbacks """
# Define callback methods which are called when events occur
# pylint: disable=unused-argument, redefined-outer-name
def connect(mqtt_client, userdata, flags, rc):
    # This function will be called when the mqtt_client is connected
    # successfully to the broker.
    my_print("info" ,"Connected to MQTT Broker!")
    my_print("info" ,"Flags: {0}\n RC: {1}".format(flags, rc))


def disconnect(mqtt_client, userdata, rc):
    # This method is called when the mqtt_client disconnects
    # from the broker.
    my_print("info" ,"Disconnected from MQTT Broker!")


def subscribe(mqtt_client, userdata, topic, granted_qos):
    # This method is called when the mqtt_client subscribes to a new feed.
    my_print("info" ,"Subscribed to {0} with QOS level {1}".format(topic, granted_qos))


def unsubscribe(mqtt_client, userdata, topic, pid):
    # This method is called when the mqtt_client unsubscribes from a feed.
    my_print("info" ,"Unsubscribed from {0} with PID {1}".format(topic, pid))


def publish(mqtt_client, userdata, topic, pid):
    # This method is called when the mqtt_client publishes data to a feed.
    #my_print("info" ,"Published to {0} with PID {1}".format(topic, pid))
    pass


def message(client, topic, message):
    # Method called when a client's subscribed feed has a new value.
    my_print("info" ,"New message on topic {0}: {1}".format(topic, message))


""" intermediate functions to use the MQTT functions """
def connect_to_broker():
    if do_connect_to_broker:
        # Connect to Broker
        try:
            my_print("info" ,"Connecting to Broker at {}...".format(secrets["broker"]))
            mqtt_client.connect()
            return True
        except RuntimeError:
            my_print("info" ,"Failed to connect to Broker...RuntimeError, wait {} seconds and reset".format(reset_wait_time))
            time.sleep(reset_wait_time)
            microcontroller.reset()
            deep_sleep(sleep_time)  # recover by deep sleep reset
        except Exception as ex:
            template = "An exception of type {0} occurred. Arguments:\n{1!r}"
            message = template.format(type(ex).__name__, ex.args)
            my_print("info" ,"MQTT Error: Unable to connect to Broker\n{}".format(message))
            my_print("info" ,"Failed to connect, wait {} seconds and reset".format(reset_wait_time))
            time.sleep(reset_wait_time)
            microcontroller.reset()
            deep_sleep(sleep_time)  # recover by deep sleep reset
    else:
        return True


def disconnect_from_broker():
    if do_connect_to_broker:
        # Connected to Broker
        try:
            my_print("info" ,"Disconnecting from Broker...")
            #io.disconnect()
            mqtt_client.disconnect()
            return True
        except Exception as ex:
            template = "An exception of type {0} occurred. Arguments:\n{1!r}"
            message = template.format(type(ex).__name__, ex.args)
            my_print("info" ,"MQTT Error: Unable to disconnect to Broker\n{}".format(message))
            deep_sleep(sleep_time)  # recover by deep sleep reset
    else:
        return True


def publish_to_broker(tag, nomenclature, value):
    # Send MQTT data to my broker
    if do_send_to_broker:
        #my_print("info" ,"Publishing {:.2f} {} to {} ... ".format(value, nomenclature, tag), end=' ')
        try:
            #io.publish("{}".format(tag), value)
            if mqtt_client.is_connected():
                mqtt_client.publish("{}".format(tag), value)
        except OSError:
            my_print("info" ,"OSError occurred, not connected to broker...wait {} seconds and reset\n".format(reset_wait_time))
            time.sleep(reset_wait_time)
            microcontroller.reset()
        except Exception as ex:
            template = "An exception of type {0} occurred. Arguments:\n{1!r}"
            message = template.format(type(ex).__name__, ex.args)
            my_print("info" ,"MQTT Error: Unable to publish to Broker\n{}".format(message))
            my_print("info" ,"...wait {} seconds and reset\n".format(reset_wait_time))
            time.sleep(reset_wait_time)
            microcontroller.reset()
            deep_sleep(sleep_time)  # recover by deep sleep reset
        my_print("info" ,"Published {:.2f} {} to {} ... ".format(value, nomenclature, tag), end=' ')

    else:
        my_print("info" ,"Read {:.2f} {} for {}".format(value, nomenclature, tag))


def setup_watchdog(watchdog_timeout):
    # set up watchdog to reset system if it gets stuck on wifi or broker connections
    wdt = microcontroller.watchdog
    try:
        wdt.timeout = watchdog_timeout
        wdt.mode = watchdog.WatchDogMode.RAISE
        my_print("info" ,"set watchdog_timeout to {} seconds and started watchdog".format(watchdog_timeout))
        if test_watchdog:
            my_print("info" ,"set sleep to {} seconds to test watchdog".format(watchdog_timeout + 10))
            time.sleep(watchdog_timeout + 10)  # this delay should trigger watchdog timeout
        return wdt
    except watchdog.WatchDogTimeout as e:
        my_print("info" ,"Watchdog expired, reset system")
        microcontroller.reset()
    except Exception as e:
        my_print("info" ,"Other exception, reset system:\n{}".format(e))
        microcontroller.reset()


def retrigger_hardware_watchdog(trigger_duration):
    if using_hardware_watchdog:
        # take trigger low ... retrigger the hardware watchdog
        if testing_wdt:
            my_print("info" ,"retrigger the hardware watchdog ... currently is {}".format(wdt_out.value))
        trigger.value = False
        time.sleep(trigger_duration)
        trigger.value = True
        if testing_wdt:
            my_print("info" ,"hardware watchdog retriggered ...   currently is {}".format(wdt_out.value))
    else:
        my_print("info" ,"not using hardware watchdog")


""" CODE ############################################################################# """

#### SETUP HARDWARE ######################################################################

#### Setup SD card for logging
# Get chip select pin depending on the board, this one is for the Feather M4 Express
sd_cs = board.TX
sdcard_found = False
try:
    # Set up SPI
    spi = busio.SPI(board.SCK, board.MOSI, board.MISO)
    cs = DigitalInOut(sd_cs)
    try:
        # Set up SD card for logging
        sdcard = adafruit_sdcard.SDCard(spi, cs)
        print("\ncreated the sdcard object")
        try:
            # Create a file system
            vfs = storage.VfsFat(sdcard)
            print("created the vfs")
            try:
                # Mount the file system
                storage.mount(vfs, "/sd")
                print("mounted the sd")
                sdcard_found = True
            except Exception as ex:
                print("Error with mount ... {}".format(ex))
        except Exception as ex:
            print("Error with vfs ... {}".format(ex))
    except Exception as ex:
        print("Error with sd card ... {}".format(ex))
except Exception as ex:
    print("Error with spi ... {}".format(ex))

# print filesystem contents
if sdcard_found: print_directory("/sd")

#### Initialize log functionality
sdcard_filesystem = False
log_filepath = "/sd/testlog.log"
logger = logging.getLogger("testlog")
try:
    file_handler = FileHandler(log_filepath)
    logger.addHandler(file_handler)
    logger.setLevel(logging.NOTSET)
    sdcard_filesystem = True
    print("sdcard filesystem looks good for logging")
except Exception as ex:
    print("Error with sdcard filesystem ... {}".format(ex))
# test logging
my_print("info", "Testing log")

#### Analog pins for battery state on qtpy
#adc0 = analogio.AnalogIn(A0)  # unused ADC/DAC, used as digital for Vcc of soil moisture probe
#adc1 = analogio.AnalogIn(A1)  # 12v Battery monitor 12k-3k divider ... handled in module
adc2 = analogio.AnalogIn(A2)  # QtPy BFF voltage
#adc3 = analogio.AnalogIn(A3)  # Soil probe ... handled in module

#### Soil moisture detector
if soil_moisture_detector_used:
    soil_probe_ready, soil_moisture_power, soil_adc = mod_soil_probe.init(model)

#### Battery probe
if battery_probe_used:
    battery_probe_ready, battery_adc = mod_battery_voltage.init(model)

#### Watchdog timer
trigger = digitalio.DigitalInOut(board.D6) # GPIO/D6 was A1(GPIO/D17)
trigger.direction = digitalio.Direction.OUTPUT
trigger.value = True

if testing_wdt:
    ## define an input pin for WDT (for testing)
    wdt_out = digitalio.DigitalInOut(board.D9) # GPIO/D9
    wdt_out.direction = digitalio.Direction.INPUT


#### FUNCTIONAL CODE #####################################################################
print() # for aesthetics to separate runs visually
my_print("info", "Logger initialized!")
if sdcard_filesystem: my_print("info", "sdcard_filesystem found")
#### print version and the last reset reason
reset_reason = 0
if microcontroller.cpu.reset_reason == microcontroller.ResetReason.POWER_ON:
    reset_reason = 1
elif microcontroller.cpu.reset_reason == microcontroller.ResetReason.SOFTWARE:
    reset_reason = 2
elif microcontroller.cpu.reset_reason == microcontroller.ResetReason.WATCHDOG:
    reset_reason = 3
else : pass
my_print("info" ,"VERSION: {}, reset reason is {}".format(version, microcontroller.cpu.reset_reason))
my_print("info", "code_status is {}".format(code_status))

# retrigger the hardware watchdog
retrigger_hardware_watchdog(trigger_duration)

# assign a battery sensor
if (model == "featherS2"):
    battery_sensor_found = False
    try:
        battery_sensor = LC709203F(board.I2C())
        my_print("info" ,"featherS2 battery sensor found, IC version {}".format(hex(battery_sensor.ic_version)))
        battery_sensor_found = True
    except:
        my_print("info" ,"featherS2 battery sensor not found")

#### Setup I2C
i2c_board, i2c_qwiic = mod_i2c.init()
my_print("info", "Using i2c_onboard is {}, using i2c_qwiic is {}".format(i2c_board, i2c_qwiic))
if i2c_board != None: i2c_connected = True
else: i2c_connected = False
if i2c_qwiic != None: i2c_qwiic_connected = True
else: i2c_qwiic_connected = False

#### Setup I2C sensors

## The environmental sensors
aht20_found = False
sht40_found = False
bme280_found = False
bme680_found = False
ds3231_found = False

# check for an aht20 sensor
aht20 = mod_aht20.init(i2c_board, i2c_qwiic)
if aht20 != None:
    my_print("info", "AHT20 found")
    aht20_found = True
else:
    my_print("info", "AHT20 not found")

# check for an sht40 sensor
sht40 = mod_sht40.init(i2c_board, i2c_qwiic)
if sht40 != None:
    my_print("info", "SHT40 found")
    sht40_found = True
else:
    my_print("info", "SHT40 not found")

# check for an bme280 sensor
bme280 = mod_bme280.init(i2c_board, i2c_qwiic)
if bme280 != None:
    my_print("info", "BME280 found")
    bme280_found = True
    # change this to match the location's pressure (hPa) at sea level
    bme280.sea_level_pressure = 1020.0

else:
    my_print("info", "BME280 not found")

# check for an bme680 sensor
bme680 = mod_bme680.init(i2c_board, i2c_qwiic)
if bme680 != None:
    my_print("info", "BME680 found")
    bme680_found = True
    # change this to match the location's pressure (hPa) at sea level
    bme680.sea_level_pressure = 1020.0
    # You will usually have to add an offset to account for the temperature of
    # the sensor. This is usually around 5 degrees but varies by use. Use a
    # separate temperature sensor to calibrate this one.
    temperature_offset = -1
else:
    my_print("info", "BME680 not found")

# check for an INA260 voltage/current sensor
ina260 = mod_ina260.init(i2c_board, i2c_qwiic)
ina260_found = False
if ina260 != None:
    my_print("info", "INA260 found")
    ina260_found = True
else:
    my_print("info", "INA260 not found")


# indicate the health of the environmental sensors
env_sensors_found = True
if not (aht20_found or sht40_found or bme280_found or bme680_found):
    my_print("info" ,"No sensor found, sleeping")
    mod_neopixel.no_sensors()
    env_sensors_found = False
    #deep_sleep(error_sleep)  # recover by deep sleep reset

# Set up the DS3231 RTC, set it if necessary
ds3231 = mod_ds3231.init(i2c_board, i2c_qwiic)
if ds3231 != None:
    my_print("info", "DS3231 found")
else:
    my_print("info", "DS3231 not found")

# Set up the 24LC32 EEPROM on the DS3231 module we're using
eeprom = mod_24lc32.init(i2c_board, i2c_qwiic)
if eeprom != None:
    my_print("info", "EEPROM found")
else:
    my_print("info", "EEPROM not found")

# create a sensors dictionary
sensors = {}
if env_sensors_found:
    #### READ SENSORS
    if aht20 != None:
        sensor = mod_aht20.read(aht20)
        sensors.update({sensor['type']:sensor})

    if sht40 != None:
        sensor = mod_sht40.read(sht40)
        sensors.update({sensor['type']:sensor})

    if bme280 != None:
        sensor = mod_bme280.read(bme280)
        sensors.update({sensor['type']:sensor})

    if bme680 != None:
        sensor = mod_bme680.read(bme680)
        sensors.update({sensor['type']:sensor})

    if ds3231 != None:
        sensor = mod_ds3231.read(ds3231)
        sensors.update({sensor['type']:sensor})

    if soil_moisture_detector_used:
        sensor = mod_soil_probe.read(soil_moisture_power, soil_adc)
        sensors.update({sensor['type']:sensor})

    if battery_probe_used:
        sensor = mod_battery_voltage.read(battery_adc)
        sensors.update({sensor['type']:sensor})
        while(False):
            time.sleep(1.0)
            sensor = mod_battery_voltage.read(battery_adc)
            print("divider {} voltage {}".format(sensor["divider_reading"], sensor["battery_voltage"]))


if eeprom != None:
    # Check the upper EEPROM for flag ... bytearray\(b'KFRANKS'\)
    begin = 4000
    store = bytearray(b'KFRANKS')
    end = begin + len(store)
    #print("begin {} -> {}".format(begin, end))
    sensor = mod_24lc32.read(eeprom, begin, end)
    sensors.update({sensor['type']:sensor})
    # if we have set the flag, just say so, otherwise set it
    if str(sensor['value_list']) == str(store):
        my_print("info", "{} - EEPROM matches 'KFRANKS'".format(sensor['status_message']))
    else:
        my_print("info", "{} - EEPROM contains - {} - DS3231 NEEDS TO BE SET".format(sensor['status_message'], sensor['value_list']))
        # This tells us to set the DS3231 to the current time. We only need to do this once.
        set_ds3231 = True

if (model == "qtpy") and using_bff:
    bff = (adc2.value/10000.0)*1.0183
    #vA0 = (adc0.value * 3.3) / 65536
    #vA1 = (adc1.value * 3.3) / 65536
    vA2 = (adc2.value * 3.3) / 65536
    #vA3 = (adc3.value * 3.3) / 65536
    voltage = 0
    if charger == "solar": voltage = vA2
    if charger == "bff": voltage = bff
    sensors.update({"battery_voltage": voltage})

sensors.update({"version": version})
sensors.update({"code_status": code_status})
sensors.update({"microcontroller.cpu.reset_reason": microcontroller.cpu.reset_reason})


#### setup watchdog to catch issues with WiFi or MQTT broker connections
wdt = setup_watchdog(watchdog_timeout)

# Add a secrets.py to your filesystem that has a dictionary called secrets with
# "ssid" and "password" keys with your WiFi credentials.
# DO NOT share that file or commit it into Git or other source control.
# pylint: disable=no-name-in-module,wrong-import-order

""" Wifi stuff """
# Read secrets
try:
    from secrets import secrets
except ImportError:
    my_print("info" ,"WiFi secrets are kept in secrets.py, please add them there!")
    raise

# Connect to WiFi
if connect_to_wifi:
    wifi_connected = False
    try:
        my_print("info" ,"Connecting to %s" % secrets["ssid"])
        wifi.radio.connect(secrets["ssid"], secrets["password"])
        my_print("info" ,"Connected to %s!" % secrets["ssid"])
        my_print("info" ,"Using IP %s" % wifi.radio.ipv4_address)
        this_ip = wifi.radio.ipv4_address
        regex = re.compile("[\.]")
        octets = regex.split("{}".format(this_ip))
        topic_prefix = '{}/{}'.format(model, octets[-1])
        my_print("info" ,"topic_prefix = {}".format(topic_prefix))
        wifi_connected = True
        sensors.update({"IP": wifi.radio.ipv4_address})
        sensors.update({"topic_prefix": topic_prefix})
        my_print("info", "SENSORS: {}".format(sensors))
    except ConnectionError:
        my_print("info" ,"Failed to connect...ConnectionError, wait {} seconds and reload".format(reload_wait_time))
        time.sleep(reload_wait_time)
        # Set up for deep sleep to conserve battery
        deep_sleep(sleep_time)  # Normal stuff

else:
    do_connect_to_broker = False
    do_send_to_broker = False
    sleep_time = error_sleep

# Create a socket pool
pool = socketpool.SocketPool(wifi.radio)
# !!! DO THIS ONCE, THEN UNSET set_ds3231
if set_ds3231:
    sensor = mod_ds3231.read(ds3231)
    my_print("info", "DS3231 IS SET TO - {}".format(sensor))
    ds3231_is_set = mod_ds3231.set(ds3231, pool)
    sensor = mod_ds3231.read(ds3231)
    my_print("info", "DS3231 IS SET TO - {}".format(sensor))
    if ds3231_is_set:
        # set the flag in EEPROM
        my_print("info", "Writing {} to EEPROM".format(store))
        status_message = mod_24lc32.set(eeprom, begin, end, store) # 'KFRANKS
        my_print("info", "{}".format(status_message))



""" MQTT stuff """
# Set up a MiniMQTT Client
mqtt_client = MQTT.MQTT(
    broker=secrets["broker"],
    port=secrets["port"],
    #username=secrets["aio_username"],
    #password=secrets["aio_key"],
    socket_pool=pool,
    ssl_context=ssl.create_default_context(),
)

# Initialize an Adafruit IO MQTT Client
io = IO_MQTT(mqtt_client)

# Connect callback handlers to mqtt_client
mqtt_client.on_connect = connect
mqtt_client.on_disconnect = disconnect
mqtt_client.on_subscribe = subscribe
mqtt_client.on_unsubscribe = unsubscribe
mqtt_client.on_publish = publish
mqtt_client.on_message = message

# connect to broker
if connect_to_broker():
    my_print("info" ,"Connected to Broker")
else:
    my_print("info" ,"Failed to connect to Broker, wait {} seconds and reload".format(reload_wait_time))
    time.sleep(reload_wait_time)
    # Set up for deep sleep to conserve battery
    deep_sleep(sleep_time)  # Normal stuff

""" Show everyone we're alive """
mod_neopixel.connected_health(do_send_to_broker)

""" Manually publish new values to Broker """
## Explicitly pump the message loop.
#if do_connect_to_broker:
#    #io.loop()
#    mqtt_client.loop()
if debug:
    my_print("info" ,"debug:\n")
else:
    my_print("info" ,"\n")

# publish_to_broker(tag, nomenclature, value)
# topic_prefix is qtpy/xxx, where xxx is the last byte of the IP for this model
if (model == "qtpy") or (model == "featherS2") or (model == "featherS3"):
    publish_to_broker("{}/ResetReason".format(topic_prefix), "f", float("{}.0".format(reset_reason)))
    if env_sensors_found:
        if aht20_found:
            publish_to_broker("{}/AHT20/Temp".format(topic_prefix), "F", sensors['aht20']['tempF'])
            publish_to_broker("{}/AHT20/Humidity".format(topic_prefix), "Percent", sensors['aht20']['humP'])
        if sht40_found:
            publish_to_broker("{}/SHT40/Temp".format(topic_prefix), "F", sensors['sht40']['tempF'])
            publish_to_broker("{}/SHT40/Humidity".format(topic_prefix), "Percent", sensors['sht40']['tempF'])
        if bme280_found:
            publish_to_broker("{}/BME280/Temp".format(topic_prefix), "F", sensors['bme280']['tempF'])
            publish_to_broker("{}/BME280/Humidity".format(topic_prefix), "Percent", sensors['bme280']['humP'])
            publish_to_broker("{}/BME280/Pressure".format(topic_prefix), "inHG", sensors['bme280']['presH'])
            publish_to_broker("{}/BME280/Altitude".format(topic_prefix), "meters", sensors['bme280']['altM'])
        if bme680_found:
            publish_to_broker("{}/BME680/Temp".format(topic_prefix), "F", sensors['bme680']['tempF'])
            publish_to_broker("{}/BME680/Humidity".format(topic_prefix), "Percent", sensors['bme680']['humP'])
            publish_to_broker("{}/BME680/Pressure".format(topic_prefix), "inHG", sensors['bme680']['presH'])
            publish_to_broker("{}/BME680/Altitude".format(topic_prefix), "meters", sensors['bme680']['altM'])
            publish_to_broker("{}/BME680/Gas".format(topic_prefix), "ohm", sensors['bme680']['gasOhm'])

    if ina260_found:
        publish_to_broker("{}/INA260/Battery".format(topic_prefix), "V", ina260.voltage)
        publish_to_broker("{}/INA260/Current".format(topic_prefix), "mA", ina260.current)
        publish_to_broker("{}/INA260/Power".format(topic_prefix), "mW", ina260.power)
    if (model == "qtpy") and using_bff:
        publish_to_broker("{}/BFF/BatteryADC".format(topic_prefix), "V", voltage)
        if soil_moisture_detector_used:
            publish_to_broker("{}/Soil/Moisture".format(topic_prefix), "Percent", sensors['soil_probe']['soil_value'])
        if battery_probe_used:
            publish_to_broker("{}/Battery/Voltage".format(topic_prefix), "Volts", sensors['battery']['battery_voltage'])
    elif (model == "featherS2"):
        if battery_sensor_found:
            voltage = battery_sensor.cell_voltage
            cell_percent = battery_sensor.cell_percent
            publish_to_broker("{}/LC709203F/BatteryVoltage".format(topic_prefix), "V", voltage)
            publish_to_broker("{}/LC709203F/BatteryPercent".format(topic_prefix), "Percent", cell_percent)
        if soil_moisture_detector_used:
            publish_to_broker("{}/Soil/Moisture".format(topic_prefix), "Percent", sensors['soil_probe']['soil_value'])
        if battery_probe_used:
            publish_to_broker("{}/Battery/Voltage".format(topic_prefix), "Volts", sensors['battery']['battery_voltage'])
    else:
        pass

else:
    my_print("info" ,"unknown model {}".format(model))

if (model == "qtpy") or (model == "featherS2"):
    publish_to_broker("{}/Onboard/CPUTemp".format(topic_prefix), "F", (9.0/5.0)*microcontroller.cpu.temperature + 32.0)
if (model == "featherS3"):
    publish_to_broker("{}/Onboard/CPUTemp".format(topic_prefix), "F", (9.0/5.0)*microcontroller.cpus[0].temperature + 32.0)
my_print("info" ,"")

# wait for data to get uploaded
upload_wait = 5
my_print("info" ,"Wait {} seconds for the data to get uploaded".format(upload_wait))
time.sleep(upload_wait)
disconnect_from_broker()


#### the end is near
powerdown_method = "TPL5110"
if powerdown_method == "deep_sleep":
    my_print("info" ,"Deep sleep for {} seconds...".format(this_sleep_time))
    if sdcard_found:
        my_print("info" ,"Closing logger filehandle...this forces writes to SD")
        file_handler.close()  # We're done with the logger file handle, close it
        print_directory("/sd") # print filesystem contents
    # Set up for deep sleep to conserve battery
    deep_sleep(sleep_time)  # Normal stuff
if powerdown_method == "watchdog":
    # feed the watchdog
    my_print("info" ,"Feed the watchdog")
    wdt.feed()
    my_print("info" ,"Deep sleep for {} seconds...".format(this_sleep_time))
    if sdcard_found:
        my_print("info" ,"Closing logger filehandle...this forces writes to SD")
        file_handler.close()  # We're done with the logger file handle, close it
        print_directory("/sd") # print filesystem contents
    deep_sleep(sleep_time)  # Normal stuff
if powerdown_method == "TPL5110":
    #### Set up the pin that indicates DONE for the TPL5110, the circuit cuts off our supply
    # set it True (DONE)
    this_delay = 2
    my_print("info" ,"Telling TPL5110 to shut down power...in {} seconds".format(this_delay))
    if sdcard_found:
        my_print("info" ,"Closing logger filehandle...this forces writes to SD")
        file_handler.close()  # We're done with the logger file handle, close it
        print_directory("/sd") # print filesystem contents
    time.sleep(this_delay)
    DONE = digitalio.DigitalInOut(board.RX) # GPIO/RX
    DONE.direction = digitalio.Direction.OUTPUT
    DONE.value = False
    set_pin = True
    time.sleep(0.2)
    DONE.value = True
    time.sleep(0.8)
    DONE.value = False
    deep_sleep(sleep_time)  # Normal stuff
