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


class Spindle(object):
    """Abstract Class for Spindle
    Spindle can rotate clockwise or counterclockwise
    in given Speed
    """

    CW = -1 # clockwise direction
    CCW = 1 # counter clockwise direction

    def __init__(self, speed=1.0):
        self.speed = speed
        self.running = False

    def rotate(self, direction, speed=None):
        """
        turn on spindle and rotate in direction with speed
        """
        if speed is None:
            speed = self.speed
        self.running = True
        logging.info("Turn Spindle in Direction %s with speed %s", direction, speed)
        
    def get_state(self):
        if self.running:
            return("%s@%s" % (self.running, self.speed))
        else:
            return("not running")

    def unhold(self):
        """
        power off Spindle
        """
        logging.info("Power Off Spindle")
        self.running = False


class Laser(Spindle):
    """Abstract Class for Spindle
    Spindle can rotate clockwise or counterclockwise
    in given Speed
    """

    def __init__(self, power_pin, speed=1.0):
        self.power_pin = power_pin
        GPIO.setup(self.power_pin, GPIO.OUT)
        Spindle.__init__(self, speed=1.0)

    def rotate(self, direction, speed=None):
        """
        turn on spindle and rotate in direction with speed
        """
        logging.info("Turn Laser on")
        GPIO.output(self.power_pin, 1)
        self.running = True
        
    def unhold(self):
        """
        power off Spindle
        """
        logging.info("Turn Laser off")
        GPIO.output(self.power_pin, 0)
        self.running = False
