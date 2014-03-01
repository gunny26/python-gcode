#/usr/bin/python
# -*- coding: utf-8 -*-
#
# parse Gcode
#
"""
Motor Classes for Controller
"""

try:
    import RPi.GPIO as GPIO
except ImportError:
    from FakeGPIO import FakeGPIO as GPIO
import logging
logging.basicConfig(level=logging.INFO, format="%(message)s")
import time

class Motor(object):
    """
    Abstract Class for Motor
    usually you have to overwrite __move and unhold methods
    """

    def __init__(self, max_position, min_position, delay, sos_exception=True):
        self.max_position = max_position
        self.min_position = min_position
        self.delay = delay
        self.sos_exception = sos_exception
        # define
        self.position = 0
        self.float_position = 0.0
        # timekeeping
        self.last_step_time = time.time()

    def move_float(self, direction, float_step):
        """
        this method is called from controller
        float_step is bewtween 0.0 < 1.0
        """
        #logging.debug("move_float called with %d, %f", direction, float_step)
        assert type(direction) == int
        assert (direction == -1) or (direction == 1)
        assert 0.0 <= float_step <= 1.0
        # check between max and min
        temp = float_step * direction
        if not (self.min_position < temp < self.max_position):
            if self.sos_exception is True:
                raise(StandardError("Boundary reached!"))
            else:
                logging.error("%s < %s < %s not true", self.min_position, temp, self.max_position)
        # next step should not before self.last_step_time + self.delay
        time_gap = self.last_step_time + self.delay - time.time()
        if time_gap > 0:
            time.sleep(time_gap)
        self.float_position += (float_step * direction)
        distance = abs(self.position - self.float_position)
        if distance >= 1.0:
            #logging.debug("initializing full step, distance %s > 1.0", distance) 
            self._move(direction)
        #else:
            #logging.debug("distance %s to small to initialize full step", distance)
        # remember last_step_time
        self.last_step_time = time.time()
        distance = abs(self.float_position - self.position)
        #logging.debug("int_position = %d : float_position = %f : distance = %f", self.position, self.float_position, distance)
        # final distance between exact float and real int must be lesser than 1.0
        assert distance < 1.0

    def _move(self, direction):
        """
        move number of full integer steps
        """
        #logging.debug("Moving Motor One step in direction %s", direction)
        #logging.debug("Motor accuracy +/- %s", self.position - self.float_position)
        self.position += direction

    def unhold(self):
        """release power"""
        #logging.info("Unholding Motor Coils")
        pass

    def get_position(self):
        """return real position as int"""
        return(self.position)

    def get_float_position(self):
        """return exact position as float"""
        return(self.float_position)



class LaserMotor(Motor):
    """Laser Motor, reactive if axis moves negative"""

    def __init__(self, laser_pin, max_position, min_position, delay):
        """
        GPIO like Object for laser_pin
        max_position value
        min_position value
        delay between phase changes
        """
        Motor.__init__(self, max_position, min_position, delay)
        self.laser_pin = laser_pin
        self.laser_pin.setup(GPIO.OUT)
        self.unhold()
 
    def _move(self, direction):
        """move number of full integer steps"""
        self.position += direction
        # turn on laser if position < 0
        if self.position < 0.0:
            self.laser_pin.output(1)
        else:
            self.laser_pin.output(0)

    def unhold(self):
        """power off"""
        logging.info("Power off laser")
        self.laser_pin.output(0)


class BipolarStepperMotor(Motor):
    """
    Class to represent a bipolar stepper motor
    it could only with on one dimension, forward or backwards

    cloil -> set(a1, a2, b1, b2) of GPIO Pins where these connectors are patched
    delay -> int(milliseconds to wait between moves
    max_position -> int(maximum position) is set to safe value of 1
    min_position -> int(minimum position) is set to 0
        b1
    a1      a1
        b2

    following seuqnece is possible (a1, a2, b1, b2)

    low torque mode
    1 0 0 0 a1
    0 0 1 0 b1
    0 1 0 0 a2
    0 0 0 1 b2
    
    high torque mode - full step mode
    1 0 1 0 between a1/b1
    0 1 1 0 between b1/a2
    0 1 0 1 between a2/b2
    1 0 0 1 between b2/a1

    mixed torque mode - half step mode
    1 0 0 0 a1
    1 0 1 0 between a1/b1
    0 0 1 0 b1
    0 1 1 0 between b1/a2
    0 1 0 0 a2
    0 1 0 1 between a2/b2
    0 0 0 1 b2
    1 0 0 1 between b2/a1

    """
    # low torque mode - also low power as only one coil is powered
    SEQUENCE_LOW = ((1,0,0,0), (0,0,1,0), (0,1,0,0), (0,0,0,1))
    # high torque - full step mode
    SEQUENCE_HIGH = ((1,0,1,0), (0,1,1,0), (0,1,0,1), (1,0,0,1))
    # mixed torque - half step mode
    SEQUENCE_MIXED = ((1,0,0,0), (1,0,1,0), (0,0,1,0), (0,1,1,0), (0,1,0,0), (0,1,0,1), (0,0,0,1), (1,0,0,1))
    # ok
    SEQUENCE = SEQUENCE_MIXED

    def __init__(self, coils, max_position, min_position, delay):
        """
        coils a set of for GPIO like object to represent a1, a2, b1, b2 connection to motor
        max_position
        min_position
        """
        Motor.__init__(self, max_position, min_position, delay)
        self.coils = coils
        # define coil pins as output
        for pin in self.coils:
            pin.setup(GPIO.OUT)
            pin.output(0)
        self.num_sequence = len(self.SEQUENCE)
        self.unhold()

    def _move(self, direction):
        """
        move to given direction number of steps, its relative
        delay_faktor could be set, if this Motor is connected to a controller
        which moves also another Motor
        """
        phase = self.SEQUENCE[self.position % self.num_sequence]
        counter = 0
        for pin in self.coils:
            pin.output(phase[counter])
            counter += 1
        self.position += direction

    def unhold(self):
        """
        sets any pin of motor to low, so no power is needed
        """
        for pin in self.coils:
            pin.output(GPIO.LOW)

