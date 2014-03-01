#/usr/bin/python
# -*- coding: utf-8 -*-
#
# parse Gcode
#
"""
Inspired by Makelangelo, great work.

controlls plotter with two stepper motors and one pen stepper or servo motor

Stepper Motors A and B are mounted on top in the corner of the area/panel
Stepper or Servo Motor P is hanging on line between them

A-----------------B
 \               /
  \             /
   \           /
    \         /
    a\       /b 
      \     /
       \   /
        \ /
         P

so by controlling length a and b, the plotter is able to get to any position
on the area.

Normally any gcode is written for linear X/Y machine, so a special tranformer
is needed to calculate from X/Y motions to a/b motions.
"""
# cython imports, if installed
try:
    import pyximport
    pyximport.install()
except ImportError:
    pass
import sys
import math
import logging
logging.basicConfig(level=logging.DEBUG, format="%(message)s")
# FakeGPIO or real one, depends on hardware
try:
    #import RPi.GPIO as GPIO
    from GpioObject import GpioObject
    GPIO = GpioObject(GpioObject.BOARD)
except ImportError:
    logging.error("Semms not to be a RaspberryPi")
    from  FakeGPIO import FakeGPIO as GPIO
# own modules
# GPIO Warpper, object interface to GPIO Ports
from FakeGPIO import GPIOWrapper as gpio
from ShiftRegister import ShiftRegister as ShiftRegister
from ShiftRegister import ShiftGPIOWrapper as ShiftGPIOWrapper
# from PlotterSimulator import PlotterSimulator as PlotterSimulator
from GcodeGuiConsole import GcodeGuiConsole as GcodeGuiConsole
from Parser import Parser as Parser
from Controller import ControllerExit as ControllerExit
from Motor import UnipolarStepperMotor as UnipolarStepperMotor
from Spindle import Spindle as Spindle
from Controller import Controller as Controller
from Transformer import PlotterTransformer as PlotterTransformer

def main(): 
    # if no parameter option is given, default to example gcode
    if len(sys.argv) == 1:
        sys.argv.append("examples/tiroler_adler.ngc")
    # bring GPIO to a clean state
    GPIO.cleanup_existing()
    GPIO.setmode(GPIO.BOARD)
    # we use GPIO Wrapper, object like interface to real GPIO Module
    ser = gpio(23, GPIO)
    ser.setup(GPIO.OUT)
    rclk = gpio(24, GPIO)
    rclk.setup(GPIO.OUT)
    srclk = gpio(25, GPIO)
    srclk.setup(GPIO.OUT)
    # in this example a shift register will be used
    shift_register = ShiftRegister(ser, rclk, srclk, 16, autocommit=True)
    # and we use a fake GPIO Object to use ShiftRegister instead
    m_a_a1 = ShiftGPIOWrapper(shift_register, 0)
    m_a_a2 = ShiftGPIOWrapper(shift_register, 1)
    m_a_b1 = ShiftGPIOWrapper(shift_register, 2)
    m_a_b2 = ShiftGPIOWrapper(shift_register, 3)
    m_b_a1 = ShiftGPIOWrapper(shift_register, 4)
    m_b_a2 = ShiftGPIOWrapper(shift_register, 5)
    m_b_b1 = ShiftGPIOWrapper(shift_register, 6)
    m_b_b2 = ShiftGPIOWrapper(shift_register, 7)
    m_c_a1 = ShiftGPIOWrapper(shift_register, 8)
    m_c_a2 = ShiftGPIOWrapper(shift_register, 9)
    m_c_b1 = ShiftGPIOWrapper(shift_register, 10)
    m_c_b2 = ShiftGPIOWrapper(shift_register, 11)
    try:
        logging.info("Initialize GPIO Modes")
        # build our controller
        logging.info("Creating Controller Object")
        # one turn is 8 mm * pi in 48 steps, motor and screw specifications
        controller = Controller(resolution=8 * math.pi / 48, default_speed=1.0, delay=0.0)
        controller.add_motor("X", UnipolarStepperMotor(coils=(m_a_a1, m_a_a2, m_a_b1, m_a_b2), max_position=9999, min_position=-9999, delay=0.00))
        controller.add_motor("Y", UnipolarStepperMotor(coils=(m_b_a1, m_b_a2, m_b_b1, m_b_b2), max_position=9999, min_position=-9999, delay=0.00))
        controller.add_motor("Z", UnipolarStepperMotor(coils=(m_c_a1, m_c_a2, m_c_b1, m_c_b2), max_position=20, min_position=0, delay=0.00))
        controller.add_spindle(Spindle()) # generic spindle object
        controller.add_transformer(PlotterTransformer(width=1000, heigth=500, scale=20.0)) # transformer for plotter usage
        # create parser
        logging.info("Creating Parser Object")
        parser = Parser(filename=sys.argv[1])
        parser.set_controller(controller)
        # create gui
        logging.info("Creating GUI")
        gui = PlotterSimulator(automatic=True)
        # gui = GcodeGuiConsole()
        # connect gui with parser and controller
        gui.set_controller(controller)
        controller.set_gui_cb(gui.controller_cb)
        gui.set_parser(parser)
        parser.set_gui_cb(gui.parser_cb)
        # start
        logging.info("Please move pen to left top corner, the origin")
        key = raw_input("Press any KEY when done")
        parser.read()
    except ControllerExit as exc:
        logging.info(exc)
    except KeyboardInterrupt as exc:
        logging.info(exc)
    except StandardError as exc:
        logging.exception(exc)
    GPIO.cleanup()

if __name__ == "__main__":
    import cProfile
    import pstats
    profile = "Tracer.profile"
    #cProfile.runctx( "main()", globals(), locals(), filename=profile)
    s = pstats.Stats(profile)
    s.sort_stats('time')
    s.print_stats()
    # main()
