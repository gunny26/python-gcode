#!/usr/bin/python
"""
Object Interface to GPIO Interfaces on raspberry PI
"""
import logging
logging.basicConfig(level=logging.DEBUG)
import os
import time

class GpioObject(object):

    # mapping between BOARD Numbering and Header Numbering
    BOARD_TO_HEADER = {
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
    BOARD_TO_BCM = {
        2 : 3,
        3 : 5,
        4 : 7,
        7 : 26,
        8 : 24,
        9 : 21,
        10 : 19,
        11 : 23,
        14 : 8,
        15 : 10,
        17 : 11,
        18 : 12,
        22 : 15,
        23 : 16,
        24 : 18,
        25 : 22,
        27 : 13,
    }
    # define some static values
    BCM_TO_BOARD = {}
    for key, value in BOARD_TO_BCM.items():
        BCM_TO_BOARD[value] = key
    # these numbers only are used for sysfs calles
    BOARD_NUMBERS = BOARD_TO_BCM.keys()
    BCM_NUMBERS = BCM_TO_BOARD.keys()
    EXPORT_SYMLINKS = list(("gpio%d" % pin for pin in BOARD_NUMBERS))

    LOW = 0
    HIGH = 1
    OUT = 1
    IN = 0
    BOARD = 0
    BCM = 1

    def __init__(self, mode):
        """mode could be either GPIOObject.BOARD or GPIOObject.BCM"""
        assert type(mode) == int
        assert mode == self.BCM or mode == self.BOARD
        self.mode = mode
        self.setmode(mode)
        self.modes = {}
        if not os.path.exists("/sys/class/gpio"):
            raise ImportError("/sys/class/gpio not found, seems not be an raspberry, or gpio modules not loaded")

    def setmode(self, mode):
        assert type(mode) == int
        assert mode == self.BOARD or mode == self.BCM
        self.mode = mode

    def get_board_number(self, pin):
        """translate BCM to BOARD numbering if mode == BCM"""
        if self.mode == self.BCM:
            return(self.BCM_TO_BOARD[pin])
        else:
            return(pin)

    def setup(self, pin, direction):
        """set board pin to out or in
        direction is numeric IN or OUT and will be mapped
        0 : in
        1 : out
        """
        assert type(direction) == int
        assert direction == 0 or direction == 1
        assert type(pin) == int
        pin = self.get_board_number(pin)
        direction_str = "out"
        if direction == 0:
            direction_str = "in"
        if os.path.exists("/sys/class/gpio/gpio%d" % pin):
            logging.error("GPIO already exported")
            actual_direction_str = open("/sys/class/gpio/gpio%d/direction" % pin, "r").read().strip()
            logging.info("actual direction %s" % actual_direction_str)
            if actual_direction_str != direction_str:
                logging.error("Requested direction is not actual direction, unexport gpio first")
                return()
        if pin in self.modes:
            logging.error("Pin already enabled")
        else:
            self.sysfs_writer("/sys/class/gpio/export", str(pin))
        if not os.path.exists("/sys/class/gpio/gpio%d" % pin):
            logging.error("gpio directory symlink not created")
        self.sysfs_writer("/sys/class/gpio/gpio%d/direction" % pin, direction_str)
        fd = None
        if direction == 0:
            fd = os.open("/sys/class/gpio/gpio%d/value" % pin, os.O_RDONLY)
        elif direction == 1:
            fd = os.open("/sys/class/gpio/gpio%d/value" % pin, os.O_WRONLY | os.O_SYNC)
        self.modes[pin] = fd

    def output(self, pin, value):
        assert type(pin) == int
        assert type(value) == int
        assert value == 0 or value == 1
        pin = self.get_board_number(pin)
        assert pin in self.modes
        fd = self.modes[pin]
        os.write(fd, str(value))

    def input(self, pin):
        assert type(pin) == int
        pin = self.get_board_number(pin)
        assert pin in self.modes
        fd = self.modes[pin]
        value = os.read(fd, 1).strip()
        return(value)

    def gpio_function(self, pin):
        assert type(pin) == int
        pin = self.get_board_number(pin)
        assert pin in self.modes
        direction = open("/sys/class/gpio/gpio%d/direction" % pin).read().strip()
        return(direction)

    def dump_state(self):
        for pin, mode in self.modes.items():
            logging.info("%s : %s", pin, mode)

    def cleanup(self):
        for pin, mode in self.modes.items():
            self._cleanup(pin)

    def cleanup_existing(self):
        """cleanup all existing exported gpios"""
        for filename in os.listdir("/sys/class/gpio/"):    
            logging.info(filename)
            if filename in self.EXPORT_SYMLINKS:
                self._cleanup(int(filename[4:]))

    def cleanup_pin(self, pin):
        assert type(pin) == int
        pin = self.get_board_number(pin)
        self._cleanup(pin) 
    
    def _cleanup(self, pin):
        assert type(pin) == int
        logging.debug("cleanup(%d) called", pin)
        self.sysfs_writer("/sys/class/gpio/unexport", str(pin))
        starttime = time.time()
        duration = time.time() - starttime
        while os.path.exists("/sys/class/gpio/gpio%d" % pin) or duration > 60.0:
            duration = time.time() - starttime
            logging.debug("Wainting for exported gpio to vanish")
            time.sleep(0.1)
        if pin in self.modes:
            fd = self.modes[pin]
            os.close(fd)
            del self.modes[pin]

    def sysfs_writer(self, path, value):
        """subpath under /sys/class/gpio"""
        basepath = "/sys/class/gpio"
        fd = os.open(path, os.O_WRONLY | os.O_SYNC)
        os.write(fd, value)
        os.close(fd)

def test():
    GPIO = GpioObject
    gpio = GPIO(GPIO.BOARD)
    logging.info("cleanup_existing()")
    gpio.cleanup_existing()
    logging.info("cleanup()")
    gpio.cleanup()
    for pin in GPIO.BOARD_NUMBERS:    
        logging.info("setup(%d, GPIO.IN)", pin)
        gpio.setup(pin, GPIO.IN)
        logging.info(gpio.gpio_function(pin))
        logging.info("input(%d)", pin)
        logging.info(gpio.input(pin))
        logging.info("cleanup(%d)", pin)
        gpio.cleanup_pin(pin)
        logging.info("setup(%d, GPIO.OUT)", pin)
        gpio.setup(pin, GPIO.OUT)
        logging.info(gpio.gpio_function(pin))
        logging.info("output(GPIO.HIGH)")
        gpio.output(pin, GPIO.HIGH)
        gpio.output(pin, GPIO.LOW)
        logging.info("cleanup(%d)", pin)
        gpio.cleanup_pin(pin)
    gpio.cleanup()
    logging.info("Testing BCM Pin Numbering")
    gpio.setmode(GPIO.BCM)
    logging.info("cleanup_existing()")
    gpio.cleanup_existing()
    logging.info("cleanup()")
    gpio.cleanup()
    for pin in GPIO.BCM_NUMBERS:    
        logging.info("setup(%d, GPIO.IN)", pin)
        gpio.setup(pin, GPIO.IN)
        logging.info(gpio.gpio_function(pin))
        logging.info("input(%d)", pin)
        logging.info(gpio.input(pin))
        logging.info("cleanup(%d)", pin)
        gpio.cleanup_pin(pin)
        logging.info("setup(%d, GPIO.OUT)", pin)
        gpio.setup(pin, GPIO.OUT)
        logging.info(gpio.gpio_function(pin))
        logging.info("output(GPIO.HIGH)")
        gpio.output(pin, GPIO.HIGH)
        gpio.output(pin, GPIO.LOW)
        logging.info("cleanup(%d)", pin)
        gpio.cleanup_pin(pin)
    gpio.dump_state()

if __name__ == "__main__":
    test()
