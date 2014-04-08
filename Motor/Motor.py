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

class Motor(object):
    """
    Base - Class for Motors
    usually you have to overwrite __move and unhold methods
    """

    # low torque mode - also low power as only one coil is powered
    SEQUENCE_LOW = ((1, 0, 0, 0), (0, 0, 1, 0), (0, 1, 0, 0), (0, 0, 0, 1))
    # high torque - full step mode
    SEQUENCE_HIGH = ((1, 0, 1, 0), (0, 1, 1, 0), (0, 1, 0, 1), (1, 0, 0, 1))
    # mixed torque - half step mode
    SEQUENCE_MIXED = ((1, 0, 0, 0), (1, 0, 1, 0), (0, 0, 1, 0), (0, 1, 1, 0), (0, 1, 0, 0), (0, 1, 0, 1), (0, 0, 0, 1), (1, 0, 0, 1))
    # ok
    SEQUENCE = SEQUENCE_MIXED

    def __init__(self, max_position, min_position, delay, sos_exception=True):
        """
        max_position -> the maximum position this motor should reach in steps
        min_position -> the minimum position this motor should reach in steps
        delay -> delay in seconds we wait between coil sequences
        sos_exception -> if boundary max_position or min_position are reached
            should a exception be raised, or only a warning should be logged
            in either case, this motor will NOT GET above or below boundary
        """
        self.max_position = max_position
        self.min_position = min_position
        self.delay = delay
        self.sos_exception = sos_exception
        # define float and integer position
        self.position = 0
        self.float_position = 0.0
        # timekeeping
        self.last_step_time = time.time()

    def move_float(self, direction, float_step):
        """
        this method is called from controller
        float_step is bewtween 0.0 < 1.0
        @param
        direction -> inidcates which direction stepper should move
        float_steps -> what fraction of a single step should be moved
            internally a step is only initialized if a full step is reached
        """
        #logging.debug("move_float called with %d, %f", direction, float_step)
        assert type(direction) == int
        assert (direction == -1) or (direction == 1)
        assert 0.0 <= float_step <= 1.0
        # boundary check
        temp = self.position + int(float_step * direction)
        if not (self.min_position <= temp <= self.max_position):
            if self.sos_exception is True:
                raise(StandardError("Boundary reached: %s < %s < %s not true" % (self.min_position, temp, self.max_position)))
            else:
                logging.error("%s < %s < %s not true", self.min_position, temp, self.max_position)
                # dont move any further
                return()
        # next step should not before self.last_step_time + self.delay
        time_gap = self.last_step_time + self.delay - time.time()
        if time_gap > 0:
            time.sleep(time_gap)
        self.float_position += (float_step * direction)
        distance = abs(self.position - self.float_position)
        if distance >= 1.0:
            #logging.debug("initializing full step, distance %s > 1.0", distance) 
            self._move(direction)
        #else:
            #logging.debug("distance %s to small to initialize full step", distance)
        # remember last_step_time
        self.last_step_time = time.time()
        distance = abs(self.float_position - self.position)
        #logging.debug("int_position = %d : float_position = %f : distance = %f", self.position, self.float_position, distance)
        # final distance between exact float and real int must be lesser than 1.0
        assert distance < 1.0

    def _move(self, direction):
        """
        move number of full integer steps
        """
        #logging.debug("Moving Motor One step in direction %s", direction)
        #logging.debug("Motor accuracy +/- %s", self.position - self.float_position)
        self.position += direction

    def unhold(self):
        """release power"""
        #logging.info("Unholding Motor Coils")
        pass

    def get_position(self):
        """return real position as int"""
        return(self.position)

    def get_float_position(self):
        """return exact position as float"""
        return(self.float_position)


class LaserMotor(Motor):
    """Laser Motor, reactive if axis moves negative"""

    def __init__(self, laser_pin, max_position, min_position, delay):
        """
        GPIO like Object for laser_pin
        max_position value
        min_position value
        delay between phase changes
        """
        Motor.__init__(self, max_position, min_position, delay)
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


class BipolarStepperMotor(Motor):
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
        Motor.__init__(self, max_position, min_position, delay, sos_exception)
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

class UnipolarStepperMotor(Motor):
    """
    Class to represent a unipolar stepper motor
    it could only with on one dimension, forward or backwards

    cloil -> set(a1, a2, b1, b2) of GPIO Pins where these connectors are patched
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
        coils a set of for GPIO like object to represent a1, a2, b1, b2 connection to motor
        max_position
        min_position
        delay between phase changes in seconds
        """
        Motor.__init__(self, max_position, min_position, delay, sos_exception)
        self.coils = coils
        # define coil pins as output
        self.num_sequence = len(self.SEQUENCE)
        self.unhold()

    def _move(self, direction):
        """
        move one step in direction
        """
        self.position += direction
        phase = self.SEQUENCE[self.position % self.num_sequence]
        counter = 0
        for pin in self.coils:
            pin.output(phase[counter])
            counter += 1

    def unhold(self):
        """
        sets any pin of motor to low, so no power is needed
        """
        for pin in self.coils:
            pin.output(0)
    
    def get_phase(self):
        """returns actual phase in sequence"""
        return(self.SEQUENCE[self.position % self.num_sequence])

class A5988DriverMotor(Motor):
    """
    This Motor is connected to a a5988 driver, which only needs to pins
    to control motor

    dir
    step
    """

    def __init__(self, step_pin, dir_pin, max_position, min_position, delay, sos_exception=False):
        """
        coils a set of for GPIO like object to represent a1, a2, b1, b2 connection to motor
        max_position
        min_position
        delay between phase changes in seconds
        """
        Motor.__init__(self, max_position, min_position, delay, sos_exception)
        self.step_pin = step_pin
        self.dir_pin = dir_pin
        # define coil pins as output
        self.unhold()

    def _move(self, direction):
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
