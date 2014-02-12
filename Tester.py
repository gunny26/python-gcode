#!/usr/bin/python

import logging
logging.basicConfig(level=logging.DEBUG)
import RPi.GPIO as GPIO
from Motor import UnipolarStepperMotor as Motor

def gpio_state():
    for gpio in (14, 15, 9, 7):
        GPIO.setup(gpio, GPIO.IN)
        print "%s = %s" % (gpio, GPIO.input(gpio))
        GPIO.setup(gpio, GPIO.OUT)
        GPIO.output(gpio, 0) 



GPIO.cleanup()
GPIO.setmode(GPIO.BCM)
motor = Motor((14, 15, 9, 7), 99999, -99999, 0.005)
try:
    while True:
        # logging.debug("Step %s", motor.get_phase())
        motor.move_float(1, 1.0)
        #gpio_state()
except KeyboardInterrupt:
    pass
GPIO.cleanup()
