import adafruit_ds3231
import adafruit_bus_device
import adafruit_register
import adafruit_ntp
import time

def init(i2c_board, i2c_qwiic):
    ds3231 = None
    if i2c_qwiic:
        try:
            ds3231 = adafruit_ds3231.DS3231(i2c_qwiic)
        except:
            if i2c_board:
                try:
                    ds3231 = adafruit_ds3231.DS3231(i2c_board)
                except:
                    ds3231 = None

    return ds3231


def set(ds3231, pool):
    # t = struct.time((year, month, day, hour, minute, second, wday, yday, is_dst))
    #ds3231.datetime = time.struct_time((2023, 4, 15, 16, 19, 3, 5, 106, 1))
    try:
        ntp = adafruit_ntp.NTP(pool, tz_offset=-5) # TX offset is -6 for Daylight Savings, -5 for Standard
        try:
            ds3231.datetime = ntp.datetime
            return True
        except Exception as ex:
            print("ERROR: DS3231 issue:\n{}".format(ex))
            return False
    except Exception as ex:
        print("ERROR: NTP issue:\n{}".format(ex))
        return False


def read(ds3231):
    current = ds3231.datetime
    #print('The current time is: {}/{}/{} {:02}:{:02}:{:02}'.format( \
    #current.tm_mon, current.tm_mday, current.tm_year, current.tm_hour, current.tm_min, current.tm_sec))

    sensor_data = {
        "type": "ds3231",
        "datetime": '{}/{}/{} {:02}:{:02}:{:02}'.format( \
        current.tm_mon, current.tm_mday, current.tm_year, current.tm_hour, current.tm_min, current.tm_sec)
    }

    return sensor_data
