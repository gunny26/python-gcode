#/usr/bin/python
# -*- coding: utf-8 -*-
#
# parse Gcode
#
"""
Transforms Steps
"""

import math
import logging
logging.basicConfig(level=logging.INFO, format="%(message)s")
from Point3d import Point3d as Point3d


class Transformer(object):
    """class to transfor from motor steps to other steps"""


    def __init__(self, scale=1.0):
        self.scale = scale

    def transform(self, data):
        """
        this is only generic tranformer with no action
        """
        #logging.debug("transform called with %s", data)
        return(data)


class PlotterTransformer(Transformer):
    """class to transfor from motor steps to other steps"""


    def __init__(self, width, heigth, scale):
        Transformer.__init__(self, scale)
        self.width = width
        self.heigth = heigth
        self.scale = scale
        # length on origin, which is the middle of the plane
        self.zero = math.sqrt((self.width / 2) ** 2 + (self.heigth / 2) ** 2)
        self.A = Point3d(-self.width / 2, -self.heigth / 2)
        self.B = Point3d(self.width / 2, -self.heigth / 2)

    def transform(self, data):
        """
        data is a unit vector in carthesian system
        we transfor this motion into length for plotter
        """
        #logging.debug("__step called with %s", args)
        # ignore Z axis
        logging.info("before transformation %s", data)
        # move origin in the middle of the plane
        transformed = Point3d(self.zero - (self.A - data).lengthXY(), self.zero - (self.B - data).lengthXY(), data.Z)
        transformed = transformed * self.scale
        logging.info("after transformation %s", transformed)
        return(transformed)
