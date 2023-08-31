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
- soil_probe (separate probe; power and analog input)
- battery    (external battery voltage monitor...useful for solar chargers)

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

There's a photo, in images, showing my breadboarded prototype. The QtPy, just above the breadboard, is 
stacked with a LiPo battery charger and SD card BFFs. I use an external LiPo charger, 
shown on the breadboard with a green LED light. To the left of the breadboarded LiPo 
charger is a BME280 sensor, and just to the left of that is a DS3231 RTC with an onboard 
24LC32 memory device. To the right of the LiPo charger is a TPL5110, a timer set to a 
5 minute timeout. The TPL5110 controls the power to the QtPy's battery BFF; every 5 
minutes the TPL5110 wakes up the QtPy for processing. The QtPy processes the sensors 
and sends the data via MQTT to a Raspberry Pi RP400, which is processed for display 
by Grafana.

The RP400 has containers for eclipse-mosquitto (MQTT), telegraf (mosquitto_to_influxdb),
influxd (a time-series database), and grafana (a data visualization tool). There are 
screenshots showing portainer's view of the containers running on Docker on the RP400,
as well as graphs of the data using Grafana.

The fritzing_files directory contains files associated with prototyping and the overall
context of the project. You can breadboard the system using this information.

The images directory contains, as the name implies, photos of the prototype and finished
circuit board versions of the system.

The printables directory contains files for 3D printing a baseboard to mount the LiPo and PCB
I created for the project. The base is primarily useful for testing, but the 3D model can
be extended to create an enclosure. I've added the Fusion 360 model and STL files if you
want to fiddle with them. There are photos of this part of the project.

The backend directory has screenshots associated with the RP400-based backend containers.

