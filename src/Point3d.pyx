#/usr/bin/python
# -*- coding: utf-8 -*-
#
# parse Gcode
#
#cython: profile=True

from libc.math cimport sin, cos, acos, sqrt, M_PI


cdef class Point3d(object):
    """
    three dimension vetor representation
    """

    cdef public double X
    cdef public double Y
    cdef public double Z

    def __init__(self, double x=0.0, double y=0.0, double z=0.0):
        self.X = x
        self.Y = y
        self.Z = z

    def get_axis(self, axisname):
        return(getattr(self, axisname))

    def set_axis(self, axisname, value):
        return(setattr(self, axisname, value))
 
    def __repr__(self):
        return("Point3d(%s, %s, %s)" % (self.X, self.Y, self.Z))

    def __str__(self):
        return("(%s, %s, %s)" % (self.X, self.Y, self.Z))

    def __add__(self, other):
        return(Point3d(self.X + other.X, self.Y + other.Y, self.Z + other.Z))

    def __iadd__(self, object other):
        self.X += other.X
        self.Y += other.Y
        self.Z += other.Z

    def __sub__(self, object other):
        return(Point3d(self.X - other.X, self.Y - other.Y, self.Z - other.Z))

    def __isub__(self, object other):
        self.X -= other.X
        self.Y -= other.Y
        self.Z -= other.Z

    def __mul__(self, double scalar):
        return(Point3d(self.X * scalar, self.Y * scalar, self.Z * scalar))

    def __imul__(self, float scalar):
        self.X *= scalar
        self.Y *= scalar
        self.Z *= scalar

    def __div__(self, double scalar):
        return(Point3d(self.X / scalar, self.Y / scalar, self.Z / scalar))

    def __idiv__(self, float scalar):
        self.X /= scalar
        self.Y /= scalar
        self.Z /= scalar

    cpdef double length(self):
        """return length of vector"""
        return(sqrt(self.X ** 2 + self.Y ** 2 + self.Z ** 2))

    cpdef double lengthXY(self):
        """return length of vector"""
        return(sqrt(self.X ** 2 + self.Y ** 2))

    cpdef object unit(self):
        """
        return unit vector of self
        divide every element of self by length of self

        length of unit vector is always 1
        """
        length = self.length()
        return(Point3d(self.X / length, self.Y / length, self.Z / length))

    cpdef object product(self, object other):
        """
        returns the cross product of self with other
        a = self
        b = other

        cx = ay * bz - az * by
        cy = az * bx - ax * bz
        cz = ax * by - ay * bx
        
        the returned vector is orthogonal to the plan a,b
        """
        cross_x = self.Y * other.Z - self.Z * other.Y
        cross_y = self.Z * other.X - self.X * other.Z
        cross_z = self.X * other.Y - self.Y * other.X
        return(Point3d(cross_x, cross_y, cross_z))

    cpdef object rotated_z_fast(self, double theta, double cos_theta, double sin_theta):
        """
        return rotated version of self around Z-Axis
        faster version, with precalculated cos(theta) and sin(theta)
        """
        rotated_x = self.X * cos_theta - self.Y * sin_theta
        rotated_y = self.X * sin_theta + self.Y * cos_theta
        return(Point3d(rotated_x, rotated_y, self.Z))


    cpdef object rotated_Z(self, double theta):
        """
        return rotated version of self around Z-Axis
        theta should be given in radians
        http://stackoverflow.com/questions/14607640/rotating-a-vector-in-3d-space
        |cos θ   -sin θ   0| |x|   |x cos θ - y sin θ|   |x'|
        |sin θ    cos θ   0| |y| = |x sin θ + y cos θ| = |y'|
        |  0       0      1| |z|   |        z        |   |z'|
        """
        rotated_x = self.X * cos(theta) - self.Y * sin(theta)
        rotated_y = self.X * sin(theta) + self.Y * cos(theta)
        rotated_z = self.Z
        return(Point3d(rotated_x, rotated_y, rotated_z))

    cpdef object rotated_Y(self, double theta):
        """
        return rotated version of self around Y-Axis
        theta should be given in radians
        http://stackoverflow.com/questions/14607640/rotating-a-vector-in-3d-space
        | cos θ    0   sin θ| |x|   | x cos θ + z sin θ|   |x'|
        |   0      1       0| |y| = |         y        | = |y'|
        |-sin θ    0   cos θ| |z|   |-x sin θ + z cos θ|   |z'|
        """
        rotated_x = self.X * cos(theta) + self.Z * sin(theta)
        rotated_y = self.Y
        rotated_z = (-1) * self.X * sin(theta) + self.Z * cos(theta)
        return(Point3d(rotated_x, rotated_y, rotated_z))

    cpdef object rotated_X(self, double theta):
        """
        return rotated version of self around X-Axis
        theta should be given in radians
        http://stackoverflow.com/questions/14607640/rotating-a-vector-in-3d-space
        |1     0           0| |x|   |        x        |   |x'|
        |0   cos θ    -sin θ| |y| = |y cos θ - z sin θ| = |y'|
        |0   sin θ     cos θ| |z|   |y sin θ + z cos θ|   |z'|
        """
        rotated_x = self.X
        rotated_y = self.Y * cos(theta) - self.Z * sin(theta)
        rotated_z = self.Y * sin(theta) + self.Z * cos(theta)
        return(Point3d(rotated_x, rotated_y, rotated_z))

    cpdef double dot(self, object other):
        """
        Dot Product of two vectors with the same number of items
        """
        return(self.X * other.X + self.Y * other.Y + self.Z * other.Z)

    cpdef double angle(self):
        """
        which angle does this vector has, from his origin
        """
        # corect angle if in 3rd or 4th quadrant
        if self.Y < 0 :
            return(2 * M_PI - acos(self.X))
        else:
            return(acos(self.X))

    cpdef double angle_between(self, object other):
        """
        angle between self and other vector
        """
        try:
            dot = self.dot(other)
            if dot > 1.0:
                print "Dot Product %f" % dot
                dot = 1
            elif dot < -1.0:
                print "Dot Product %f" % dot
                dot = -1
            result = acos(dot)
            return(result)
        except ValueError as exc:
            print "Value Error, dot product not between -1 and 1, actually:%f" % dot
            raise(exc)
