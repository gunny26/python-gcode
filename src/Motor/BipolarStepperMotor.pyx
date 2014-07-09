#/usr/bin/python
# -*- coding: utf-8 -*-
#
# parse Gcode
#
"""
Motor Classes for Controller
"""

import BaseMotor

class BipolarStepperMotor(BaseMotor.BaseMotor):
    """
    Class to represent a bipolar stepper motor
    it could only with on one dimension, forward or backwards

    coil -> set(a1, a2, b1, b2) of GPIO Pins where these connectors are patched
    delay -> int(milliseconds to wait between moves
    max_position -> int(maximum position) is set to safe value of 1
    min_position -> int(minimum position) is set to 0
        b1
    a1      a1
        b2

    following seuqnece is possible (a1, a2, b1, b2)

    low torque mode
    1 0 0 0 a1
    0 0 1 0 b1
    0 1 0 0 a2
    0 0 0 1 b2
    
    high torque mode - full step mode
    1 0 1 0 between a1/b1
    0 1 1 0 between b1/a2
    0 1 0 1 between a2/b2
    1 0 0 1 between b2/a1

    mixed torque mode - half step mode
    1 0 0 0 a1
    1 0 1 0 between a1/b1
    0 0 1 0 b1
    0 1 1 0 between b1/a2
    0 1 0 0 a2
    0 1 0 1 between a2/b2
    0 0 0 1 b2
    1 0 0 1 between b2/a1

    """

    def __init__(self, coils, max_position, min_position, delay, sos_exception=False):
        """
        coils a set of four GPIO like objects to represent a1, a2, b1, b2 connection to motor
        max_position
        min_position
        """
        BaseMotor.BaseMotor.__init__(self, max_position, min_position, delay, sos_exception)
        self.coils = coils
        # define coil pins as output
        self.num_sequence = len(self.SEQUENCE)
        self.unhold()

    def _move(self, direction):
        """
        move one step in direction
        """
        phase = self.SEQUENCE[self.position % self.num_sequence]
        counter = 0
        for pin in self.coils:
            pin.output(phase[counter])
            counter += 1
        self.position += direction

    def unhold(self):
        """
        sets any pin of motor to low, so no power is needed
        """
        for pin in self.coils:
            pin.output(0)

