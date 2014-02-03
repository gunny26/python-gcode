#!/usr/bin/python

import logging
logging.basicConfig(level=logging.DEBUG)
import RPi.GPIO as GPIO
from Motor import UnipolarStepperMotor as Motor

GPIO.cleanup()
GPIO.setmode(GPIO.BCM)
coilsa = (23, 24, 25, 8)
coilsb = (27, 22, 10, 9)
max_position = 9999
min_position = 0
delay = 0.008
motora = Motor(coilsa, max_position, min_position, delay)
motorb = Motor(coilsb, max_position, min_position, delay)
try:
    while True:
        # logging.debug("Step %s", motor.get_phase())
        motora.move_float(1, 1.0)
        motorb.move_float(-1, 1.0)
except KeyboardInterrupt:
    pass
GPIO.cleanup()
