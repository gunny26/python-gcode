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
        pass

    @staticmethod
    def output(*args):
        pass

    @staticmethod
    def input(*args):
        return(0)

    @staticmethod
    def cleanup(*args):
        pass

    @staticmethod
    def setmode(*args):
        pass

    def __getattr__(self, name):
        def method(*args):
            logging.info("tried to handle unknown method " + name)
            if args:
                logging.info("it had arguments: " + str(args))
        return method

