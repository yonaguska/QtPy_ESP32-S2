import time
import board
import digitalio
import analogio
from board import A1
from adafruit_simplemath import map_range

def get_voltage(pin):
    return (pin.value * 3.3) / 65536

def init(model):
    probe_ready = False
    ## Power pin for soil moisture detector
    if (model == "featherS2") or (model == "featherS3"):
        adc = analogio.AnalogIn(A1)
        probe_ready = True
    if (model == "qtpy"):
        adc = analogio.AnalogIn(A1)
        probe_ready = True
    return probe_ready, adc

def read(adc):
    # Power up the soil probe and let it stabilize before taking reading
    time.sleep(1)
    divider_reading = 1.0 * get_voltage(adc)
    battery_voltage = map_range(divider_reading, 0.032 , 3.2, 0.0, 16.0)
    # Power down the soil probe
    sensor_data = {
    	"type":  "battery",
        "divider_reading": divider_reading,
        "battery_voltage": battery_voltage
             }
    return sensor_data
