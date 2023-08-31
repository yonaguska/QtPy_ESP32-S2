import adafruit_ahtx0

def init(i2c_board, i2c_qwiic):
    aht20 = None
    if i2c_qwiic:
        try:
            aht20 = adafruit_ahtx0.AHTx0(i2c_qwiic, address=0x38)
        except:
            if i2c_board:
                try:
                    aht20 = adafruit_ahtx0.AHTx0(i2c_board, address=0x38)
                except:
                    aht20 = None

    return aht20


def read(aht20):
    sensor_data = {
    	"type":  "aht20",
        "tempF": (9.0/5.0)*aht20.temperature + 32.0,
        "tempC": aht20.temperature,
        "humP":  aht20.relative_humidity
             }
    return sensor_data
