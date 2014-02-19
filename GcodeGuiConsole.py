#/usr/bin/python
# -*- coding: utf-8 -*-
#
# parse Gcode
#

import logging
logging.basicConfig(level=logging.DEBUG, format="%(message)s")

class GcodeGuiConsole(object):
    """simple Console based User Interface"""

    def __init__(self):
        # initialize some variables
        self.controller = None
        self.parser = None

    def set_controller(self, controller):
        self.controller = controller

    def controller_cb(self, *args):
        """called from controller to inform about changes"""
        # logging.info(self.controller.position)
        self.update()

    def set_parser(self, parser):
        self.parser = parser

    def parser_cb(self, *args):
        """called from parser to inform about changes"""
        self.update()

    def update(self):
        pass
