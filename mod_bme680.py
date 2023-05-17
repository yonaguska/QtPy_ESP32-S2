import adafruit_bme680

def init(i2c_board, i2c_qwiic):
    bme680 = None
    if i2c_qwiic:
        try:
            bme680 = adafruit_bme680.Adafruit_BME680_I2C(i2c_qwiic, address=0x76)
        except:
            try:
                bme680 = adafruit_bme680.Adafruit_BME680_I2C(i2c_qwiic, address=0x77)
            except:
                if i2c_board:
                    try:
                        bme680 = adafruit_bme680.Adafruit_BME680_I2C(i2c, address=0x76)
                    except:
                        try:
                            bme680 = adafruit_bme680.Adafruit_BME680_I2C(i2c, address=0x77)
                        except:
                            bme680 = None

    return bme680

def read(bme680):
    sensor_data = {
    	"type":  "bme680",
        "tempF": (9.0/5.0)*bme680.temperature + 32.0,
        "tempC": bme680.temperature,
        "humP":  bme680.relative_humidity,
        "presH": bme680.pressure*0.030,
        "altM":  bme680.altitude,
        "gasOhm":bme680.gas
             }
    return sensor_data
