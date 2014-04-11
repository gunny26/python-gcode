#/usr/bin/python
# -*- coding: utf-8 -*-
#
# parse Gcode
#
#cython: profile=True
"""
Motor Classes for Controller
"""

import logging
logging.basicConfig(level=logging.INFO, format="%(message)s")
import time

cdef class BaseMotor(object):
    """
    Base - Class for Motors
    usually you have to overwrite __move and unhold methods
    """

    cdef public tuple SEQUENCE_LOW
    cdef public tuple SEQUENCE_HIGH
    cdef public tuple SEQUENCE_MIXED
    cdef public tuple SEQUENCE
    cdef int max_position
    cdef int min_position
    cdef double delay
    cdef int sos_exception
    cdef public int position
    cdef double float_position
    cdef double last_step_time

    def __init__(self, max_position, min_position, delay, sos_exception):
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
        # low torque mode - also low power as only one coil is powered
        self.SEQUENCE_LOW = ((1, 0, 0, 0), (0, 0, 1, 0), (0, 1, 0, 0), (0, 0, 0, 1))
        # high torque - full step mode
        self.SEQUENCE_HIGH = ((1, 0, 1, 0), (0, 1, 1, 0), (0, 1, 0, 1), (1, 0, 0, 1))
        # mixed torque - half step mode
        self.SEQUENCE_MIXED = ((1, 0, 0, 0), (1, 0, 1, 0), (0, 0, 1, 0), (0, 1, 1, 0), (0, 1, 0, 0), (0, 1, 0, 1), (0, 0, 0, 1), (1, 0, 0, 1))
        # ok
        self.SEQUENCE = self.SEQUENCE_MIXED


    cpdef int move_float(self, int direction, double float_step):
        """
        this method is called from controller
        float_step is bewtween 0.0 < 1.0
        @param
        direction -> inidcates which direction stepper should move
        float_steps -> what fraction of a single step should be moved
            internally a step is only initialized if a full step is reached
        """
        cdef double temp
        cdef double time_gap
        cdef double distance
        #logging.debug("move_float called with %d, %f", direction, float_step)
        # boundary check
        temp = self.float_position + float_step * direction
        if not (self.min_position <= temp <= self.max_position):
            if self.sos_exception is True:
                raise(StandardError("Boundary reached: %s < %s < %s not true" % (self.min_position, temp, self.max_position)))
            else:
                logging.error("%s < %s < %s not true", self.min_position, temp, self.max_position)
                # dont move any further
                return(0)
        # next step should not before self.last_step_time + self.delay
        time_gap = self.last_step_time + self.delay - time.time()
        if time_gap > 0:
            time.sleep(time_gap)
        # boundary check ok, waited for stepper interleave, lets rock
        self.float_position = temp
        distance = abs(self.position - self.float_position)
        # move only if distance is > 1
        # distance should never be more than 2
        if distance >= 1.0:
            self._move(direction)
        # remember last_step_time
        self.last_step_time = time.time()
        return(0)

    cdef int _move(self, int direction):
        """
        move number of full integer steps
        """
        self.position += direction
        return(0)

    cdef int unhold(self):
        """release power"""
        return(0)

    cpdef int get_position(self):
        """return real position as int"""
        return(self.position)

    cdef double get_float_position(self):
        """return exact position as float"""
        return(self.float_position)

