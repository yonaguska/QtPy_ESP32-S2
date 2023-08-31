import time
import board
import digitalio
import analogio
from board import A3
from adafruit_simplemath import map_range

def get_voltage(pin):
    return (pin.value * 3.3) / 65536

def init(model):
    probe_ready = False
    ## Power pin for soil moisture detector
    if (model == "featherS2") or (model == "featherS3"):
        adc = analogio.AnalogIn(A3)
        soil_moisture_power = digitalio.DigitalInOut(board.D11) # GPIO/D11
        soil_moisture_power.direction = digitalio.Direction.OUTPUT
        probe_ready = True
    if (model == "qtpy"):
        adc = analogio.AnalogIn(A3)
        soil_moisture_power = digitalio.DigitalInOut(board.D18) # GPIO/D18 (AKA A0)
        soil_moisture_power.direction = digitalio.Direction.OUTPUT
        probe_ready = True
    return probe_ready, soil_moisture_power, adc

def read(soil_moisture_power, adc):
    # Power up the soil probe and let it stabilize before taking reading
    soil_moisture_power.value = True
    time.sleep(2)
    soil_probe_voltage = get_voltage(adc)
    soil_value = map_range(soil_probe_voltage, 0.899977 , 2.35596, 100, 0)
    # Power down the soil probe
    soil_moisture_power.value = False
    sensor_data = {
    	"type":  "soil_probe",
        "soil_probe_voltage": soil_probe_voltage,
        "soil_value": soil_value
             }
    return sensor_data
