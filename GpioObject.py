#!/usr/bin/python
"""
Object Interface to GPIO Interfaces on raspberry PI
"""

class GPIOObject(object):

    # mapping between BOARD Numbering and Header Numbering
    BORAD_TO_HEADER = {
        "P1-01" : "VCC 3.3V", 
        "P1-02" : "VCC 5V",
        "P1-03" : "GPIO2",
        "P1-04" : "VCC 5V",
        "P1-05" : "GPIO3",
        "P1-06" : "GND",
        "P1-07" : "GPIO4",
        "P1-08" : "GPIO14",
        "P1-09" : "GND",
        "P1-10" : "GPIO15",
        "P1-11" : "GPIO17",
        "P1-12" : "GPIO18",
        "P1-13" : "GPIO27",
        "P1-14" : "GND",
        "P1-15" : "GPIO22",
        "P1-16" : "GPIO23",
        "P1-17" : "VCC 3.3V",
        "P1-18" : "GPIO24",
        "P1-19" : "GPIO10",
        "P1-20" : "GND",
        "P1-21" : "GPIO9",
        "P1-22" : "GPIO25",
        "P1-23" : "GPIO11",
        "P1-24" : "GPIO8",
        "P1-25" : "GND",
        "P1-26" : "GPIO7",
        "P5-01" : "VCC 5V",
        "P5-02" : "VCC 3.3V",
        "P5-03" : "GPIO28",
        "P5-04" : "GPIO29",
        "P5-05" : "GPIO30",
        "P5-06" : "GPIO31",
        "P5-07" : "GND",
        "P5-08" : "GND",

    }

    # mapping from BCM PIN Naming to Board Numbering
    BCM_TO_BOARD = {
        "GPIO2" : 3,
        "GPIO3" : 5,
        "GPIO4" : 7,
        "GPIO7" : 26,
        "GPIO8" : 24,
        "GPIO9" : 21,
        "GPIO10" : 19,
        "GPIO11" : 23,
        "GPIO14" : 8,
        "GPIO15" : 10,
        "GPIO17" : 11,
        "GPIO18" : 12,
        "GPIO22" : 15,
        "GPIO23" : 16,
        "GPIO24" : 18,
        "GPIO25" : 22,
        "GPIO27" : 13,
    }

    # define some static values
    LOW = 0
    HIGH = 1
    OUT = 1
    IN = 0
    BOARD = 0
    BCM = 1

    def __init__(self, mode):
        """mode could be either GPIOObject.BOARD or GPIOObject.BCM"""
        self mode = mode
        self.setmode(mode)
        self.modes = {}

    def setmode(self, mode):
        assert type(mode) == int
        assert mode == self.BOARD or mode == self.BCM

    def setup(self, pin, direction):
        """set board pin to out or in"""
        assert type(direction) == str
        assert direction == "out" or direction == "in"
        assert type(pin) == int
        assert pin < 26
        if pin in self.modes:
            logging.error("Pin already enabled")
        else:
            open("/sys/class/gpio/export", "wb").write(pin)
        open("/sys/class/gpio/gpio%d/direction" % pin, "wb").write(direction)
        self.modes[pin] = direction

    def output(self, pin, value):
        assert type(pin) == int
        assert pin < 26
        assert type(value) == int
        assert value == 0 or value == 1
        open("/sys/class/gpio/gpio%d/value" % pin, "wb").write(value)

    def input(self, pin):
        assert type(pin) == int
        assert pin < 26
        value = open("/sys/class/gpio/gpio%d/value" % pin, "rb").read()
        return(value)

    def cleanup(self):
        for pin, mode in self.modes.items():
            open("/sys/class/gpio/unexport", "wb").write(pin)

