#/usr/bin/python
# -*- coding: utf-8 -*-
#
# parse Gcode
#
#cython: profile=True

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


cdef class ControllerStats(object):
    """
    Object to hold some statistical informations about Controller
    should be called on every step made
    """
    cdef int steps
    cdef double max_x, min_x, max_y, min_y, max_z, min_z, start_time, duration, avg_step_time

    def __init__(self):
        """__init__"""
        self.steps = 0
        self.max_x = 0.0
        self.min_x = 0.0
        self.max_y = 0.0
        self.min_y = 0.0
        self.max_z = 0.0
        self.min_z = 0.0
        self.start_time = time.time()
        self.duration = 0.0
        self.avg_step_time = 0.0

    cpdef int update(self, object controller_obj):
        """update internal stats counters"""
        # store min / max for X/Y/Z Axis
        if controller_obj.position.X > self.max_x:
            self.max_x = controller_obj.position.X
        if controller_obj.position.X < self.min_x:
            self.min_x = controller_obj.position.X
        if controller_obj.position.Y > self.max_y:
            self.max_y = controller_obj.position.Y
        if controller_obj.position.Y < self.min_y:
            self.min_y = controller_obj.position.Y
        if controller_obj.position.Z > self.max_z:
            self.max_z = controller_obj.position.Z
        if controller_obj.position.X < self.min_z:
            self.min_z = controller_obj.position.Z
        # store steps and time
        self.steps += 1
        self.duration = time.time() - self.start_time
        self.avg_step_time = self.duration / self.steps
        return(0)

    def __str__(self):
        return(str(self.__dict__))


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
    cdef dict motors
    cdef list commands
    cdef object position, move, spindle, gui_cb, stats, transformer

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
        # initialize position
        self.position = Point3d(0, 0, 0)
        # defaults to absolute movements
        self.move = self.__linear_move_abs
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
        # statistics
        self.stats = ControllerStats()
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

