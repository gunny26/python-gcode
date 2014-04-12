#/usr/bin/python
# -*- coding: utf-8 -*-
#
# parse Gcode
#

import logging
logging.basicConfig(level=logging.DEBUG, format="%(message)s")
import threading
import time
import sys

class GuiConsole(threading.Thread):
    """simple Console based User Interface"""

    def __init__(self):
        threading.Thread.__init__(self)
        # initialize some variables
        self.controller = None
        self.parser = None
        self.ending = False
        self.controller_stats = {
                "starttime" : time.time(),
                "lasttime" : time.time(),
                "steps" : 0,
                "X" : {
                    "max" : 0,
                    "min" : 0,
                    },
                "Y" : {
                    "max" : 0,
                    "min" : 0,
                    },
                "Z" : {
                    "max" : 0,
                    "min" : 0,
                    },
                }
        self.transformer_stats = {
                "starttime" : time.time(),
                "lasttime" : time.time(),
                "steps" : 0,
                "before" : {
                    "X" : {
                        "max" : 0,
                        "min" : 0,
                        },
                    "Y" : {
                        "max" : 0,
                        "min" : 0,
                        },
                    "Z" : {
                        "max" : 0,
                        "min" : 0,
                        },
                    },
                "after" : {
                    "X" : {
                        "max" : 0,
                        "min" : 0,
                        },
                    "Y" : {
                        "max" : 0,
                        "min" : 0,
                        },
                    "Z" : {
                        "max" : 0,
                        "min" : 0,
                        },
                    },
                }
        self.parser_stats = {
                "starttime" : time.time(),
                "lasttime" : time.time(),
                "commands" : 0,
                "last_g_code" : "",
                "codes" : {},
                }
        self.start()

    def set_controller(self, controller):
        """set controller object reference"""
        self.controller = controller

    def set_parser(self, parser):
        """set parser object reference"""
        self.parser = parser

    def controller_cb(self):
        """called from controller to inform about changes"""
        # logging.info(self.controller.position)
        position = self.controller.position
        for axis in ("X", "Y", "Z"):
            self.controller_stats[axis]["min"] = min(position.get_axis(axis), self.controller_stats[axis]["min"])
            self.controller_stats[axis]["max"] = max(position.get_axis(axis), self.controller_stats[axis]["max"])
        self.controller_stats["steps"] += 1
        self.controller_stats["lasttime"] = time.time()

    def parser_cb(self):
        """called from parser to inform about changes"""
        self.parser_stats["commands"] += 1
        last_g_code = self.parser.last_g_code
        self.parser_stats["last_g_code"] = last_g_code
        if last_g_code not in self.parser_stats["codes"]:
            self.parser_stats["codes"][last_g_code] = 1
        else:
            self.parser_stats["codes"][last_g_code] += 1
        self.parser_stats["lasttime"] = time.time()

    def transformer_cb(self, before, after):
        """called from tranformer to inform about changes"""
        for axis in ("X", "Y", "Z"):
            self.transformer_stats["before"][axis]["min"] = min(before.get_axis(axis), self.transformer_stats["before"][axis]["min"])
            self.transformer_stats["before"][axis]["max"] = max(before.get_axis(axis), self.transformer_stats["before"][axis]["max"])
        for axis in ("X", "Y", "Z"):
            self.transformer_stats["after"][axis]["min"] = min(after.get_axis(axis), self.transformer_stats["after"][axis]["min"])
            self.transformer_stats["after"][axis]["max"] = max(after.get_axis(axis), self.transformer_stats["after"][axis]["max"])
        self.transformer_stats["steps"] += 1
        self.transformer_stats["lasttime"] = time.time()

    def quit(self):
        self.ending = True

    def controller_output(self):
        sb = "Controller Statistics\n"
        sb += "STEPS: %(steps)s\n" % self.controller_stats
        for axis in ("X", "Y", "Z"):
            sb += " %s:" % axis
            sb += "%(min)s steps -> %(max)s steps\n" % self.controller_stats[axis]
        sb += " duration : %s seconds" % (self.controller_stats["lasttime"] - self.controller_stats["starttime"]) 
        print sb

    def parser_output(self):
        sb = "Parser Statistics\n"
        sb += "COMMANDS: %(commands)s\n" % self.parser_stats
        sb += " last_g_code: %(last_g_code)s\n" % self.parser_stats
        for code, called in self.parser_stats["codes"].items():
            sb += " %s : %s\n" % (code, called)
        sb += " duration : %s seconds" % (self.parser_stats["lasttime"] - self.parser_stats["starttime"])
        print sb

    def transformer_output(self):
        sb = "Transformer Statistics\n"
        sb += " Before Data:\n" 
        for axis in ("X", "Y", "Z"):
            sb += "  %s:" % axis
            sb += "%(min)s mm -> %(max)s mm\n" % self.transformer_stats["before"][axis]
        sb += " After Data:\n" 
        for axis in ("X", "Y", "Z"):
            sb += "  %s:" % axis
            sb += "%(min)s mm -> %(max)s mm\n" % self.transformer_stats["after"][axis]
        print sb

    def run(self):
        while not self.ending:
            time.sleep(1)
        self.parser_output()
        self.controller_output()
        self.transformer_output()
