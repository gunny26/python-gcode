#/usr/bin/python
# -*- coding: utf-8 -*-
#
# parse Gcode
#

try:
    import RPi.GPIO as GPIO
except ImportError:
    from FakeGPIO import FakeGPIO as GPIO
import logging
logging.basicConfig(level=logging.INFO, format="%(message)s")
from Spindle import Spindle


class Laser(Spindle):
    """Abstract Class for Spindle
    Spindle can rotate clockwise or counterclockwise
    in given Speed
    """

    def __init__(self, power_pin, speed=1.0):
        self.power_pin = power_pin
        power_pin.setup(GPIO.OUT)
        Spindle.__init__(self, speed=1.0)

    def rotate(self, direction, speed=None):
        """
        turn on spindle and rotate in direction with speed
        """
        logging.info("Turn Laser on")
        self.power_pin.output(GPIO.HIGH)
        self.running = True
        
    def unhold(self):
        """
        power off Spindle
        """
        logging.info("Turn Laser off")
        self.power_pin.output(GPIO.LOW)
        self.running = False