class UnipolarStepperMotor(Motor):
    """
    Class to represent a unipolar stepper motor
    it could only with on one dimension, forward or backwards

    cloil -> set(a1, a2, b1, b2) of GPIO Pins where these connectors are patched
    delay -> int(milliseconds to wait between moves
    max_position -> int(maximum position) is set to safe value of 1
    min_position -> int(minimum position) is set to 0
        b1
    a1      a1
        b2

    following seuqnece is possible (a1, a2, b1, b2)

    low torque mode
    1 0 0 0 a1
    0 0 1 0 b1
    0 1 0 0 a2
    0 0 0 1 b2
    
    high torque mode - full step mode
    1 0 1 0 between a1/b1
    0 1 1 0 between b1/a2
    0 1 0 1 between a2/b2
    1 0 0 1 between b2/a1

    mixed torque mode - half step mode
    1 0 0 0 a1
    1 0 1 0 between a1/b1
    0 0 1 0 b1
    0 1 1 0 between b1/a2
    0 1 0 0 a2
    0 1 0 1 between a2/b2
    0 0 0 1 b2
    1 0 0 1 between b2/a1

    """
    # low torque mode - also low power as only one coil is powered
    SEQUENCE_LOW = ((1,0,0,0), (0,0,1,0), (0,1,0,0), (0,0,0,1))
    # high torque - full step mode
    SEQUENCE_HIGH = ((1,0,1,0), (0,1,1,0), (0,1,0,1), (1,0,0,1))
    # mixed torque - half step mode
    SEQUENCE_MIXED = ((1,0,0,0), (1,0,1,0), (0,0,1,0), (0,1,1,0), (0,1,0,0), (0,1,0,1), (0,0,0,1), (1,0,0,1))
    # ok
    SEQUENCE = SEQUENCE_MIXED

    def __init__(self, coils, max_position, min_position, delay):
        """
        coils a set of for GPIO like object to represent a1, a2, b1, b2 connection to motor
        max_position
        min_position
        delay between phase changes in seconds
        """
        Motor.__init__(self, max_position, min_position, delay)
        self.coils = coils
        # define coil pins as output
        for pin in self.coils:
            pin.setup(GPIO.OUT)
            pin.output(0)
        self.num_sequence = len(self.SEQUENCE)
        self.unhold()

    def _move(self, direction):
        """
        move to given direction number of steps, its relative
        delay_faktor could be set, if this Motor is connected to a controller
        which moves also another Motor
        """
        phase = self.SEQUENCE[self.position % self.num_sequence]
        counter = 0
        for pin in self.coils:
            pin.output(phase[counter])
            counter += 1
        self.position += direction

    def unhold(self):
        """
        sets any pin of motor to low, so no power is needed
        """
        for pin in self.coils:
            pin.output(GPIO.LOW)
    
    def get_phase(self):
        """returns actual phase in sequence"""
        return(self.SEQUENCE[self.position % self.num_sequence])

