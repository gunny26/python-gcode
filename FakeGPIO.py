class FakeGPIO(object):
    """use this class on non RaspberryPi"""

    BCM = True
    BOARD = False
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
