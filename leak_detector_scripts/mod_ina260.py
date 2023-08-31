import adafruit_ina260

def init(i2c_board, i2c_qwiic):
    ina260 = None
    if i2c_qwiic:
        try:
            ina260 = adafruit_ina260.INA260(i2c_qwiic)
        except:
            if i2c_board:
                try:
                    ina260 = adafruit_ina260.INA260(i2c_board)
                except:
                    ina260 = None

    return ina260

def read(ina260):
    sensor_data = {
    	"type":  "ina260",
             }
    return sensor_data
