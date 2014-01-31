#/usr/bin/python
# -*- coding: utf-8 -*-
#
# parse Gcode
#

import sys
import logging
logging.basicConfig(level=logging.DEBUG, format="%(message)s")
try:
    import RPi.GPIO as GPIO
except ImportError:
    logging.error("Semms not to be a RaspberryPi")
    from  FakeGPIO import FakeGPIO as GPIO
# own modules
from GcodeGuiTkinter import GcodeGuiTkinter as GcodeGuiTkinter
from GcodeGuiPygame import GcodeGuiPygame as GcodeGuiPygame
from GcodeGuiConsole import GcodeGuiConsole as GcodeGuiConsole
from Parser import Parser as Parser
from Controller import ControllerExit as ControllerExit
from Motor import BipolarStepperMotor as BipolarStepperMotor
from Motor import LaserMotor as LaserMotor
from Spindle import Spindle as Spindle
from Controller import Controller as Controller

def main(): 
    # bring GPIO to a clean state
    GPIO.cleanup()
    GPIO.setmode(GPIO.BCM)
    try:
        logging.info("Initialize GPIO Modes")
        GPIO.setup(23, GPIO.OUT)
        GPIO.output(23, 1)
        GPIO.setup(14, GPIO.OUT)
        GPIO.output(14, 0)
        # build our controller
        logging.info("Creating Controller Object")
        controller = Controller(resolution=512/36, default_speed=1.0, delay=0.0)
        controller.add_motor("X", BipolarStepperMotor(coils=(4, 2, 27, 22), max_position=512, min_position=0, delay=0.0))
        controller.add_motor("Y", BipolarStepperMotor(coils=(24, 25, 7, 8), max_position=512, min_position=0, delay=0.0))
        controller.add_motor("Z", LaserMotor(laser_pin=14, min_position=-10000, max_position=10000, delay=0.0))
        controller.add_spindle(Spindle())
        # create parser
        logging.info("Creating Parser Object")
        if len(sys.argv) == 1:
            sys.argv.append("examples/Coaster.ngc")
        parser = Parser(filename=sys.argv[1])
        parser.set_controller(controller)
        # create gui
        logging.info("Creating GUI")
        gui = GcodeGuiPygame(automatic=True)
        # gui = GcodeGuiTkinter()
        gui.set_controller(controller)
        controller.set_gui_cb(gui.controller_cb)
        gui.set_parser(parser)
        parser.set_gui_cb(gui.parser_cb)
        # start
        logging.info("Please move stepper motors to origin (0, 0, 0)")
        key = raw_input("Press any KEY when done")
        parser.read()
    except ControllerExit, exc:
        logging.info(exc)
    except StandardError, exc:
        logging.exception(exc)
    GPIO.cleanup()

if __name__ == "__main__":
    main()