#    def get_direction(self, number):
#        """
#        helper class to get direction of number
#        returns 1 for positive numbers, and -1 for negative numnbers
#        """
#        return(int(number/abs(number)))

    # GCommands
    # for every G-Command a method
    def F(self, feed_str):
        """Set Feed Rate"""
        #logging.info("G00 called with %s", args)
        self.feed = float(feed_str)

    def S(self, speed_str):
        """Set Feed Rate"""
        #logging.info("G00 called with %s", args)
        self.speed = int(speed_str)

    def T(self, tool_str):
        """Set Feed Rate"""
        #logging.info("G00 called with %s", args)
        self.tool = int(tool_str)

    def G00(self, *args):
        """rapid motion with maximum speed"""
        #logging.info("G00 called with %s", args)
        self.move(args[0])
    G0 = G00

    def G01(self, *args):
        """linear motion with given speed"""
        #logging.info("G01 called with %s", args)
        # self.set_speed(data)
        self.move(args[0])
    G1 = G01

    def G02(self, *args):
        """clockwise helical motion"""
        #logging.info("G02 called with %s", args)
        data = args[0]
        data["F"] = self.default_speed if "F" not in data else data["F"]
        data["P"] = 1 if "P" not in data else data["P"]
        assert type(data["P"]) == int
        self.__arc(data, -1)
    G2 = G02

    def G03(self, *args):
        """counterclockwise helical motion"""
        #logging.info("G03 called with %s", args)
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
        self.move = self.__linear_move_abs

    def G91(self, *args):
        """Incremental distance mode"""
        logging.info("G91 called with %s", args)
        self.move = self.__linear_move_inc

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
            # self.spindle.rotate(self.spindle.CW, data["S"])
            self.__spindle_caller("rotate", self.spindle.CW, data["S"])
        else: 
            #self.spindle.rotate(self.spindle.CW)
            self.__spindle_caller("rotate", self.spindle.CW)
            
    def M4(self, *args):
        logging.debug("M4 start the spindle counter-clockwise at speed S called with %s", args)
        data = args[0]
        if "S" in data:
            #self.spindle.rotate(self.spindle.CCW, data["S"])
            self.__spindle_caller("rotate", self.spindle.CCW, data["S"])
        else: 
            #self.spindle.rotate(self.spindle.CCW)
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

    def __home_and_end(self):
        """called at end of G-Code commands
        to move to origin and poweroff everything"""
        # back to origin
        self.__goto(Point3d(0, 0, 0))
        # unhold everything
        for axis in self.motors.keys():
            self.__motor_caller(axis, "unhold")
        # stop spindle
        self.__spindle_caller("unhold")
        # logging.error(self.stats)
        # raise ControllerExit("M30 received, end of program")

    def __get_center(self, target, radius):
        """
        helper method for G02 and G03 called to get center of arc
        get center from target on circle and radius given
        """
        logging.info("__get_center called with %s", (target, radius))
        distance = target - self.position
        # logging.info("x=%s, y=%s, r=%s", x, y, r)
        h_x2_div_d = math.sqrt(4 * radius **2 - distance.X**2 - distance.Y**2) / math.sqrt(distance.X**2 + distance.Y**2)
        i = (distance.X - (distance.Y * h_x2_div_d))/2
        j = (distance.Y + (distance.X * h_x2_div_d))/2
        return(Point3d(i, j, 0.0))

    def __arc(self, *args):
        """
        given actual position and 
        x, y, z relative position of stop point on arc
        i, j, k relative position of center

        i am not sure if this implementation is straight forward enough
        semms more hacked than methematically correct
        TODO: Improve
        """
        #logging.info("__arc called with %s", args)
        #logging.debug("Actual Position at %s", self.position)
        data = args[0]
        ccw = args[1]
        # correct some values if not specified
        if "X" not in data: data["X"] = self.position.X
        if "Y" not in data: data["Y"] = self.position.Y
        if "Z" not in data: data["Z"] = self.position.Z
        if "I" not in data: data["I"] = 0.0
        if "J" not in data: data["J"] = 0.0
        if "K" not in data: data["K"] = 0.0
        target = Point3d(data["X"], data["Y"], data["Z"])
        #logging.debug("Endpoint of arc at %s", target)
        # either R or IJK are given
        offset = None
        if "R" in data:
            offset = self.__get_center(target, data["R"])
        else:
            offset = Point3d(data["I"], data["J"], data["K"])
        #logging.debug("Offset = %s", offset)
        center = self.position + offset
        #logging.debug("Center of arc at %s", center)
        # DELETE radius = offset.length()
        #logging.debug("Radius: %s", radius)
        # get the angle bewteen the two vectors
        target_vec = (target - center).unit()
        #logging.debug("target_vec : %s; angle %s", target_vec, target_vec.angle())
        position_vec = (self.position - center).unit()
        #logging.debug("position_vec : %s; angle %s", position_vec, position_vec.angle())
        angle = target_vec.angle_between(position_vec)
        #logging.debug("angle between target and position is %s", target_vec.angle_between(position_vec))
        start_angle = None
        stop_angle = None
        angle_step = math.pi / 180
        # shortcut, if angle is very small, make a straight line
        if abs(angle) <= self.angle_step:
            self.__goto(target)
            return
        if ccw == 1:
            # G3 movement
            # angle step will be added
            # target angle should be greater than position angle
            # if not so correct target_angle = 2 * math.pi - target_angle 
            if target_vec.angle() < position_vec.angle():
                start_angle = position_vec.angle()
                stop_angle = 2 * math.pi - target_vec.angle()
            else:
                start_angle = position_vec.angle()
                stop_angle = target_vec.angle()
        else:
            # G2 movement
            # so clockwise, step must be negative
            # target angle should be smaller than position angle
            # if not correct target_angle = 2 * math.pi - target_angle
            angle_step = -angle_step
            # should go from position to target
            if target_vec.angle() > position_vec.angle():
                start_angle = position_vec.angle()
                stop_angle = 2 * math.pi - target_vec.angle()
            else:
                start_angle = position_vec.angle()
                stop_angle = target_vec.angle()
        # this indicates a full circle
        if start_angle == stop_angle:
            stop_angle += math.pi * 2
        angle_steps = abs(int((start_angle - stop_angle) / angle_step))
        #logging.debug("Arc from %s rad to %s rad with %s steps in %s radians", start_angle, stop_angle, angle_steps, angle_step)
        inv_offset = offset * -1
        #logging.debug("Inverse Offset vector : %s", inv_offset)
        angle = angle_step * angle_steps
        cos_theta = math.cos(angle_step)
        sin_theta = math.sin(angle_step)
        while abs(angle) > abs(angle_step):
            inv_offset = inv_offset.rotated_z_fast(angle_step, cos_theta, sin_theta)
            self.__goto(center + inv_offset)
            angle -= angle_step
            #logging.debug("angle=%s, start_angle=%s, stop_angle=%s", start_angle + angle, start_angle, stop_angle)
        # rotate last tiny fraction left
        inv_offset = inv_offset.rotated_Z(angle_step)
        self.__goto(center + inv_offset)
        # calculate drift of whole arc
        arc_drift = self.position - target
        #logging.debug("Arc-Drift: Actual=%s, Target=%s, Drift=%s(%s)", self.position, target, arc_drift, arc_drift.length())
        # TODO: changed 19.03 assert arc_drift.length() < Point3d(1.0, 1.0, 1.0).length()
        self.__drift_management(target)

    def __drift_management(self, target):
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
        #logging.debug("Drift-Management-before: Actual=%s, Target=%s, Drift=%s(%s)", self.position, target, drift, drift.length())
        # TODO: changed 19.03 assert drift.length() < Point3d(1.0, 1.0, 1.0).length()
        self.__goto(target)
        drift = self.position - target
        #logging.debug("Drift-Management-after: Actual=%s, Target=%s, Drift=%s(%s)", self.position, target, drift, drift.length())
        assert drift.length() < Point3d(1.0, 1.0, 1.0).length()

    cdef int __motor_steps(self, data):
        """
        method to initialize single steps on the different axis
        the size here is already steps, not units as mm or inches
        scaling is done in __goto
        """
        #logging.debug("__step called with %s", args)
        # data = args[0]
        cdef int direction
        cdef double step
        for axis in ("X", "Y", "Z"):
            step = data.get_axis(axis)
            assert -1.0 <= step <= 1.0
            if step == 0.0 : 
                continue
            direction = int(step/abs(step))
            self.__motor_caller(axis, "move_float", direction, abs(step))
        # self.stats.update(self)

    def __motor_caller(self, str axis, str function, *args):
        """
        wrapper to get all method calles to external motor objects
        to implement caching, and advanced features
        """
        #logging.debug("%s.%s(%s)", axis, function, args)
        method_to_call = getattr(self.motors[axis], function)
        self.__caller(method_to_call, *args)

    def __spindle_caller(self, function, *args):
        """
        wrapper to get all method calles to external spindle object
        to implement caching, and advanced features
        """
        #logging.debug("spindle.%s(%s)", function, args)
        method_to_call = getattr(self.spindle, function)
        self.__caller(method_to_call, *args)

    def __caller(self, method_to_call, *args):
        """
        this is the only method which communicated with external objects
        like motors or spindles.
        this is the point to implement autorun
        """
        # logging.debug("caller(%s, %s)", method_to_call, args)
        self.commands.append((method_to_call, args))
        if self.autorun is True:
            method_to_call(*args)

    def run(self):
        """run all commands in self.commands"""
        for (method_to_call, args) in self.commands:
            logging.info("calling %s(%s)", method_to_call.__name__, args)
            method_to_call(*args)

    cdef __goto(self, object target):
        """
        calculate vector between actual position and target position
        scale this vector to motor-steps-units und split the
        vector in unit vectors with length 1, to control single motor steps
        """
        #logging.debug("__goto called with %s", target)
        #logging.debug("moving from %s mm to %s mm", self.position, target)
        #logging.debug("moving from %s steps to %s steps", self.position * self.resolution, target * self.resolution)
        cdef object move_vec = target - self.position
        if move_vec.length() == 0.0:
            #logging.info("move_vec is zero, nothing to draw")
            # no movement at all
            return
        # steps on each axes to move
        # scale from mm to steps
        cdef object move_vec_steps = move_vec * self.resolution
        # maybe some tranformation and scaling ?
        move_vec_steps = self.transformer.transform(move_vec_steps)
        move_vec_steps_unit = move_vec_steps.unit()
        #logging.error("move_vec_steps_unit=%s", move_vec_steps_unit)
        #logging.error("scaled %s mm to %s steps", move_vec, move_vec_steps)
        #logging.error("move_vec_steps.length() = %s", move_vec_steps.length())        
        # use while loop the get to the exact value
        while move_vec_steps.length() > 1.0:
            self.__motor_steps(move_vec_steps_unit)
            #logging.error("actual length left to draw in tiny steps: %f", move_vec_steps.length())
            move_vec_steps = move_vec_steps - move_vec_steps_unit
        # the last fraction left
        self.__motor_steps(move_vec_steps)
        #if self.surface is not None:
        #    self.gui_cb(target)
        self.position = target
        # after move check controller position with motor positions
        #motor_position = Point3d(self.motors["X"].get_position(), self.motors["Y"].get_position(), self.motors["Z"].get_position())
        # drift = self.position * self.resolution - motor_position
        #logging.debug("Target Drift: Actual=%s; Target=%s; Drift=%s", self.position, target, self.position - target)
        #logging.debug("Steps-Drift : Motor=%s; Drift %s length=%s; Spindle: %s", \
        #    motor_position, drift, drift.length(), self.spindle.get_state())
        # drift should not be more than 1 step
        # drift could be in any direction 0.999...
        # assert drift.length() < Point3d(1.0, 1.0, 1.0).length()
        #logging.info("Unit-Drift: Motor: %s; Drift %s; Spindle: %s", \
        #    motor_position / self.resolution, self.position - motor_position / self.resolution, self.spindle.get_state())
        return(0)

    def set_speed(self, *args):
        """
        set speed, if data["F"] is given, defaults to default_speed if not specified
        speed is actually not implemented, everything at maximum speed
        """
        if "F" in args[0]:
            self.speed = args[0]["F"]
        else: 
            self.speed = self.default_speed

    def __linear_move_inc(self, *args):
        """
        incremental movement, parameter represents relative position change
        move to given x,y ccordinates
        x,y are given relative to actual position

        so to move in both direction at the same time,
        parameter x or y has to be sometime float
        """
        #logging.info("__linear_move_inc called with %s", args)
        if args[0] is None: 
            return
        data = args[0]
        target = Point3d(0, 0, 0)
        for axis in ("X", "Y", "Z"):
            if axis in data:
                target.set_axis(axis, self.position.get_axis(axis) + data[axis])
            else:
                target.set_axis(axis, self.position.get_axis(axis))
        #logging.info("target = %s", target)
        self.__goto(target)

    def __linear_move_abs(self, *args):
        """
        absolute movement to position
        args[X,Y,Z] are interpreted as absolute positions
        it is not necessary to give alle three axis, when no value is
        present, there is not movement on this axis
        """
        #logging.info("__linear_move_abs called with %s", args)
        if args[0] is None: 
            return
        data = args[0]
        target = Point3d(0.0, 0.0, 0.0)
        for axis in ("X", "Y", "Z"):
            if axis in data:
                target.set_axis(axis, data[axis])
            else:
                target.set_axis(axis, self.position.get_axis(axis))
        #logging.info("target = %s", target)
        self.__goto(target)

    def __getattr__(self, name):
        """handle unknwon methods"""
        def method(*args):
            logging.info("tried to handle unknown method " + name)
            if args:
                logging.info("it had arguments: " + str(args))
        return method
