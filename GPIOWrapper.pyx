#!/usr/bin/python
import logging
logging.basicConfig(level=logging.INFO)


cdef class GPIOWrapper(object):
    """GPIO Object"""
   
    cdef int pin
    cdef object gpio

    def __cinit__(self, int pin, object gpio):
        """pin to use"""
        self.pin = pin
        self.gpio = gpio

    cpdef int setup(self, int mode):
        #logging.debug("setup(%s) called" % mode)
        self.gpio.setup(self.pin, mode)
        return(0)

    cpdef int output(self, int value):
        #logging.debug("output(%s) called" % value)
        self.gpio.output(self.pin, value)
        return(0)

    cpdef int input(self):
        #logging.debug("input() called")
        return(self.gpio.input(self.pin))
