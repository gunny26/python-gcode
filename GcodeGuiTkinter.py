#/usr/bin/python
# -*- coding: utf-8 -*-
#
# parse Gcode
#

import Tkinter
import threading
import logging
logging.basicConfig(level=logging.DEBUG, format="%(message)s")

class GcodeGuiTkinter(threading.Thread):
    """simple Console based User Interface"""

    def __init__(self):
        threading.Thread.__init__(self)
        # initialize some variables
        self.controller = None
        self.parser = None
        # start thread
        self.start()

    def callback(self):
        self.root.quit()

    def run(self):
        """initialize Tkinter, will be called automatically from threading"""
        self.root = Tkinter.Tk()
        self.w = Tkinter.Canvas(self.root, width=200, height=100)
        self.w.pack()
        self.w.create_line(0, 0, 200, 100)
        self.w.create_line(0, 100, 200, 0, fill="red", dash=(4, 4))
        self.w.create_rectangle(50, 25, 150, 75, fill="blue")
        self.root.mainloop()
 
    def set_controller(self, controller):
        self.controller = controller

    def controller_cb(self, *args):
        """called from controller to inform about changes"""
        self.w.create_line(0, 0, self.controller.position.X * 100, self.controller.position.Y * 100)
        logging.info(self.controller.position)
        self.update()

    def set_parser(self, parser):
        self.parser = parser

    def parser_cb(self, *args):
        """called from parser to inform about changes"""
        self.update()

    def update(self):
        pass
