import adafruit_sht4x

def init(i2c_board, i2c_qwiic):
    sht40 = None
    if i2c_qwiic:
        try:
            sht40 = adafruit_sht4x.SHT4x(i2c_qwiic, address=0x44)
        except:
            if i2c_board:
                try:
                    sht40 = adafruit_sht4x.SHT4x(i2c_board, address=0x44)
                except:
                    sht40 = None

    return sht40


def read(sht40):
    sensor_data = {
    	"type":  "sht40",
        "tempF": (9.0/5.0)*sht40.temperature + 32.0,
        "tempC": sht40.temperature,
        "humP":  sht40.relative_humidity
             }
    return sensor_data
