#!/usr/bin/python
# cython: profile=True
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

    def setup(self, int mode):
        #logging.debug("setup(%s) called" % mode)
        self.gpio.setup(self.pin, mode)

    def output(self, int value):
        #logging.debug("output(%s) called" % value)
        self.gpio.output(self.pin, value)

    def input(self):
        #logging.debug("input() called")
        return(self.gpio.input(self.pin))
