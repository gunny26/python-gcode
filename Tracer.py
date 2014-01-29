#/usr/bin/python
# -*- coding: utf-8 -*-
#
# parse Gcode
#

import logging
logging.basicConfig(level=logging.INFO, format="%(message)s")
try:
    import RPi.GPIO as GPIO
except ImportError:
    logging.error("Semms not be a RaspberryPi")
    from  FakeGPIO import FakeGPIO as GPIO
import sys
import re
import inspect
import pygame
#import time
import trace
import cProfile
# own modules
from Motor import Motor as Motor
from Motor import BipolarStepperMotor as BipolarStepperMotor
from Motor import LaserMotor as LaserMotor
from Spindle import Spindle as Spindle
from Spindle import Laser as Laser
from Controller import Controller as Controller
from GcodeParser import Parser as Parser

# wait for keypress, or wait amount of time
AUTOMATIC = None
AUTOMATIC = 0.01
# pygame Zoom faktor
ZOOM = 4


def safe_position():
    for pin in (4, 2, 27, 22, 23, 14, 24, 25, 7, 8):
        GPIO.setup(pin, GPIO.OUT)
        GPIO.output(pin, 0)

def main(): 
    # bring GPIO to a clean state
    GPIO.cleanup()
    GPIO.setmode(GPIO.BCM)
    try:
        logging.info("Initializing all GPIO Pins, and set state LOW")
        safe_position()
        logging.info("Please move positions to origin")
        logging.info("Initialize GPIO Modes")
        GPIO.setup(23, GPIO.OUT)
        GPIO.output(23, 1)
        GPIO.setup(14, GPIO.OUT)
        GPIO.output(14, 0)
        pygame.init()
        surface = pygame.display.set_mode((530, 530))
        surface.fill((0, 0, 0))
        pygame.display.flip()
        parser = Parser(surface=None)
        parser.read()
    except Exception, exc:
        logging.exception(exc)
        safe_position()
        GPIO.cleanup()
    pygame.quit()

if __name__ == "__main__":
    import cProfile
    import pstats
    profile = "Tracer.profile"
    cProfile.runctx( "main()", globals(), locals(), filename=profile)
    s = pstats.Stats(profile)
    s.sort_stats('tottime')
    s.print_stats()
    key = raw_input("Press any key")
    tracer = trace.Trace( 
        ignoredirs = [sys.prefix, sys.exec_prefix], 
        trace = 0) 
    tracer.run("main()")
    r = tracer.results() 
    r.write_results(show_missing=True, coverdir="ergebnis1")
