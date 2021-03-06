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
import sys
import math
import logging
logging.basicConfig(level=logging.INFO)
try:
    import RPi.GPIO as GPIO
except ImportError:
    logging.error("Semms not to be a RaspberryPi")
    from  FakeGPIO import FakeGPIO as GPIO
# own modules
# GPIO Warpper, object interface to GPIO Ports
from GPIOWrapper import GPIOWrapper as gpio
from ShiftRegister import ShiftRegister as ShiftRegister
from ShiftGPIOWrapper import ShiftGPIOWrapper as ShiftGPIOWrapper
from Parser import Parser as Parser
from Controller import ControllerExit as ControllerExit
from A5988DriverMotor import A5988DriverMotor as A5988DriverMotor
from UnipolarStepperMotor import UnipolarStepperMotor as UnipolarStepperMotor
from BaseSpindle import BaseSpindle as BaseSpindle
from Controller import Controller as Controller
from Transformer import PlotterTransformer as PlotterTransformer
#from PlotterSimulator import PlotterSimulator as PlotterSimulator
from GuiConsole import GuiConsole as GuiConsole

def main(): 
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
    m_a_dir = ShiftGPIOWrapper(shift_register, 0)
    m_a_step = ShiftGPIOWrapper(shift_register, 1)
    m_a_enable = ShiftGPIOWrapper(shift_register, 2)
    # motor B, should be reversed to A
    m_b_dir = ShiftGPIOWrapper(shift_register, 3)
    m_b_step = ShiftGPIOWrapper(shift_register, 4)
    m_b_enable = ShiftGPIOWrapper(shift_register, 5)
    # Motor C Penholder
    m_c_dir = ShiftGPIOWrapper(shift_register, 6)
    m_c_step = ShiftGPIOWrapper(shift_register, 7)
    m_c_enable = ShiftGPIOWrapper(shift_register, 8)
    try:
        logging.info("Initialize GPIO Modes")
        # build our controller
        logging.info("Creating Controller Object")
        motor_x = A5988DriverMotor(
            enable_pin=m_a_enable,
            dir_pin=m_a_dir,
            step_pin=m_a_step, 
            max_position=9999, 
            min_position=-9999, 
            delay=0.05)
        motor_y = A5988DriverMotor(
            enable_pin=m_b_enable,
            dir_pin=m_b_dir,
            step_pin=m_b_step, 
            max_position=9999, 
            min_position=-9999, 
            delay=0.05)
        motor_z = A5988DriverMotor(
            enable_pin=m_c_enable,
            dir_pin=m_c_dir,
            step_pin=m_c_step, 
            max_position=9999, 
            min_position=-9999, 
            delay=0.05)
        # one turn is 8 mm * pi in 48 steps, motor and screw specifications
        controller = Controller(resolution=8 * math.pi / 48, default_speed=1.0, autorun=False)
        controller.add_motor("X", motor_x)
        controller.add_motor("Y", motor_y)
        controller.add_motor("Z", motor_z)
        controller.add_spindle(BaseSpindle()) # generic spindle object
        transformer = PlotterTransformer(width=830, scale=15.0, ca_zero=320, h_zero=140) # transformer for plotter usage
        controller.add_transformer(transformer) # transformer for plotter usage
        # create parser
        logging.info("Creating Parser Object")
        parser = Parser(filename=FILENAME, autorun=False)
        parser.set_controller(controller)
        # create gui
        logging.info("Creating GUI")
        # gui = PlotterSimulator(automatic=True)
        gui = GuiConsole()
        # connect gui with parser and controller
        gui.set_controller(controller)
        gui.set_parser(parser)
        controller.set_gui_cb(gui.controller_cb)
        parser.set_gui_cb(gui.parser_cb)
        transformer.set_gui_cb(gui.transformer_cb)
        # start
        logging.info("Please move pen to left top corner, the origin")
        # key = raw_input("Press any KEY when done")
        logging.error("start parsing")
        parser.read()
        logging.error("parsing done, calling controller methods")
        parser.run()
        logging.error("controller calculations done, calling physical world")
        controller.run()
        gui.quit()
    except KeyboardInterrupt as exc:
        logging.info(exc)
    except StandardError as exc:
        logging.exception(exc)
    shift_register.clear()
    GPIO.cleanup()

if __name__ == "__main__":
    FILENAME = "examples/tiroler_adler.ngc"
    if len(sys.argv) == 2:
        FILENAME = sys.argv[1]
    main()
    sys.exit(0)
    import cProfile
    import pstats
    profile = "profiles/%s.profile" % sys.argv[0].split(".")[0]
    cProfile.runctx( "main()", globals(), locals(), filename=profile)
    s = pstats.Stats(profile)
    s.sort_stats('time')
    s.print_stats()
