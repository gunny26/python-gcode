#!/usr/bin/python
"""
Object Interface to GPIO Calls of one pin
"""

cdef class GPIOWrapper(object):
    """GPIO Object"""
   
    cdef int pin
    cdef object gpio

    def __cinit__(self, int pin, object gpio):
        """pin to use"""
        self.pin = pin
        self.gpio = gpio

    cpdef int setup(self, int mode):
        self.gpio.setup(self.pin, mode)
        return(0)

    cpdef int output(self, int value):
        self.gpio.output(self.pin, value)
        return(0)

    cpdef int input(self):
        return(self.gpio.input(self.pin))
