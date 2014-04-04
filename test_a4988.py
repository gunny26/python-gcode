#!/usr/bin/python

from RPi import GPIO
import time
import sys

dir_pin = 24
step_pin = 23
sleep_pin = 7 
reset_pin = 8
enable_pin = 25


GPIO.setmode(GPIO.BCM)
GPIO.setup(step_pin, GPIO.OUT)
GPIO.setup(dir_pin, GPIO.OUT)
GPIO.output(dir_pin, 0)
# do a reset
GPIO.setup(reset_pin, GPIO.OUT)
GPIO.output(reset_pin, 0)
GPIO.output(reset_pin, 1)
GPIO.setup(sleep_pin, GPIO.OUT)
GPIO.output(sleep_pin, 1)
# sleep and reset have to be high
GPIO.setup(enable_pin, GPIO.OUT)
GPIO.output(enable_pin, 0)
# enable has to be low

try:
    GPIO.output(dir_pin, 0)
    for _ in range(int(sys.argv[2])):
        GPIO.output(step_pin, 1)
	# time.sleep(0.0001)
        GPIO.output(step_pin, 0)
        time.sleep(float(sys.argv[1]))
except KeyboardInterrupt:
    GPIO.cleanup()
GPIO.output(dir_pin, 0)
GPIO.output(step_pin, 0)
GPIO.cleanup()
