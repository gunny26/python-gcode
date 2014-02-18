#/usr/bin/python
# -*- coding: utf-8 -*-
#
# parse Gcode
#
"""
Classes to Transfor motions in X/Y/Z to other dimensions
"""
import math
import logging
logging.basicConfig(level=logging.INFO, format="%(message)s")
# own modules
from Point3d import Point3d as Point3d


class Transformer(object):
    """
    class to transform from X/Y motion to other scales or dimensions
    this is the simple pass-through version, no modification is done to the
    motion values
    this class is also the base class for every custom Transformer
    """


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
        # the zero positon is in bottom middle
        self.zero = math.sqrt((self.width / 2) ** 2 + (self.heigth / 2) ** 2)
        # Motor A is positioned in upper left corner
        self.motor_A = Point3d(-self.width / 2, -self.heigth / 2)
        # Motor B is positioned in upper right corner
        self.motor_B = Point3d(self.width / 2, -self.heigth / 2)

    def get_motor_A(self):
        return(self.motor_A)

    def get_motor_B(self):
        return(self.motor_B)

    def transform(self, data):
        """
        data is a unit vector in R3
        from X/Y/Z Motions this fuction translates to a/b length for plotter
        z axis is ignored for transformation, and left unchanged
        """
        #logging.debug("__step called with %s", args)
        # ignore Z axis
        # logging.info("before transformation %s", data)
        # move origin in the middle of the plane
        transformed = Point3d(self.zero - (self.motor_A - data).lengthXY(), self.zero - (self.motor_B - data).lengthXY(), data.Z)
        transformed = transformed * self.scale
        # logging.info("after transformation %s", transformed)
        return(transformed)
