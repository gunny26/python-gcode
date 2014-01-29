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
    logging.error("Semms not be a RaspberryPi")
    from  FakeGPIO import FakeGPIO as GPIO
import re
import pygame
# own modules
from Motor import BipolarStepperMotor as BipolarStepperMotor
from Motor import LaserMotor as LaserMotor
from Spindle import Spindle as Spindle
from Controller import Controller as Controller

# wait for keypress, or wait amount of time
AUTOMATIC = True

class Parser(object):
    """
    Class to parse GCode Text Commands
    """

    def __init__(self, surface, filename):
        self.surface = surface
        self.filename = filename
        # build our controller
        self.controller = Controller(surface=surface, resolution=512/36, default_speed=1.0, delay=0.0)
        self.controller.add_motor("X", BipolarStepperMotor(coils=(4, 2, 27, 22), max_position=512, min_position=0, delay=0.0))
        self.controller.add_motor("Y", BipolarStepperMotor(coils=(24, 25, 7, 8), max_position=512, min_position=0, delay=0.0))
        self.controller.add_motor("Z", LaserMotor(laser_pin=14, min_position=-10000, max_position=10000, delay=0.0))
        self.controller.add_spindle(Spindle())
        # last known g code
        self.last_g_code = None
        # draw grid
        if self.surface is not None:
            self.draw_grid()
        # precompile regular expressions
        self.rex_g = {}
        self.g_params = ("X", "Y", "Z", "F", "I", "J", "K", "P", "R")
        for g_param in self.g_params:
            self.rex_g[g_param] = re.compile("%s([\+\-]?[\d\.]+)\D?" % g_param)
        self.rex_m = {}
        self.m_params = ("S", )
        for m_param in self.m_params:
            self.rex_m[m_param] = re.compile("%s([\+\-]?[\d\.]+)\D?" % m_param)

    def draw_grid(self):
        """
        draw grid on pygame window
        first determine, which axis are to draw
        second determine what the min_position and max_positions of each motor are

        surface.X : self.motors["X"].min_position <-> surface.get_width() = self.motors["X"].max_position
        surface.Y : self.motors["Y"].min_position <-> surface.get_height() = self.motors["Y"].max_position
        """
        color = pygame.Color(0, 50, 0, 255)
        for x in range(0, self.surface.get_height(), 10):
            pygame.draw.line(self.surface, color, (x, 0), (x, self.surface.get_height()), 1)
        for y in range(0, self.surface.get_width(), 10):
            pygame.draw.line(self.surface, color, (0, y), (self.surface.get_width(), y), 1)
        color = pygame.Color(0, 100, 0, 255)
        pygame.draw.line(self.surface, color, (self.surface.get_width() / 2, 0), (self.surface.get_width() / 2, self.surface.get_height()))
        pygame.draw.line(self.surface, color, (0, self.surface.get_height() / 2), (self.surface.get_width(), self.surface.get_height() / 2))
        # draw motor scales
        color = pygame.Color(100, 0, 0, 255)
        pygame.draw.line(self.surface, color, (self.surface.get_width() - 10, 0), (self.surface.get_width() - 10, self.surface.get_height()))
        pygame.draw.line(self.surface, color, (0, self.surface.get_height() - 10), (self.surface.get_width(), self.surface.get_height() - 10))

    def parse_g_params(self, line):
        """parse known Parameters to G-Commands"""
        result = {}
        for parameter in self.g_params:
            match = self.rex_g[parameter].search(line)
            if match:
                result[parameter] = float(match.group(1))
        return(result)

    def parse_m_params(self, line):
        """parse known Parameters to M-Commands"""
        result = {}
        for parameter in self.m_params:
            match = self.rex_m[parameter].search(line)
            if match:
                result[parameter] = float(match.group(1))
        return(result)

    def caller(self, methodname=None, args=None):
        """
        calls G- or M- code Method

        if no G-Code Method was given, the last methos will be repeated

        fo example G02 results in call of self.controller.G02(args)
        """
        # logging.info("Methodname = %s" % methodname)
        if methodname is None:
            methodname = self.last_g_code
        else:
            self.last_g_code = methodname
        method_to_call = getattr(self.controller, methodname)
        method_to_call(args)

    def read(self):
        """
        read input file line by line, and parse gcode Commands
        """
        for line in open(self.filename, "rb"):
            # cleanup line
            line = line.strip()
            line = line.upper()
            # filter out some incorrect lines
            if len(line) == 0: 
                continue
            if line[0] == "%": 
                continue
            # start of parsing
            logging.info("-" * 80)
            if line[0] == "(":
                logging.info("Comment: %s", line[1:])
                continue
            logging.info("parsing %s", line)
            # search for M-Codes
            mcodes = re.findall("([m|M][\d|\.]+\D?)", line)
            if len(mcodes) == 1:
                mcode = mcodes[0].strip()
                parameters = self.parse_m_params(line)
                self.caller(mcode, parameters)
                continue
            elif len(mcodes) > 1:
                logging.error("There should only be one M-Code in one line")
            # search for G-Codes
            gcodes = re.findall("([g|G][\d|\.]+\D)", line)
            if len(gcodes) > 1:
                logging.debug("Multiple G-Codes on one line detected")
                for gcode in gcodes:
                    gcode = gcode.strip()
                    logging.info("Found %s", gcode)
                    self.caller(gcode)
            elif len(gcodes) == 1:
                gcode = gcodes[0].strip()
                logging.debug("Only one G-Code %s detected", gcode)
                parameters = self.parse_g_params(line)
                self.caller(gcode, parameters)
            else:
                logging.debug("No G-Code on this line assuming last modal G-Code %s" % self.last_g_code)
                result = self.parse_g_params(line)
                self.caller(methodname=None, args=result)
            # pygame drawing if surface is available
            if self.surface is not None:
                pygame.display.flip()
            # automatic stepping or keypress
            if AUTOMATIC is not True:
                while (pygame.event.wait().type != pygame.KEYDOWN):
                    pass
        # wait for keypress
        while (pygame.event.wait().type != pygame.KEYDOWN):
            pass


def safe_position():
    """safe GPIO Pin Position, everything LOW"""
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
        key = raw_input("Press any KEY when done")
        logging.info("Initialize GPIO Modes")
        GPIO.setup(23, GPIO.OUT)
        GPIO.output(23, 1)
        GPIO.setup(14, GPIO.OUT)
        GPIO.output(14, 0)
        key = raw_input("Press and KEY to start parsing")
        pygame.init()
        surface = pygame.display.set_mode((530, 530))
        surface.fill((0, 0, 0))
        pygame.display.flip()
        parser = Parser(surface=surface, filename=sys.argv[1])
        parser.read()
    except Exception, exc:
        logging.exception(exc)
        safe_position()
        GPIO.cleanup()
    pygame.quit()

if __name__ == "__main__":
    main()
