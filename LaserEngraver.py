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
#import pyximport
#pyximport.install()
import sys
import logging
logging.basicConfig(level=logging.INFO, format="%(message)s")
try:
    import RPi.GPIO as GPIO
    #import GpioObject
    #GPIO = GpioObject(GpioObject.BOARD)
except ImportError:
    logging.error("Semms not to be a RaspberryPi")
    import FakeGPIO as GPIO
# own modules
from GPIOWrapper import GPIOWrapper as gpio
#from GcodeGuiTkinter import GcodeGuiTkinter as GcodeGuiTkinter
#from GcodeGuiPygame import GcodeGuiPygame as GcodeGuiPygame
#from GcodeGuiPygame import GcodeGuiPygame as GcodeGuiPygame
from LaserSimulator import LaserSimulator
# from GcodeGuiConsole import GcodeGuiConsole as GcodeGuiConsole
from Parser import Parser
#import ControllerExit
from BipolarStepperMotor import BipolarStepperMotor
from LaserMotor import LaserMotor
from BaseSpindle import BaseSpindle
from Controller import Controller
from Transformer import Transformer

def main(): 
    if len(sys.argv) == 1:
        sys.argv.append("examples/tiroler_adler.ngc")
    # STEP 1 - GPIO Initialization
    # bring GPIO to a clean state
    try:
        GPIO.cleanup_existing()
    except AttributeError:
        pass
    GPIO.setmode(GPIO.BOARD)
    # define GPIO Pins to use
    enable_pin = gpio(23, GPIO)
    enable_pin.setup(GPIO.OUT)
    laser_pin = gpio(14, GPIO)
    laser_pin.setup(GPIO.OUT)
    m_a_a1 = gpio(4, GPIO)
    m_a_a1.setup(GPIO.OUT)
    m_a_a2 = gpio(2, GPIO)
    m_a_a2.setup(GPIO.OUT)
    m_a_b1 = gpio(27, GPIO)
    m_a_b1.setup(GPIO.OUT)
    m_a_b2 = gpio(22, GPIO)
    m_a_b2.setup(GPIO.OUT)
    m_b_a1 = gpio(24, GPIO)
    m_b_a1.setup(GPIO.OUT)
    m_b_a2 = gpio(25, GPIO)
    m_b_a2.setup(GPIO.OUT)
    m_b_b1 = gpio(7, GPIO)
    m_b_b1.setup(GPIO.OUT)
    m_b_b2 = gpio(8, GPIO)
    m_b_b2.setup(GPIO.OUT)
    logging.info("Initialize GPIO")
    # enable pin for L293D Chip
    enable_pin.output(1)
    # laser power off
    laser_pin.output(0)
    # STEP 2 - create Objects and connect them
    # build our controller
    logging.info("Creating Controller Object")
    controller = Controller(resolution=512/36, default_speed=1.0, autorun=False)
    controller.add_motor("X", BipolarStepperMotor(coils=(m_a_a1, m_a_a2, m_a_b1, m_a_b2), max_position=512, min_position=0, delay=0.002))
    controller.add_motor("Y", BipolarStepperMotor(coils=(m_b_a1, m_b_a2, m_b_b1, m_b_b2), max_position=512, min_position=0, delay=0.002))
    controller.add_motor("Z", LaserMotor(laser_pin=laser_pin, min_position=-10000, max_position=10000, delay=0.00))
    controller.add_spindle(Spindle())
    controller.add_transformer(Transformer())
    # create parser
    logging.info("Creating Parser Object")
    parser = Parser(filename=sys.argv[1], autorun=False)
    parser.set_controller(controller)
    # create gui
    logging.info("Creating GUI")
    gui = LaserSimulator(automatic=True, zoom=10.0, controller=controller, parser=parser)
    # gui = GcodeGuiConsole()
    controller.set_gui_cb(gui.controller_cb)
    parser.set_gui_cb(gui.parser_cb)
    # start
    logging.info("Please move stepper motors to origin (0, 0, 0)")
    #key = raw_input("Press any KEY when done")
    # STEP 3 - run 
    # this is usually done from
    try:
        parser.read()
        #key = raw_input("Parsing done, press Return to call controller")
        parser.run()
        #key = raw_input("Controller calculations done, press Return to move")
        controller.run()
        key = raw_input("Controller calculations done, press Return to move")
    except ControllerExit as exc:
        logging.info(exc)
    except Exception as exc:
        logging.exception(exc)
    except KeyboardInterrupt as exc:
        logging.exception(exc)
    # STEP 4 - shutdown
    # inidcate gui to quit
    gui.stop_flag = True
    # cleanup gpio
    GPIO.cleanup()

if __name__ == "__main__":
    main()
    sys.exit(0)
    import cProfile
    import pstats
    profile = "Tracer.profile"
    cProfile.runctx( "main()", globals(), locals(), filename=profile)
    s = pstats.Stats(profile)
    s.sort_stats('time')
    s.print_stats()
    #key = raw_input("Press any key")
    #import trace
    #tracer = trace.Trace( 
    #    ignoredirs = [sys.prefix, sys.exec_prefix], 
    #    trace = 0) 
    #tracer.run("main()")
    #r = tracer.results() 
    #r.write_results(show_missing=True, coverdir="LaserEngraver")
