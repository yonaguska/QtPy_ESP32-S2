from adafruit_bme280 import basic as adafruit_bme280

def init(i2c_board, i2c_qwiic):
    bme280 = None
    if i2c_qwiic:
        try:
            bme280 = adafruit_bme280.Adafruit_BME280_I2C(i2c_qwiic, address=0x76)
        except:
            try:
                bme280 = adafruit_bme280.Adafruit_BME280_I2C(i2c_qwiic, address=0x77)
            except:
                if i2c_board:
                    try:
                        bme280 = adafruit_bme280.Adafruit_BME280_I2C(i2c_board, address=0x76)
                    except:
                        try:
                            bme280 = adafruit_bme280.Adafruit_BME280_I2C(i2c_board, address=0x77)
                        except:
                            bme280 = None

    return bme280


def read(bme280):
    sensor_data = {
    	"type":  "bme280",
        "tempF": (9.0/5.0)*bme280.temperature + 32.0,
        "tempC": bme280.temperature,
        "humP":  bme280.relative_humidity,
        "presH": bme280.pressure*0.030,
        "altM":  bme280.altitude
             }
    return sensor_data
