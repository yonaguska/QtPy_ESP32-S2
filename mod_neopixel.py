import neopixel

import board
import time

""" stuff for the onboard neopixel """
# pixel definitions
pixel = neopixel.NeoPixel(board.NEOPIXEL, 1)
dim_red = (10, 0, 0)
dim_green = (0, 10, 0)
dim_blue = (0, 0, 10)
bright_red = (100, 0, 0)
bright_green = (0, 100, 0)
bright_blue = (0, 0, 100)
pixels_off = (0, 0, 0)


def power_pixel(pixels, time_on):
    """ this code manipulates the onboard neopixel """
    pixel.fill(pixels)
    time.sleep(time_on)


def connected_health(do_send_to_broker):
    """ Show everyone we're alive """
    # Show the user we're alive by manipulating the Neopixel
    power_pixel(dim_red, 0.1)
    power_pixel(dim_green, 0.1)
    power_pixel(dim_blue, 0.1)
    power_pixel(pixels_off, 0.1)
    if do_send_to_broker:
        power_pixel(bright_green, 1)
    else:
        power_pixel(bright_red, 1)
    power_pixel(pixels_off, 0.1)


def no_sensors():
    # Show the user we have a sensor issue by manipulating the Neopixel
    power_pixel(dim_red, 0.1)
    power_pixel(dim_green, 0.1)
    power_pixel(dim_blue, 0.1)
    power_pixel(pixels_off, 0.1)
    power_pixel(bright_red, 1)
    power_pixel(pixels_off, 0.1)
    power_pixel(bright_red, 1)
    power_pixel(pixels_off, 0.1)
    power_pixel(bright_red, 1)
    power_pixel(pixels_off, 0.1)
