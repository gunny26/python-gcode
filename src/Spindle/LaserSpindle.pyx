#/usr/bin/python

import logging
logging.basicConfig(level=logging.INFO)
from BaseSpindle import BaseSpindle as BaseSpindle


class LaserSpindle(BaseSpindle):
    """Abstract Class for Spindle
    Spindle can rotate clockwise or counterclockwise
    in given Speed
    """

    def __init__(self, power_pin, speed=1.0):
        super(LaserSpindle, self).__init__(speed)
        self.power_pin = power_pin

    def rotate(self, direction, speed=None):
        """
        turn on spindle and rotate in direction with speed
        """
        logging.info("Turn Laser on")
        self.power_pin.output(1)
        self.running = True
        
    def unhold(self):
        """
        power off Spindle
        """
        logging.info("Turn Laser off")
        self.power_pin.output(0)
        self.running = False
