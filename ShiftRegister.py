#!/usr/bin/python

try:
    import RPi.GPIO as GPIO
except ImportError:
    from FakeGPIO import FakeGPIO as GPIO
import logging
logging.basicConfig(level=logging.DEBUG)


class ShiftGPIOWrapper(object):
    """
    interface for GPIO like calls to ShiftRegister
    should be used instead original GPIO Module to set corresponding bit in shift register
    """

    def __init__(self, shift_register, bit):
        self.shift_register = shift_register
        self.bit = bit
        self.value = 0

    def is_shiftwrapper(self):
        """indicates that this class is a wrapper object"""
        return(True)

    def setup(self, mode):
        """
        all pins in shift register are output only
        """
        assert mode == GPIO.OUT

    def output(self, value):
        """output value on this bit"""
        assert value == 0 or value == 1
        self.value = value
        self.shift_register.set_value(self.bit, self.value)

    def input(self, value):
        """not realy input, only returns last value set"""
        return(self.bit)


class ShiftRegister(object):
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

    def __init__(self, ser, rclk, srclk, bits, autocommit=False):
        """
        ser -> GPIO Pin used for SER
        rclk -> GPIO Pin used for RCLK
        srclk -> GPIO Pin used for SRCLK
        pins -> the amount of pins or bits to use, every single 74hc595 counts for 8 bits,
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
        # initialize GPIO
        self.ser.setup(GPIO.OUT)
        self.rclk.setup(GPIO.OUT)
        self.srclk.setup(GPIO.OUT)
        # set these two guys to high
        self.rclk.output(1)
        self.srclk.output(1)

    def unhold(self):
        """
        set anything to low, so no power is consumed
        """
        self.rclk.output(0)
        self.srclk.output(0)
        self.ser.output(0)

    def set_value(self, pos, value):
        """
        set value for bit at position pos
        """
        if value == 1:
            self._set_bit(pos)
        else:
            self._clear_bit(pos)
        if self.autocommit is True:
            self.write()

    def _set_bit(self, pos):
        """set pin at position pos starting by 0"""
        assert pos < self.bits
        mask = 1 << pos
        self.binary = self.binary | mask
        assert self.binary < self.overflow

    def _clear_bit(self, pos):
        assert pos < self.bits
        mask = ~(1 << pos)
        self.binary = self.binary & mask
        assert self.binary < self.overflow
        if self.autocommit is True:
            self.write()

    def get_bit(self, pos):
        assert pos < self.bits
        mask = 1 << pos
        if self.binary & mask > 0:
            return(1)
        return(0)

    def write(self):
        """push bit register to chip and enable output"""
        self.rclk.output(0)
        bit = self.bits
        while bit > 0:
            bit -= 1
            self.srclk.output(0)
            self.ser.output(self.get_bit(bit))
            self.srclk.output(1)
        self.rclk.output(1)
        #logging.error(self.dump())
            
    def clear(self):
        """set internal bit representation to zero"""
        self.binary = 0
        if self.autocommit is True:
            self.write()

    def dump(self):
        """dump internal state, debugging only"""
        sb = []
        bit = self.bits
        while bit > 0:
            bit -= 1
            if self.get_bit(bit):
                sb.append("1")
            else:
                sb.append("0")
        return(" ".join(sb))

def test():
    import time
    import sys
    from FakeGPIO import GPIOWrapper as gpio
    GPIO.setmode(GPIO.BCM)
    for pin in (23, 24, 25):
        print "setting GPIO %s to HIGH 1s and LOW 1s" % pin
        ser = gpio(pin, GPIO)
        ser.setup(GPIO.OUT)
        try:
            while True:
                ser.output(GPIO.HIGH)
                time.sleep(1)
                ser.output(GPIO.LOW)
                time.sleep(1)
        except KeyboardInterrupt:
            pass
    shift_register = ShiftRegister(gpio(23, GPIO), gpio(24, GPIO), gpio(25, GPIO), 16, autocommit=True)
    print "setting every bit, then clear, and reset"
    try:
        while True:
            for pin in range(16):
                shift_register.set_value(pin, 1)
                shift_register.dump()
                time.sleep(0.1)
            time.sleep(2)
            shift_register.clear()
    except KeyboardInterrupt:
        pass
    sys.exit(0)

if __name__ == "__main__":
    test()
