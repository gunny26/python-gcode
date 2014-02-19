#/usr/bin/python
# -*- coding: utf-8 -*-
#
# parse Gcode
#
"""
inspired by instructable project

Module to control a two axis laser engraver
X/Y stepper motor controlled transport of laser head on Z axis
if Z is non-zero laser is powered on

alternatively laser could also trigger with spindle,
but your gcode has to support this
"""
import sys
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
#from GcodeGuiPygame import GcodeGuiPygame as GcodeGuiPygame
from LaserSimulator import LaserSimulator as LaserSimulator
# from GcodeGuiConsole import GcodeGuiConsole as GcodeGuiConsole
from Parser import Parser as Parser
from Controller import ControllerExit as ControllerExit
from Motor import BipolarStepperMotor as BipolarStepperMotor
from Motor import LaserMotor as LaserMotor
from Spindle import Spindle as Spindle
from Controller import Controller as Controller
from Transformer import Transformer as Transformer

def main(): 
    if len(sys.argv) == 1:
        sys.argv.append("examples/tiroler_adler.ngc")
    # bring GPIO to a clean state
    GPIO.cleanup()
    GPIO.setmode(GPIO.BCM)
    try:
        logging.info("Initialize GPIO")
        # enable pin for L293D IC
        GPIO.setup(23, GPIO.OUT)
        GPIO.output(23, 1)
        # laser power off
        GPIO.setup(14, GPIO.OUT)
        GPIO.output(14, 0)
        # build our controller
        logging.info("Creating Controller Object")
        controller = Controller(resolution=512/36, default_speed=1.0, delay=0.0)
        controller.add_motor("X", BipolarStepperMotor(coils=(4, 2, 27, 22), max_position=512, min_position=0, delay=0.0))
        controller.add_motor("Y", BipolarStepperMotor(coils=(24, 25, 7, 8), max_position=512, min_position=0, delay=0.0))
        controller.add_motor("Z", LaserMotor(laser_pin=14, min_position=-10000, max_position=10000, delay=0.0))
        controller.add_spindle(Spindle())
        controller.add_transformer(Transformer())
        # create parser
        logging.info("Creating Parser Object")
        parser = Parser(filename=sys.argv[1])
        parser.set_controller(controller)
        # create gui
        logging.info("Creating GUI")
        gui = LaserSimulator(automatic=True, zoom=10.0, controller=controller, parser=parser)
        # gui = GcodeGuiConsole()
        #gui.set_controller(controller)
        controller.set_gui_cb(gui.controller_cb)
        #gui.set_parser(parser)
        parser.set_gui_cb(gui.parser_cb)
        # start
        logging.info("Please move stepper motors to origin (0, 0, 0)")
        #key = raw_input("Press any KEY when done")
        parser.read()
    except ControllerExit, exc:
        logging.info(exc)
    except StandardError, exc:
        logging.exception(exc)
    GPIO.output(23, 0)
    GPIO.output(14, 0)
    GPIO.cleanup()

if __name__ == "__main__":
    main()
    sys.exit(0)
    import cProfile
    import pstats
    import trace
    #profile = "Tracer.profile"
    #cProfile.runctx( "main()", globals(), locals(), filename=profile)
    #s = pstats.Stats(profile)
    #s.sort_stats('time')
    #s.print_stats()
    #key = raw_input("Press any key")
    tracer = trace.Trace( 
        ignoredirs = [sys.prefix, sys.exec_prefix], 
        trace = 0) 
    tracer.run("main()")
    r = tracer.results() 
    r.write_results(show_missing=True, coverdir="LaserEngraver")
