#!/usr/bin/python

cdef class ShiftGPIOWrapper(object):
    """
    interface for GPIO like calls to ShiftRegister Bits
    should be used instead original GPIO Module to 
    set corresponding bit in shift register
    """

    cdef object shift_register
    cdef int bitnumber

    def __init__(self, object shift_register, int bitnumber):
        """
        GPIO like Interface to one bit of shift register given
        <shift_register> isInstanceOf ShiftRegister
        <bit> which bit in ShiftRegister type <int>
        """
        self.shift_register = shift_register
        self.bitnumber = bitnumber

    cpdef int setup(self, int mode):
        """
        all pins in shift register are output only
        """
        return(0)

    cpdef int output(self, int value):
        """
        output value on this bit
        and call ShiftRegister.set_value method
        """
        self.shift_register.set_bit(self.bitnumber, value)
        return(0)

    cpdef int input(self):
        """not realy input, returns only self.bitnumber"""
        return(self.bitnumber)
