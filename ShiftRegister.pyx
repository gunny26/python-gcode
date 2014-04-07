#!/usr/bin/python
# cython: profile=True

import logging
logging.basicConfig(level=logging.DEBUG)

cdef class ShiftRegister(object):
    """
    Class to controll shift register array based on 74hc595 logic ic
    from raspberry to first shift register chip, we only need three lines
    SER -> actual value HIGH or LOW
    RCLK -> shift register to the left
    SRCLK -> swap output state with state in register, to enable settings
    
    VCC and GND are also needed
    for a very good explanation on how to work with shift registers look at
    http://bildr.org/2011/02/74hc595/
    """

    cdef object ser
    cdef object rclk
    cdef object srclk
    cdef int bits
    cdef int autocommit
    cdef int binary
    cdef int overflow

    def __init__(self, object ser, object rclk, object srclk, int bits, int autocommit=False):
        """
        ser -> GpioObject used for SER
        rclk -> GpioObject used for RCLK
        srclk -> GpioObject used for SRCLK
        bits -> the amount of pins or bits to use, every single 74hc595 counts for 8 bits,
                so two chips in chain and pins should be 16

        autocommit indicates if every bit change should be pushed to shift register,
        or the push to shift register schould be explicit by calling write()
        the last is faster and more efficient
        """
        self.ser = ser
        self.rclk = rclk
        self.srclk = srclk
        self.bits = bits
        self.autocommit = autocommit
        # initial binary value
        self.binary = 0
        self.overflow = 1 << self.bits
        # set these two guys to high
        self.rclk.output(True)
        self.srclk.output(True)

    def unhold(self):
        """
        set anything to low, so no power is consumed
        """
        self.rclk.output(False)
        self.srclk.output(False)
        self.ser.output(False)

    def set_bit(self, int pos, int value):
        """
        set bit on position <pos> to value <value>
        value should be type bool
        """
        if value is True:
            self._set(pos)
        else:
            self._unset(pos)
        if self.autocommit is True:
            self._write()

    def _set(self, int pos):
        """
        set bit at position pos to HIGH(1) 
        pos starting by 0
        pos has to be lower than self.bits
        """
        assert pos < self.bits
        cdef int mask = 1 << pos
        self.binary = self.binary | mask
        assert self.binary < self.overflow

    def _unset(self, int pos):
        """
        set bit at position pos to LOW(0)
        pos starting at 0
        """
        assert pos < self.bits
        cdef int mask = ~(1 << pos)
        self.binary = self.binary & mask
        assert self.binary < self.overflow

    def get_bit(self, int pos):
        """
        return bit at position <pos> type <bool>
        """
        assert pos < self.bits
        cdef int mask = 1 << pos
        if self.binary & mask > 0:
            return(True)
        return(False)

    def commit(self):
        self._write()

    def _write(self):
        """
        push bit register to chip and enable output
        """
        self.rclk.output(False)
        cdef int pos = self.bits
        while pos > 0:
            pos -= 1
            self.srclk.output(False)
            self.ser.output(self.get_bit(pos))
            self.srclk.output(True)
        self.rclk.output(True)
            
    def clear(self):
        """
        set all bits to zero
        """
        self.binary = 0
        if self.autocommit is True:
            self._write()

    def dump(self):
        """
        dump internal state as string 
        debugging only"""
        sb = []
        cdef int bit = self.bits
        while bit > 0:
            bit -= 1
            if self.get_bit(bit):
                sb.append("1")
            else:
                sb.append("0")
        return(" ".join(sb))
