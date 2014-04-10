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
#try:
#    import pyximport
#    pyximport.install()
#except ImportError:
#    pass
import sys
import math
import logging
logging.basicConfig(level=logging.ERROR, format="%(message)s")
# FakeGPIO or real one, depends on hardware
from FakeGPIO import FakeGPIO as GPIO
#try:
#    import RPi.GPIO as GPIO
    # from GpioObject import GpioObject
    # GPIO = GpioObject()
#except ImportError:
#    logging.error("Semms not to be a RaspberryPi")
#    from  FakeGPIO import FakeGPIO as GPIO
# own modules
# GPIO Warpper, object interface to GPIO Ports
from GPIOWrapper import GPIOWrapper as gpio
from ShiftRegister import ShiftRegister as ShiftRegister
from ShiftGPIOWrapper import ShiftGPIOWrapper as ShiftGPIOWrapper
from Parser import Parser as Parser
from Controller import ControllerExit as ControllerExit
from UnipolarStepperMotor import UnipolarStepperMotor as UnipolarStepperMotor
from BaseSpindle import BaseSpindle as BaseSpindle
from Controller import Controller as Controller
from Transformer import PlotterTransformer as PlotterTransformer
from PlotterSimulator import PlotterSimulator as PlotterSimulator
from GcodeGuiConsole import GcodeGuiConsole as GcodeGuiConsole

def main(): 
    # if no parameter option is given, default to example gcode
    if len(sys.argv) == 1:
        sys.argv.append("examples/tiroler_adler.ngc")
    # bring GPIO to a clean state
    try:
        GPIO.cleanup_existing()
        GPIO.setmode(GPIO.BOARD)
    except AttributeError:
        GPIO.setmode(GPIO.BCM)
    # we use GPIO Wrapper, object like interface to real GPIO Module
    ser = gpio(7, GPIO)
    ser.setup(GPIO.OUT)
    rclk = gpio(8, GPIO)
    rclk.setup(GPIO.OUT)
    srclk = gpio(25, GPIO)
    srclk.setup(GPIO.OUT)
    # in this example a shift register will be used
    shift_register = ShiftRegister(ser, rclk, srclk, 16, autocommit=True)
    # and we use a fake GPIO Object to use ShiftRegister instead
    # Motor A left upper corner
    m_a_a1 = ShiftGPIOWrapper(shift_register, 0)
    m_a_a2 = ShiftGPIOWrapper(shift_register, 1)
    m_a_b1 = ShiftGPIOWrapper(shift_register, 2)
    m_a_b2 = ShiftGPIOWrapper(shift_register, 3)
    # motor B, should be reversed to A
    m_b_a1 = ShiftGPIOWrapper(shift_register, 6)
    m_b_a2 = ShiftGPIOWrapper(shift_register, 7)
    m_b_b1 = ShiftGPIOWrapper(shift_register, 4)
    m_b_b2 = ShiftGPIOWrapper(shift_register, 5)
    # Motor C Penholder
    m_c_a1 = ShiftGPIOWrapper(shift_register, 8)
    m_c_a2 = ShiftGPIOWrapper(shift_register, 9)
    m_c_b1 = ShiftGPIOWrapper(shift_register, 10)
    m_c_b2 = ShiftGPIOWrapper(shift_register, 11)
    try:
        logging.info("Initialize GPIO Modes")
        # build our controller
        logging.info("Creating Controller Object")
        motor_x = UnipolarStepperMotor(coils=(m_a_a1, m_a_a2, m_a_b1, m_a_b2), max_position=9999, min_position=-9999, delay=0.0)
        motor_y = UnipolarStepperMotor(coils=(m_b_a1, m_b_a2, m_b_b1, m_b_b2), max_position=9999, min_position=-9999, delay=0.0)
        motor_z = UnipolarStepperMotor(coils=(m_c_a1, m_c_a2, m_c_b1, m_c_b2), max_position=9999, min_position=-9999, delay=0.0, sos_exception=False)
        # one turn is 8 mm * pi in 48 steps, motor and screw specifications
        controller = Controller(resolution=8 * math.pi / 48, default_speed=1.0)
        controller.add_motor("X", motor_x)
        controller.add_motor("Y", motor_y)
        controller.add_motor("Z", motor_z)
        controller.add_spindle(BaseSpindle()) # generic spindle object
        controller.add_transformer(PlotterTransformer(width=830, scale=15.0, ca_zero=320, h_zero=140)) # transformer for plotter usage
        # create parser
        logging.info("Creating Parser Object")
        parser = Parser(filename=sys.argv[1], autorun=1)
        parser.set_controller(controller)
        # create gui
        logging.info("Creating GUI")
        # gui = PlotterSimulator(automatic=True)
        gui = GcodeGuiConsole()
        # connect gui with parser and controller
        gui.set_controller(controller)
        controller.set_gui_cb(gui.controller_cb)
        gui.set_parser(parser)
        parser.set_gui_cb(gui.parser_cb)
        # start
        logging.info("Please move pen to left top corner, the origin")
        # key = raw_input("Press any KEY when done")
        parser.read()
    except ControllerExit as exc:
        logging.info(exc)
    except KeyboardInterrupt as exc:
        logging.info(exc)
    except StandardError as exc:
        logging.exception(exc)
    shift_register.clear()
    GPIO.cleanup()

if __name__ == "__main__":
    import cProfile
    import pstats
    profile = "Plotter.profile"
    cProfile.runctx( "main()", globals(), locals(), filename=profile)
    s = pstats.Stats(profile)
    s.sort_stats('time')
    s.print_stats()
