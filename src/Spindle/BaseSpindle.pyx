#/usr/bin/python

import logging
logging.basicConfig(level=logging.INFO)


class BaseSpindle(object):
    """Abstract Class for Spindle
    Spindle can rotate clockwise or counterclockwise
    in given Speed
    """

    CW = -1 # clockwise direction
    CCW = 1 # counter clockwise direction

    def __init__(self, speed=1.0):
        self.speed = speed
        self.running = False

    def rotate(self, direction, speed=None):
        """
        turn on spindle and rotate in direction with speed
        """
        if speed is None:
            speed = self.speed
        self.running = True
        logging.info("Turn Spindle in Direction %s with speed %s", direction, speed)
        
    def get_state(self):
        if self.running:
            return("%s@%s" % (self.running, self.speed))
        else:
            return("not running")

    def unhold(self):
        """
        power off Spindle
        """
        logging.info("Power Off Spindle")
        self.running = False
