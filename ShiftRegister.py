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

    def __init__(self, ser, rclk, srclk, pins, autocommit=False):
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
        self.pins = pins
        self.autocommit = autocommit
        # initial binary value
        self.binary = 0
        self.overflow = 1 << pins
        # initialize GPIO
        self.ser.setup(GPIO.OUT)
        self.rclk.setup(GPIO.OUT)
        self.srclk.setup(GPIO.OUT)
        # set these two guys to high
        self.rclk.output(GPIO.HIGH)
        self.srclk.output(GPIO.HIGH)

    def set_value(self, pos, value):
        """
        set value for bit at position pos
        """
        if value == 1:
            self.set_bit(pos)
        else:
            self.clear_bit(pos)

    def set_bit(self, pos):
        """set pin at position pos starting by 0"""
        assert pos < self.pins
        mask = 1 << pos
        self.binary = self.binary | mask
        assert self.binary < self.overflow
        if self.autocommit is True:
            self.write()

    def clear_bit(self, pos):
        assert pos < self.pins
        mask = ~(1 << pos)
        self.binary = self.binary & mask
        assert self.binary < self.overflow
        if self.autocommit is True:
            self.write()

    def get_bit(self, pos):
        assert pos < self.pins
        mask = 1 << pos
        if self.binary & mask > 0:
            return(True)
        return(False)

    def write(self):
        """push bit register to chip and enable output"""
        self.rclk.output(GPIO.LOW)
        for bit in range(self.pins):
            mask = 1 << bit
            value = 0
            if (self.binary & mask) > 0:
                value = 1
            self.srclk.output(GPIO.LOW)
            self.ser.output(value)
            self.srclk.output(GPIO.HIGH)
        self.rclk.output(GPIO.HIGH)
        # logging.error(self.dump())
            
    def clear(self):
        """set internal bit representation to zero"""
        self.binary = 0

    def dump(self):
        """dump internal state, debugging only"""
        sb = []
        bit = 16
        while bit > 0:
            bit -= 1
            if self.get_bit(bit):
                sb.append("1")
            else:
                sb.append("0")
        return(" ".join(sb))

def test():
    from FakeGPIO import GPIOWrapper as gpio
    shift_register = ShiftRegister(gpio(23), gpio(24), gpio(25), 16, autocommit=True)
    for pin in range(16):
        shift_register.set_value(pin, 1)
        shift_register.dump()
    shift_register.write()
    shift_register.clear()
    test_gpio = ShiftGPIOWrapper(shift_register, 1)
    test_gpio.output(GPIO.HIGH)
    test_gpio.output(GPIO.LOW)
    test_gpio.output(GPIO.HIGH)
    test_gpio.output(GPIO.LOW)

if __name__ == "__main__":
    test()
