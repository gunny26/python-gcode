#/usr/bin/python
# -*- coding: utf-8 -*-
#
# parse Gcode
#
"""
Motor Classes for Controller
"""

import time
import BaseMotor

class A5988DriverMotor(BaseMotor.BaseMotor):
    """
    This Motor is connected to a a5988 driver, which only needs two pins
    to control the motor

    dir
    step
    enable

    reset should be wired to low
    sense should be wired to low
    """

    def __init__(self, step_pin, dir_pin, enable_pin, int max_position, int min_position, double delay, int sos_exception=False):
        """
        this is a direction and step interface

        max_position
        min_position
        delay between phase changes in seconds
        """
        BaseMotor.BaseMotor.__init__(self, max_position, min_position, delay, sos_exception)
        self.enable_pin = enable_pin
        self.step_pin = step_pin
        self.dir_pin = dir_pin
        # power on
        self.enable()

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
        # driver triggers LOW - HIGH impulse
        self.step_pin.output(1)
        # duty cycle of 1ms to hold high level of pulse
        time.sleep(0.001)
        self.step_pin.output(0)

    def unhold(self):
        """
        TODO: sleep or enable pin should be set on this function,
        to power off stepper motors
        """
        self.enable_pin.output(1)

    def enable(self):
        """
        set enable to low to activate driver board
        """
        self.enable_pin.output(0)
