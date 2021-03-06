#/usr/bin/python
# -*- coding: utf-8 -*-
#
# parse Gcode
#

import logging
logging.basicConfig(level=logging.INFO, format="%(message)s")
# import inspect
import math
import time
# own modules
from Point3d import Point3d as Point3d


class ControllerExit(Exception):

    def __init__(self, *args):
        Exception.__init__(self, *args)


class ControllerCommandNotImplemented(Exception):

    def __init__(self, *args):
        Exception.__init__(self, *args)


cdef class Controller(object):
    """
    Class to receive Gcode Commands and Statements and translate
    these statements in actual motor movement commands.

    this class should be setup with 1-3 motors for x,y,z axis
    and at least one spindle.

    for all of them there are No-Action Classes to serve as placeholder
    """

    cdef double resolution, angle_step, angle_step_sin, angle_step_cos
    cdef double feed, default_speed, speed
    cdef int autorun, tool
    cdef list commands
    cdef object spindle, gui_cb, transformer
    cdef object __caller, __linear_move
    cdef public dict motors
    cdef public object position

    def __init__(self, double resolution, int default_speed, int autorun):
        """
        initialize Controller Object
        @param
        resolution -> 1.0 means 1 step 1 mm
            so gcode is given in mm, so value in mm times resolution is the amount of steps
        default_speed -> default rotation speed for spindle
            TODO -> should be in Spindle class
        autorun -> in True perform motor commands immediately
            if False, motor command are stored in self.commands
            and can be executed independently
        """
        self.default_speed = default_speed
        self.resolution = resolution
        self.autorun = autorun
        # set function according to autorun or not,
        # to prevent if switches in functions
        if self.autorun is True:
            self.__caller = self.__caller_autorun
        else:
            self.__caller = self.__caller_norun
        # initialize position
        self.position = Point3d(0, 0, 0)
        # defaults to absolute movements
        self.__linear_move = self.__linear_move_abs
        # defaults to millimeter
        # DELETE self.unit = "millimeter"
        # motors dict
        self.motors = {}
        self.spindle = None
        # GUI Callback method, called after every g-command
        self.gui_cb = None
        # Feed Rate
        self.feed = 0
        # Speed
        self.speed = 0
        # Tool
        self.tool = 1
        # define minimal arc step
        self.angle_step = math.pi / 180 
        self.angle_step_sin = math.sin(self.angle_step)
        self.angle_step_cos = math.cos(self.angle_step)
        # optional a tranforming function
        self.transformer = None
        # list of motor commands
        self.commands = []

    def add_spindle(self, spindle_object):
        """add spindle to controller"""
        self.spindle = spindle_object

    def add_motor(self, axis, motor_object):
        """add specific axis motor to controller
        axis should be named with capitalized letters of X, Y, Z"""
        assert axis in ("X", "Y", "Z")
        self.motors[axis] = motor_object

    def add_transformer(self, transformer):
        """add transformer"""
        self.transformer = transformer

    def set_gui_cb(self, gui_cb):
        """
        GUI Callback method, should be called after every step to inform GUI about changes
        """
        self.gui_cb = gui_cb

    def get_position(self):
        """return own position"""
        return(self.position)

    # GCommands
    # for every G-Command a method
    def F(self, feed_str):
        """Set Feed Rate"""
        self.feed = float(feed_str)

    def S(self, speed_str):
        """Set Feed Rate"""
        self.speed = int(speed_str)

    def T(self, tool_str):
        """Set Feed Rate"""
        self.tool = int(tool_str)

    def G00(self, *args):
        """rapid motion with maximum speed"""
        self.__linear_move(args[0])
    G0 = G00

    def G01(self, *args):
        """linear motion with given speed"""
        self.__linear_move(args[0])
    G1 = G01

    def G02(self, *args):
        """clockwise helical motion"""
        data = args[0]
        data["F"] = self.default_speed if "F" not in data else data["F"]
        data["P"] = 1 if "P" not in data else data["P"]
        assert type(data["P"]) == int
        self.__arc(data, -1)
    G2 = G02

    def G03(self, *args):
        """counterclockwise helical motion"""
        data = args[0]
        data["F"] = self.default_speed if "F" not in data else data["F"]
        data["P"] = 1 if "P" not in data else data["P"]
        assert type(data["P"]) == int
        self.__arc(data, 1)
    G3 = G03

    def G04(self, *args):
        """Dwell (no motion for P seconds)"""
        logging.info("G04 called with %s", args)
        if "P" in args[0]:
            time.sleep(args[0]["P"])
    G4 = G04

    def G17(self, *args):
        """Select XY Plane"""
        logging.info("G17 called with %s", args)

    def G18(self, *args):
        """Select XZ plane"""
        logging.info("G18 called with %s", args)
 
    def G19(self, *args):
        """Select YZ plane"""
        logging.info("G19 called with %s", args)
 
    def G20(self, *args):
        """Inches"""
        logging.info("G20 called with %s", args)

    def G21(self, *args):
        """Millimeters"""
        logging.info("G21 called with %s", args)

    def G54(self, *args):
        """Select coordinate system"""
        logging.info("G54 called with %s", args)

    def G90(self, *args):
        """Absolute distance mode"""
        logging.info("G90 called with %s", args)
        self.__linear_move = self.__linear_move_abs

    def G91(self, *args):
        """Incremental distance mode"""
        logging.info("G91 called with %s", args)
        self.__linear_move = self.__linear_move_inc

    def G94(self, *args):
        """Units per minute feed rate"""
        logging.info("G94 called with %s", args)

    def M2(self, *args):
        logging.debug("M2 end the program called with %s", args)
        self.__home_and_end()

    def M3(self, *args):
        logging.debug("M3 start the spindle clockwise at speed S called with %s", args)
        data = args[0]
        if "S" in data:
            self.__spindle_caller("rotate", self.spindle.CW, data["S"])
        else: 
            self.__spindle_caller("rotate", self.spindle.CW)
            
    def M4(self, *args):
        logging.debug("M4 start the spindle counter-clockwise at speed S called with %s", args)
        data = args[0]
        if "S" in data:
            self.__spindle_caller("rotate", self.spindle.CCW, data["S"])
        else: 
            self.__spindle_caller("rotate", self.spindle.CCW)

    def M5(self, *args):
        logging.debug("M5 stop the spindle called with %s", args)
        self.spindle.unhold()
        self.__spindle_caller("unhold")

    def M6(self, *args):
        logging.debug("M6 Tool change called with %s", args)

    def M7(self, *args):
        logging.debug("M7 turn mist coolant on called with %s", args)

    def M8(self, *args):
        logging.debug("M8 turn flood coolant on called with %s", args)

    def M9(self, *args):
        logging.debug("M9 turn all collant off called with %s", args)

    def M30(self, *args):
        logging.debug("M30 end the program called with %s", args)
        self.__home_and_end()

    cdef __home_and_end(self):
        """called at end of G-Code commands
        to move to origin and poweroff everything"""
        # back to origin
        self.__goto(Point3d(0, 0, 0))
        # unhold everything
        for axis in self.motors.keys():
            self.__motor_caller(axis, "unhold")
        # stop spindle
        self.__spindle_caller("unhold")

    cdef object __get_center(self, object target, double radius):
        """
        helper method for G02 and G03 called to get center of arc
        get center from target on circle and radius given
        """
        cdef object distance = target - self.position
        cdef double h_x2_div_d = math.sqrt(4 * radius **2 - distance.X**2 - distance.Y**2) / math.sqrt(distance.X**2 + distance.Y**2)
        cdef double i = (distance.X - (distance.Y * h_x2_div_d))/2
        cdef double j = (distance.Y + (distance.X * h_x2_div_d))/2
        return(Point3d(i, j, 0.0))

    cdef __arc(self, dict data, int ccw):
        """
        given actual position and 
        x, y, z relative position of stop point on arc
        i, j, k relative position of center

        i am not sure if this implementation is straight forward enough
        semms more hacked than mathematically correct
        TODO: Improve
        """
        # correct some values if not specified
        if "X" not in data: data["X"] = self.position.X
        if "Y" not in data: data["Y"] = self.position.Y
        if "Z" not in data: data["Z"] = self.position.Z
        if "I" not in data: data["I"] = 0.0
        if "J" not in data: data["J"] = 0.0
        if "K" not in data: data["K"] = 0.0
        # arc endpoint at X/Y/Z
        cdef object target = Point3d(data["X"], data["Y"], data["Z"])
        # calculate endpoint of arc, either given in
        # I/J/K position or R
        cdef object offset
        if "R" in data:
            offset = self.__get_center(target, data["R"])
        else:
            offset = Point3d(data["I"], data["J"], data["K"])
        #startpoint and endpoint are known, so calculate midpoint
        cdef object center = self.position + offset
        # get the angle bewteen
        # unit vector from mid to target
        # unit vector from mid to actual position
        cdef object target_vec = (target - center).unit()
        cdef object position_vec = (self.position - center).unit()
        cdef double angle = target_vec.angle_between(position_vec)
        # next trigonometry
        #logging.debug("angle between target and position is %s", target_vec.angle_between(position_vec))
        cdef double start_angle
        cdef double stop_angle
        cdef double angle_step = math.pi / 180
        # shortcut, if angle is smaller than angle_step,
        # make a straight line
        if abs(angle) <= self.angle_step:
            self.__goto(target)
            return
        # according to count/non-counter clockwise
        # and actual position and target
        # calculate starting and stop angle adn stepsize
        cdef double target_angle = target_vec.angle()
        cdef double position_angle = position_vec.angle()
        if ccw == 1:
            # G3 movement
            # angle step will be added
            # target angle should be greater than position angle
            # if not so correct target_angle = 2 * math.pi - target_angle 
            if target_angle < position_angle:
                start_angle = position_angle
                stop_angle = 2 * math.pi - target_angle
            else:
                start_angle = position_angle
                stop_angle = target_angle
        else:
            # G2 movement
            # so clockwise, step must be negative
            # target angle should be smaller than position angle
            # if not correct target_angle = 2 * math.pi - target_angle
            angle_step = -angle_step
            # should go from position to target
            if target_angle > position_angle:
                start_angle = position_angle
                stop_angle = 2 * math.pi - target_angle
            else:
                start_angle = position_angle
                stop_angle = target_angle
        # if start equals end this indicates a full circle
        if start_angle == stop_angle:
            stop_angle += math.pi * 2
        # well done, positions and angle are known
        # what is the stepsize in degree
        cdef int angle_steps = abs(int((start_angle - stop_angle) / angle_step))
        cdef object inv_offset = offset * -1
        angle = angle_step * angle_steps
        cdef double cos_theta = math.cos(angle_step)
        cdef double sin_theta = math.sin(angle_step)
        while abs(angle) > abs(angle_step):
            inv_offset = inv_offset.rotated_z_fast(angle_step, cos_theta, sin_theta)
            self.__goto(center + inv_offset)
            angle -= angle_step
        # rotate last tiny fraction left
        inv_offset = inv_offset.rotated_Z(angle_step)
        self.__goto(center + inv_offset)
        self.__drift_management(target)

    cdef __drift_management(self, object target):
        """
        can be called to get closer to target
        drift is calculated as vector between actual position and target
        the length of the drift vector should always be under 1

        the remaining drift vector is moved to get as close as possible to target

        Note: 
            there will always be a small gap between actual position and wanted target,
            because motors only can move in whole steps
            a second source of error will be floating point operations
        """
        drift = self.position - target
        self.__goto(target)

    cdef int __motor_steps(self, data):
        """
        method to initialize single steps on the different axis
        the size here is already steps, not units as mm or inches
        scaling is done in __goto
        """
        cdef double step
        for axis in ("X", "Y", "Z"):
            step = data.get_axis(axis)
            if step != 0.0 : 
                self.__motor_caller(axis, "move_float", 1 if step > 0.0 else -1, abs(step))

    def __motor_caller(self, str axis, str function, *args):
        """
        wrapper to get all method calles to external motor objects
        to implement caching, and advanced features
        """
        method_to_call = getattr(self.motors[axis], function)
        self.__caller(method_to_call, *args)

    def __spindle_caller(self, function, *args):
        """
        wrapper to get all method calles to external spindle object
        to implement caching, and advanced features
        """
        method_to_call = getattr(self.spindle, function)
        self.__caller(method_to_call, *args)

    def __caller_autorun(self, method_to_call, *args):
        """
        this is the only method which communicated with external objects
        like motors or spindles.
        this is the point to implement autorun

        autorun=True version
        """
        self.gui_cb()
        self.commands.append((method_to_call, args))
        method_to_call(*args)

    def __caller_norun(self, method_to_call, *args):
        """
        this is the only method which communicated with external objects
        like motors or spindles.
        this is the point to implement autorun
        
        autrun=False version
        """
        self.gui_cb()
        self.commands.append((method_to_call, args))

    cpdef run(self):
        """run all commands in self.commands"""
        for (method_to_call, args) in self.commands:
            logging.debug("%s(%s)", method_to_call, args)
            method_to_call(*args)

    cdef __goto(self, object target):
        """
        calculate vector between actual position and target position
        scale this vector to motor-steps-units und split the
        vector in unit vectors with length 1, to control single motor steps
        """
        cdef object move_vec_steps
        cdef object move_vec_steps_unit
        cdef object move_vec
        cdef double length
        # nothing to move?
        if target == self.position:
            return(0)
        else:
            # vector from position to target in mm
            move_vec = target - self.position
        # maybe some tranformation and scaling ?
        move_vec = self.transformer.transform(move_vec)
        # scale from mm to steps unit 
        move_vec_steps = move_vec * self.resolution
        # and not get the unit vector, length=1
        move_vec_steps_unit = move_vec_steps.unit()
        # use while loop the get to the exact value
        length = move_vec_steps.length()
        while length > 1.0:
            self.__motor_steps(move_vec_steps_unit)
            length -= 1
            move_vec_steps = move_vec_steps - move_vec_steps_unit
        # the last fraction left
        self.__motor_steps(move_vec_steps)
        # set own position to target, done
        self.position = target

    cdef set_speed(self, dict data):
        """
        set speed, if data["F"] is given, defaults to default_speed if not specified
        speed is actually not implemented, everything at maximum speed
        """
        if "F" in data:
            self.speed = data["F"]
        else: 
            self.speed = self.default_speed

    def __linear_move_inc(self, data):
        """
        incremental movement, parameter represents relative position change
        move to given x,y ccordinates
        x,y are given relative to actual position

        so to move in both direction at the same time,
        parameter x or y has to be sometime float
        """
        cdef object target = Point3d(0, 0, 0)
        for axis in ("X", "Y", "Z"):
            if axis in data:
                target.set_axis(axis, self.position.get_axis(axis) + data[axis])
            else:
                target.set_axis(axis, self.position.get_axis(axis))
        self.__goto(target)

    def __linear_move_abs(self, data):
        """
        absolute movement to position
        args[X,Y,Z] are interpreted as absolute positions
        it is not necessary to give alle three axis, when no value is
        present, there is not movement on this axis
        """
        target = Point3d(0.0, 0.0, 0.0)
        for axis in ("X", "Y", "Z"):
            if axis in data:
                target.set_axis(axis, data[axis])
            else:
                target.set_axis(axis, self.position.get_axis(axis))
        self.__goto(target)

    def __getattr__(self, name):
        """handle unknwon methods"""
        def method(*args):
            logging.info("tried to handle unknown method " + name)
            if args:
                logging.info("it had arguments: " + str(args))
        return method
