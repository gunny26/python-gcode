#/usr/bin/python
# -*- coding: utf-8 -*-
#
# parse Gcode
#
"""
Module to parse Gcode from File
"""
import os
import logging
logging.basicConfig(level=logging.DEBUG, format="%(message)s")
import re


class Parser(object):
    """
    Class to parse GCode Text Commands
    """

    def __init__(self, filename):
        self.filename = filename
        # last known g code
        self.last_g_code = None
        # precompile regular expressions
        self.rex_g = {}
        self.g_params = ("X", "Y", "Z", "I", "J", "K", "P", "R", "K", "U", "V", "W", "A", "B", "C")
        for g_param in self.g_params:
            self.rex_g[g_param] = re.compile("(%s[\+\-]?[\d\.]+)\D?" % g_param)
        # initial values
        self.controller = None
        self.gui_cb = None
        # save actual commands on this line
        self.command = None
        # call list
        self.calls = []

    def set_controller(self, controller):
        """set controller object, must be done prior to parse() call"""
        self.controller = controller

    def set_gui_cb(self, gui_cb):
        """
        gui should be called after every step
        gui_cb must be a instance method
        """
        self.gui_cb = gui_cb

    def caller(self, methodname=None, args=None):
        """
        calls G- or M- code Method

        if no G-Code Method was given, the last methos will be repeated

        fo example G02 results in call of self.controller.G02(args)
        """
        # logging.debug("calling %s(%s)", methodname, args)
        self.command = "%s(%s)" % (methodname, args)
        # update gui object
        self.gui_cb()
        method_to_call = getattr(self.controller, methodname)
        self.calls.append((method_to_call, args))
        # method_to_call(args)
        if methodname[0] == "G":
            self.last_g_code = methodname

    def read(self):
        """
        read input file line by line, and parse gcode Commands
        """
        fd = os.open(self.filename, os.O_RDONLY)
        f = os.fdopen(fd, "r", -1)
        for line in f.readlines():
            # cleanup line
            line = line.strip()
            line = line.upper()
            # filter out some incorrect lines
            if len(line) == 0: 
                continue
            if line[0] == "%": 
                continue
            # start of parsing
            #logging.info("-" * 80)
            comment = re.match("^\((.*)\)?$", line)
            if comment is not None:
                logging.info("ignoring: %s", comment.group(0))
                continue
            logging.info("parsing: %s", line)
            # first determine if this line is something of G-Command or M-Command
            # if that line is after a modal G or M Code, there are only 
            # G Parameters ("X", "Y", "Z", "F", "I", "J", "K", "P", "R")
            # M Parameters ("S")
            # search for M-Codes
            # Feed Rate has precedence over G
            params = {}
            for parameter in self.g_params:
                match = self.rex_g[parameter].search(line)
                if match:
                    params[parameter] = float(match.group(1)[1:])
                    line = line.replace(match.group(1), "")
            codes = re.findall("([F|S|T][\d|\.]+)\D?", line)
            if codes is not None:
                for code in codes:
                    self.caller(code[0], code[1:])
                    line = line.replace(code, "")
            gcodes = re.findall("([G|M][\d|\.]+)\D?", line)
            if (len(params) > 0) and (len(gcodes) == 0):
                gcodes.append(self.last_g_code)
            for code in gcodes:
                self.caller(code, params)
                line = line.replace(code, "")
            # remaining line should be of no interest
            remaining_line = line.strip()
            if len(remaining_line) > 0:
                logging.info("remaining: %s", line)
        logging.info("parsing done")
        for (method_to_call, args) in self.calls:
            logging.debug("calling %s(%s)", method_to_call, args)
            method_to_call(args)
