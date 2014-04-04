#!/usr/bin/python
"""
test program for a4988 breakoutboard

only two control pins are needed

DIR -> to set direction
STEP -> to send impulses to step

ENABLED -> GND
RESET -> GND
SLEEP -> GND

5V -> VDD
GND -> GND

also Motor Power has to be connected
VMOT > 8V - 32V
GND -> GND
"""
from RPi import GPIO
import time
import sys

sleep_pin = 24
reset_pin = 23
dir_pin = 7
step_pin = 8

GPIO.setmode(GPIO.BCM)
GPIO.setup(step_pin, GPIO.OUT)
GPIO.setup(dir_pin, GPIO.OUT)
GPIO.setup(sleep_pin, GPIO.OUT)
GPIO.setup(reset_pin, GPIO.OUT)

# reset driver
GPIO.output(reset_pin, 0)
GPIO.output(reset_pin, 1)
time.sleep(0.1)
GPIO.output(sleep_pin, 1)

GPIO.output(dir_pin, 0)

direction = int(sys.argv[1])
step_interval = float(sys.argv[2])
duration_s = int(sys.argv[3])

try:
    GPIO.output(dir_pin, direction)
    start = time.time()
    while (start + duration_s) >= time.time():
        GPIO.output(step_pin, 1)
	# time.sleep(0.0001)
        GPIO.output(step_pin, 0)
        time.sleep(step_interval)
except KeyboardInterrupt:
    GPIO.cleanup()
GPIO.output(dir_pin, 0)
GPIO.output(step_pin, 0)
GPIO.cleanup()
