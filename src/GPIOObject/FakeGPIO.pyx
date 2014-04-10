#!/usr/bin/python

class FakeGPIO(object):

    BCM = True
    BOARD = False
    OUT = True
    IN = False
    HIGH = True
    LOW = False

    @staticmethod
    def setup(*kwds):
        return(0)

    @staticmethod
    def output(*args):
        return(0)

    @staticmethod
    def input(*args):
        return(0)

    @staticmethod
    def cleanup(*args):
        return(0)

    @staticmethod
    def setmode(*args):
        return(0)
