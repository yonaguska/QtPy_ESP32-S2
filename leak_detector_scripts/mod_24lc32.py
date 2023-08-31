import adafruit_24lc32


def init(i2c_board, i2c_qwiic):
    eeprom = None
    if i2c_qwiic:
        try:
            eeprom = adafruit_24lc32.EEPROM_I2C(i2c_qwiic, address=0x57)
        except:
            if i2c_board:
                try:
                    eeprom = adafruit_24lc32.EEPROM_I2C(i2c_board, address=0x57)
                except:
                    eeprom = None

    return eeprom


def set(eeprom, begin, end, value_list):
    if end == begin:
        try:
            eeprom[begin] = value_list[0]
            status_message = "Successful setting value into EEPROM"
        except Exception as ex:
            status_message = "ERROR: EEPROM single-value write issue:\n{}".format(ex)
    else:
        try:
            #eeprom[begin:end] = value_list[begin:end]
            eeprom[begin:end] = value_list
            status_message = "Successful setting values into EEPROM"
        except Exception as ex:
            status_message = "ERROR: EEPROM multi-value write issue:\n{}".format(ex)

    return status_message


def read(eeprom, begin, end):
    value_list = []
    if end == begin:
        try:
            value_list = eeprom[begin]
            status_message = "Successful reading value from EEPROM"
        except Exception as ex:
            status_message = "ERROR: EEPROM single-value read issue:\n{}".format(ex)
    else:
        try:
            value_list = eeprom[begin:end]
            status_message = "Successful reading values from EEPROM"
        except Exception as ex:
            status_message = "ERROR: EEPROM multi-value read issue:\n{}".format(ex)

    sensor_data = {
        "type": "24ls32",
        "begin": begin,
        "end": end,
        "value_list": '{}'.format(value_list),
        "status_message": status_message
    }

    return sensor_data