class UnipolarStepperMotorOnOff(Motor):
    """
    Same as other motors, but with only two positions

    something positive = goto position ON
    zero or negative = goto position OFF

    """
    # low torque mode - also low power as only one coil is powered
    SEQUENCE_LOW = ((1,0,0,0), (0,0,1,0), (0,1,0,0), (0,0,0,1))
    # high torque - full step mode
    SEQUENCE_HIGH = ((1,0,1,0), (0,1,1,0), (0,1,0,1), (1,0,0,1))
    # mixed torque - half step mode
    SEQUENCE_MIXED = ((1,0,0,0), (1,0,1,0), (0,0,1,0), (0,1,1,0), (0,1,0,0), (0,1,0,1), (0,0,0,1), (1,0,0,1))
    # ok
    SEQUENCE = SEQUENCE_MIXED

    def __init__(self, coils, on_position, on_direction, delay):
        """
        coils a set of for GPIO like object to represent a1, a2, b1, b2 connection to motor
        max_position
        min_position
        delay between phase changes in seconds
        """
        Motor.__init__(self, on_position, 0, delay)
        self.coils = coils
        self.on_position = on_position
        self.on_direction = on_direction
        # define coil pins as output
        for pin in self.coils:
            pin.setup(GPIO.OUT)
            pin.output(0)
        self.state = 0
        self.num_sequence = len(self.SEQUENCE)
        self.unhold()

    def move_float(self, direction, float_step):
        """
        this method is called from controller
        float_step is bewtween 0.0 < 1.0
        """
        #logging.debug("move_float called with %d, %f", direction, float_step)
        assert type(direction) == int
        assert (direction == -1) or (direction == 1)
        assert 0.0 <= float_step <= 1.0
        logging.error("state: %s, float_position: %s, position: %s", self.state, self.float_position, self.position)
        # next step should not before self.last_step_time + self.delay
        time_gap = self.last_step_time + self.delay - time.time()
        if time_gap > 0:
            time.sleep(time_gap)
        self.float_position += (float_step * direction)
        # if position > 0 and now in OFF position
        if self.float_position > 0.0 and self.state == 0:
            for _ in range(self.on_position):
                self._move(self.on_direction)
                time.sleep(self.delay)
            # goto position ON
            self.state = 1
        # otherwise
        if self.float_position == 0.0 and self.state == 1:
            for _ in range(self.on_position):
                self._move(-self.on_direction)
                time.sleep(self.delay)
            # goto position OFF
            self.state = 0
        logging.error("state: %s, float_position: %s, position: %s", self.state, self.float_position, self.position)
        # remember last_step_time
        self.last_step_time = time.time()

    def _move(self, direction):
        """
        move to given direction number of steps, its relative
        delay_faktor could be set, if this Motor is connected to a controller
        which moves also another Motor
        """
        phase = self.SEQUENCE[self.position % self.num_sequence]
        counter = 0
        for pin in self.coils:
            pin.output(phase[counter])
            counter += 1
        self.position += direction

    def unhold(self):
        """
        sets any pin of motor to low, so no power is needed
        """
        for pin in self.coils:
            pin.output(GPIO.LOW)
    
    def get_phase(self):
        """returns actual phase in sequence"""
        return(self.SEQUENCE[self.position % self.num_sequence])


class UnipolarStepperMotorTwoWire(Motor):
    """
    Class to represent a bipolar stepper motor
    it could only with on one dimension, forward or backwards

    cloil -> set(a1, a2, b1, b2) of GPIO Pins where these connectors are patched
    delay -> int(milliseconds to wait between moves
    max_position -> int(maximum position) is set to safe value of 1
    min_position -> int(minimum position) is set to 0
        b1
    a1      a1
        b2

    following seuqnece is possible (a1, a2, b1, b2)

    low torque mode
    1 0 0 0 a1
    0 0 1 0 b1
    0 1 0 0 a2
    0 0 0 1 b2
    
    high torque mode - full step mode
    1 0 1 0 between a1/b1
    0 1 1 0 between b1/a2
    0 1 0 1 between a2/b2
    1 0 0 1 between b2/a1

    mixed torque mode - half step mode
    1 0 0 0 a1
    1 0 1 0 between a1/b1
    0 0 1 0 b1
    0 1 1 0 between b1/a2
    0 1 0 0 a2
    0 1 0 1 between a2/b2
    0 0 0 1 b2
    1 0 0 1 between b2/a1

    """
    # with two wire, there is only one sequence possible, results in full step mode
    SEQUENCE = ((1,0), (1,1), (0,1), (0,0))

    def __init__(self, coils, max_position, min_position, delay):
        """
        coils a set of two GPIO like object to represent a1 and b1 connections to motor
        max_position
        min_position
        delay between phase changes in seconds
        """
        Motor.__init__(self, max_position, min_position, delay)
        assert len(coils) == 2
        self.coils = coils
        # define coil pins as output
        for pin in self.coils:
            pin.setup(GPIO.OUT)
            pin.output(0)
        self.num_sequence = len(self.SEQUENCE)
        self.unhold()

    def _move(self, direction):
        """
        move to given direction number of steps, its relative
        delay_faktor could be set, if this Motor is connected to a controller
        which moves also another Motor
        """
        phase = self.SEQUENCE[self.position % self.num_sequence]
        counter = 0
        for pin in self.coils:
            pin.output(phase[counter])
            counter += 1
        self.position += direction

    def unhold(self):
        """
        sets any pin of motor to low, so no power is needed
        """
        for pin in self.coils:
            pin.output(GPIO.LOW)
    
    def get_phase(self):
        """returns actual phase in sequence"""
        return(self.SEQUENCE[self.position % self.num_sequence])
