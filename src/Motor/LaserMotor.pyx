#/usr/bin/python
# -*- coding: utf-8 -*-
#
# parse Gcode
#
"""
Motor Classes for Controller
"""

import logging
logging.basicConfig(level=logging.INFO, format="%(message)s")
import time
import BaseMotor

class LaserMotor(BaseMotor.BaseMotor):
    """Laser Motor, reactive if axis moves negative"""

    def __init__(self, laser_pin, max_position, min_position, delay, sos_exception=False):
        """
        GPIO like Object for laser_pin
        max_position value
        min_position value
        delay between phase changes
        """
        BaseMotor.BaseMotor.__init__(self, max_position, min_position, delay, sos_exception)
        self.laser_pin = laser_pin
        self.unhold()
 
    def _move(self, direction):
        """move number of full integer steps"""
        self.position += direction
        # turn on laser if position < 0
        if self.position < 0.0:
            self.laser_pin.output(1)
        else:
            self.laser_pin.output(0)

    def unhold(self):
        """power off"""
        logging.info("Power off laser")
        self.laser_pin.output(0)

