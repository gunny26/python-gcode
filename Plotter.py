#/usr/bin/python
# -*- coding: utf-8 -*-
#
# parse Gcode
#

import sys
import math
import logging
logging.basicConfig(level=logging.DEBUG, format="%(message)s")
try:
    import RPi.GPIO as GPIO
except ImportError:
    logging.error("Semms not to be a RaspberryPi")
    from  FakeGPIO import FakeGPIO as GPIO
# own modules
#from GcodeGuiTkinter import GcodeGuiTkinter as GcodeGuiTkinter
#from GcodeGuiPygame import GcodeGuiPygame as GcodeGuiPygame
from PlotterSimulator import PlotterSimulator as PlotterSimulator
from GcodeGuiConsole import GcodeGuiConsole as GcodeGuiConsole
from Parser import Parser as Parser
from Controller import ControllerExit as ControllerExit
from Motor import UnipolarStepperMotor as UnipolarStepperMotor
from Motor import UnipolarStepperMotorOnOff as UnipolarStepperMotorOnOff
from Motor import Motor as Motor
from Spindle import Spindle as Spindle
from Controller import Controller as Controller
from Transformer import PlotterTransformer as PlotterTransformer

def gpio_state():
    for gpio in (23, 24, 25, 8, 2, 3, 4, 27, 14, 15, 9, 7):
        GPIO.setup(gpio, GPIO.IN)
        print "%s = %s" % (gpio, GPIO.input(gpio))
        GPIO.setup(gpio, GPIO.OUT)
        GPIO.output(gpio, 0) 

def main(): 
    # bring GPIO to a clean state
    GPIO.cleanup()
    GPIO.setmode(GPIO.BCM)
    gpio_state()
    try:
        logging.info("Initialize GPIO Modes")
        # build our controller
        logging.info("Creating Controller Object")
        # one turn is 8 mm * pi in 48 steps, motor and screw specifications
        controller = Controller(resolution=8 * math.pi / 48, default_speed=1.0, delay=0.0)
        controller.add_motor("X", UnipolarStepperMotor(coils=(2, 3, 4, 27), max_position=9999, min_position=-9999, delay=0.002))
        controller.add_motor("Y", UnipolarStepperMotor(coils=(23, 24, 25, 8), max_position=9999, min_position=-9999, delay=0.002))
        # controller.add_motor("Z", UnipolarStepperMotorOnOff(coils=(14, 15, 9, 7), on_position=10, on_direction=0, delay=0.003))
        # controller.add_motor("Z", UnipolarStepperMotor(coils=(14, 15, 9, 7), max_position=20, min_position=0, delay=0.003))
        controller.add_motor("Z", Motor(min_position=-10000, max_position=10000, delay=0.0))
        controller.add_spindle(Spindle())
        controller.add_transformer(PlotterTransformer(width=1000, heigth=500, scale=20.0))
        # create parser
        logging.info("Creating Parser Object")
        if len(sys.argv) == 1:
            sys.argv.append("examples/tiroler_adler.ngc")
        parser = Parser(filename=sys.argv[1])
        parser.set_controller(controller)
        # create gui
        logging.info("Creating GUI")
        gui = PlotterSimulator(automatic=True)
        # gui = GcodeGuiPygame(automatic=True)
        # gui = GcodeGuiTkinter()
        # gui = GcodeGuiConsole()
        gui.set_controller(controller)
        controller.set_gui_cb(gui.controller_cb)
        gui.set_parser(parser)
        parser.set_gui_cb(gui.parser_cb)
        # start
        logging.info("Please move stepper motors to origin (0, 0, 0)")
        #key = raw_input("Press any KEY when done")
        parser.read()
    except ControllerExit, exc:
        logging.info(exc)
    except StandardError, exc:
        logging.exception(exc)
    gpio_state()
    GPIO.cleanup()

if __name__ == "__main__":
    main()
