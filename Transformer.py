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


    def __init__(self, width, height, scale, ca_zero, h_zero):
        Transformer.__init__(self, scale)
        self.width = width
        #self.height = height
        self.scale = scale
        # offset to virtual point (x=0, y=0)
        self.ca_zero = ca_zero
        self.cb_zero = ca_zero - self.width
        self.h_zero = h_zero
        # two null-position vectors, for motr a and b
        self.zero_a = Point3d(self.ca_zero, 0, 0) + Point3d(0, self.h_zero, 0)
        self.zero_b = Point3d(self.cb_zero, 0, 0) + Point3d(0, self.h_zero, 0)
        # the zero positon length is in bottom middle
        # at this length of both motors, we define zero position
        #self.zero = math.sqrt((self.width / 2) ** 2 + (self.height / 2) ** 2)
        # Motor A is positioned in upper left corner
        #self.motor_A = Point3d(-self.width / 2, -self.height / 2)
        # Motor B is positioned in upper right corner
        #self.motor_B = Point3d(self.width / 2, -self.height / 2)

#    def get_motor_A(self):
#        return(self.motor_A)
#
#    def get_motor_B(self):
#        return(self.motor_B)
#
    def transform(self, data):
        """
        data is a unit vector of type Point3d (length = 1)
        from x,y,z coordinates this fuction translates to a/b/z for plotter
        z axis is ignored for transformation, and left unchanged

        virtual motor X is translated into motor A
        virtual motor Y is translated into motor B
        virtual motor Z -> will stay Z

        ^ Y
        |
        |      Z
        |    /
        |   /        . data(x, y, z)
        |  /
        | /
        |/
        -----------------------------> X

        should be translated into

        A            B
         \--------- /
          \        /
           \      /
            \    /
             \  /
              \/
              data(a, b, z)
        
        a represents the vector from A to data
        b represents the vector from B to data
        z is not used, untouched

        the zero point is exactly in the middle of A and B at the bottom
        usually zero ion carthesian coordinates is in upper left corner,
        so y has to be subtracted from height, to go up
        """
        cx = Point3d(self.ca_zero + data.X, 0, 0)
        cy = Point3d(self.cb_zero - data.X, 0, 0)
        h = Point3d(0, self.h_zero + data.Y, 0)
        # calculate length a and b
        a = (cx + h).lengthXY() - self.zero_a.lengthXY()
        b = (cy + h).lengthXY() - self.zero_b.lengthXY()
        transformed = Point3d(a, b, 0) * self.scale
        # Z-Axis is unchanged from scale
        transformed = transformed + Point3d(0, 0, data.Z)
        #logging.debug("__step called with %s", args)
        # logging.info("before transformation %s", data)
        # move origin in the middle of the plane
        #transformed = Point3d(self.zero - (self.motor_A - data).lengthXY(), self.zero - (self.motor_B - data).lengthXY(), data.Z)

        #
        #transformed = Point3d(self.zero - (self.motor_A - data).lengthXY(), self.zero - (self.motor_B - data).lengthXY(), data.Z)
        #transformed = transformed * self.scale
        logging.info("transformation %s -> %s", data, transformed)
        return(transformed)
