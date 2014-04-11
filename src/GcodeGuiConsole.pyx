#/usr/bin/python
# -*- coding: utf-8 -*-
#
# parse Gcode
#

import logging
logging.basicConfig(level=logging.DEBUG, format="%(message)s")

cdef class GcodeGuiConsole(object):
    """simple Console based User Interface"""

    cdef object controller
    cdef object parser

    def __init__(self):
        # initialize some variables
        self.controller = None
        self.parser = None

    cpdef int set_controller(self, controller):
        self.controller = controller

    cpdef int controller_cb(self):
        """called from controller to inform about changes"""
        # logging.info(self.controller.position)
        self.update()

    cpdef int set_parser(self, parser):
        self.parser = parser

    cpdef int parser_cb(self):
        """called from parser to inform about changes"""
        self.update()

    cpdef int update(self):
        pass
