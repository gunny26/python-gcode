#!/usr/bin/python

try:
    import RPi.GPIO as GPIO
except ImportError:
    from FakeGPIO import FakeGPIO as GPIO
import logging
logging.basicConfig(level=logging.DEBUG)


class ShiftRegister(object):

    def __init__(self, ser, rclk, srclk, pins, autocommit=False):
        """
        autocommit inidtaces if every bit change should be pushed to shift register,
        or the push to shift register schould be explicit by calling write()
        the latter is faster and more efficient
        """
        self.ser = ser
        self.rclk = rclk
        self.srclk = srclk
        self.pins = pins
        # initial binary value
        self.binary = 0
        self.overflow = 1 << pins
        # initialize GPIO
        GPIO.setup(self.ser, GPIO.OUT)
        GPIO.setup(self.rclk, GPIO.OUT)
        GPIO.setup(self.srclk, GPIO.OUT)
        # set these two guys to high
        GPIO.output(self.rclk, GPIO.HIGH)
        GPIO.output(self.srclk, GPIO.HIGH)

    def set_bit(self, pos, state):
        """set pin at position pos starting by 0"""
        assert pos < self.pins
        bit = state << pos
        self.binary = self.binary | bit
        assert self.binary < self.overflow

    def write(self):
        GPIO.output(self.rclk, GPIO.LOW)
        for bit in range(self.pins):
            mask = 1 << bit
            value = 0
            if (self.binary & mask) > 0:
                value = 1
            print "Setting %s on bit %s" % (value, bit)
            GPIO.output(self.srclk, GPIO.LOW)
            GPIO.output(self.ser, value)
            GPIO.output(self.srclk, GPIO.HIGH)
        GPIO.output(self.rclk, GPIO.HIGH)
            
    def clear(self):
        self.binary = 0

    def dump(self):
        """dump internal state"""
        print "%018s" % bin(self.binary)
        print "%18d" % self.binary

def test():
    sr = ShiftRegister(23, 24, 25, 16)
    for pin in range(16):
        sr.set_bit(pin, 1)
        sr.dump()
    sr.write()

if __name__ == "__main__":
    test()
