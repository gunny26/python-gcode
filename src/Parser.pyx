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


cdef class Parser(object):
    """
    Class to parse GCode Commands from File
    G-Codes will be translated in method calls in Class Controller
    """

    cdef str filename
    cdef int autorun
    cdef object controller
    cdef object gui_cb
    cdef list calls
    cdef public str last_g_code

    def __init__(self, str filename, int autorun):
        """
        @params
        filename -> filename to read G-Codes from
        autorun -> should controller method calles automatically be initialized
            after parssing of file is done, or not
        """
        self.filename = filename
        self.autorun = autorun
        # last known g code
        self.last_g_code = ""
        # initial values
        self.controller = None
        self.gui_cb = None
        # call list
        self.calls = []

    cpdef int set_controller(self, object controller):
        """set controller object, must be done prior to parse() call"""
        self.controller = controller
        return(0)

    cpdef int set_gui_cb(self, object gui_cb):
        """
        gui should be called after every step
        gui_cb must be a instance method
        """
        self.gui_cb = gui_cb
        return(0)

    cdef int caller(self, str methodname, object args):
        """
        calls G- or M- code Method

        if no G-Code Method was given, the last method will be repeated

        for example G02 results in call of self.controller.G02(args)
        """
        # logging.debug("calling %s(%s)", methodname, args)
        method_to_call = getattr(self.controller, methodname)
        self.calls.append((method_to_call, args, methodname))
        # method_to_call(args)
        if methodname[0] == "G":
            self.last_g_code = methodname
        self.gui_cb()
        return(0)

    cpdef int run(self):
        """run stored methodcalls to controller in batch"""
        for (method_to_call, args, methodname) in self.calls:
            logging.info("calling %s(%s)", methodname, args)
            method_to_call(args)
        return(0)

    cpdef int read(self):
        """
        read input file line by line, and parse gcode Commands
        """
        fd = os.open(self.filename, os.O_RDONLY)
        f = os.fdopen(fd, "r")
        # precompile regular expressions
        cdef dict rex_g = {}
        cdef set g_params = set(("X", "Y", "Z", "I", "J", "K", "P", "R", "K", "U", "V", "W", "A", "B", "C"))
        for g_param in g_params:
            rex_g[g_param] = re.compile("(%s[\+\-]?[\d\.]+)\D?" % g_param)
        # regex compilation
        codes_rex = re.compile("([F|S|T][\d|\.]+)\D?")
        gcodes_rex = re.compile("([G|M][\d|\.]+)\D?")
        comment_rex = re.compile("^\((.*)\)?$")
        for line in f:
            # cleanup line
            line = line.strip()
            line = line.upper()
            # filter out some incorrect lines
            # blank lines
            # lines beginning with % or ( 
            if len(line) == 0 or line[0] == "%" or line[0] == "(": 
                continue
            # start of parsing
            
            #comment = comment_rex.match(line)
            #if comment is not None:
            #    #logging.info("ignoring: %s", comment.group(0))
            #    continue

            #logging.info("parsing: %s", line)
            # first determine if this line is something of G-Command or M-Command
            # if that line is after a modal G or M Code, there are only 
            # G Parameters ("X", "Y", "Z", "F", "I", "J", "K", "P", "R")
            # M Parameters ("S")
            # search for M-Codes
            # Feed Rate has precedence over G
            params = {}
            for parameter in g_params:
                match = rex_g[parameter].search(line)
                if match:
                    params[parameter] = float(match.group(1)[1:])
                    line = line.replace(match.group(1), "")
            codes = codes_rex.findall(line)
            if codes is not None:
                for code in codes:
                    self.caller(code[0], code[1:])
                    line = line.replace(code, "")
            gcodes = gcodes_rex.findall(line)
            if (len(params) > 0) and (len(gcodes) == 0):
                gcodes.append(self.last_g_code)
            for code in gcodes:
                self.caller(code, params)
                line = line.replace(code, "")
            # remaining line should be of no interest
            remaining_line = line.strip()
            if len(remaining_line) > 0:
                logging.debug("remaining: %s", line)
        logging.info("parsing done")
        if self.autorun is True:
            self.run()
        else:
            logging.info("You have to call run(), to call Controller methods")
        return(0)
