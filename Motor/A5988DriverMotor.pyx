#/usr/bin/python
# -*- coding: utf-8 -*-
#
# parse Gcode
#
"""
Motor Classes for Controller
"""

import BaseMotor

class A5988DriverMotor(BaseMotor.BaseMotor):
    """
    This Motor is connected to a a5988 driver, which only needs two pins
    to control the motor

    dir
    step
    """

    def __init__(self, int step_pin, int dir_pin, int max_position, int min_position, int delay, bint sos_exception=False):
        """
        coils a set of for GPIO like object to represent a1, a2, b1, b2 connection to motor
        max_position
        min_position
        delay between phase changes in seconds
        """
        super().__init__(self, max_position, min_position, delay, sos_exception)
        self.step_pin = step_pin
        self.dir_pin = dir_pin
        self.unhold()

    def _move(self, int direction):
        """
        move one step in direction
        """
        self.position += direction
        # direction is either -1 or 1
        if direction == 1:
            self.dir_pin.output(1)
        else:
            self.dir_pin.output(0)
        self.step_pin.output(0)
        self.step_pin.output(1)

    def unhold(self):
        """
        sets any pin of motor to low, so no power is needed
        """
        pass
