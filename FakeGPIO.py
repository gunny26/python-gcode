import logging
logging.basicConfig(level=logging.INFO)


class FakeGPIO(object):
    """use this class on non RaspberryPi"""

    BCM = True
    OUT = True
    IN = False
    HIGH = True
    LOW = False

    @staticmethod
    def setup(*args):
        #logging.error("setup(%s)", args)
        pass

    @staticmethod
    def output(*args):
        #logging.error("output(%s)", args)
        pass

    @staticmethod
    def input(*args):
        #logging.error("input(%s)", args)
        return(0)

    @staticmethod
    def cleanup(*args):
        #logging.error("cleanup(%s)", args)
        pass

    @staticmethod
    def setmode(*args):
        #logging.error("setmode(%s)", args)
        pass

    def __getattr__(self, name):
        def method(*args):
            logging.info("tried to handle unknown method " + name)
            if args:
                logging.info("it had arguments: " + str(args))
        return method

try:
    GPIO
except NameError:
    GPIO = FakeGPIO

class GPIOWrapper(object):
    """GPIO Object"""
   
    def __init__(self, pin, gpio):
        """pin to use"""
        self.pin = pin
        self.gpio = gpio

    def setup(self, mode):
        self.gpio.setup(self.pin, mode)

    def output(self, value):
        self.gpio.output(self.pin, value)

    def input(self):
        return(self.gpio.input(self.pin))

    def __getattr__(self, name):
        def method(*args):
            logging.info("tried to handle unknown method " + name)
            if args:
                logging.info("it had arguments: " + str(args))
        return method


