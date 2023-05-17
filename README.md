# QtPy_ESP32-S2
Adafruit QtPy ESP32 S2 used in leak detector

Kirk Franks, hobby shack 2023

This is the refactored leak detector code. I am creating modules for the
hardware aspects of the system to simplify creation and maintenance of
new and existing hardware.

The new modules include support for:
- i2c       (stemma qt and onboard)
- neopixel  (onboard indicator)
- aht20     (temp and humidity)
- sht40     (temp and humidity)
- bme280    (temp, humidity, pressure, and altitude)
- bme680    (temp, humidity, pressure, altitude, and voc/gas)
- ds3231    (timestamp, set via NTP)
- wifi      (if present)
- lc709203f (feather2 s2/s3)
- ina260    (option for testing)
- 24lc32    (4kB EEPROM on the DS3231)

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



