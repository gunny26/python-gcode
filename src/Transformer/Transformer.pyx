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


cdef class Transformer(object):
    """
    class to transform from X/Y motion to other scales or dimensions
    this is the simple pass-through version, no modification is done to the
    motion values
    this class is also the base class for every custom Transformer
    """

    cdef float scale

    def __init__(self, float scale=1.0):
        self.scale = scale

    cpdef object transform(self, object data):
        """
        this is only generic tranformer with no action
        """
        #logging.debug("transform called with %s", data)
        return(data)


cdef class PlotterTransformer(Transformer):
    """class to transfor from motor steps to other steps"""

    cdef int width
    cdef int ca_zero
    cdef int h_zero
    cdef object position
    cdef object offset_a
    cdef object offset_b
    cdef float zero_a
    cdef float zero_b

    def __init__(self, int width, float scale, int ca_zero, int h_zero):
        Transformer.__init__(self, scale)
        self.scale = scale
        # two null-position vectors, for motor a and b
        self.offset_a = Point3d(ca_zero, h_zero, 0)
        self.offset_b = Point3d(ca_zero - width, h_zero, 0)
        # remember last length
        self.zero_a = self.offset_a.lengthXY()
        self.zero_b = self.offset_b.lengthXY()
        # remember own position
        self.position = Point3d(0, 0, 0)

    cpdef object transform(self, object data):
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
        #logging.info("last vector a: %s (%s)", self.offset_a, self.zero_a)
        #logging.info("last vector b: %s (%s)", self.offset_b, self.zero_b)
        #logging.info("moving about vector %s", data)
        a = self.offset_a + data * self.scale
        b = self.offset_b + data * self.scale
        l_a = a.lengthXY()
        l_b = b.lengthXY()
        #logging.info("new vector a: %s (%s)", a, l_a)
        #logging.info("new vector b: %s (%s)", b, l_b)
        l_a -= self.zero_a
        l_b -= self.zero_b
        transformed = Point3d(l_a, l_b, data.Z * self.scale)
        #logging.info("transformation %s -> %s", data, transformed)
        self.offset_a = a
        self.offset_b = b
        self.zero_a += l_a
        self.zero_b += l_b
        return(transformed)
