#!/usr/bin/python

from RPi import GPIO
import time
import sys

fg_pin = 7
ld_pin = 8

GPIO.setmode(GPIO.BCM)
GPIO.setup(fg_pin, GPIO.OUT)
GPIO.setup(ld_pin, GPIO.OUT)
print "trying static levels fg=0, ld=0"
GPIO.output(fg_pin, 0)
GPIO.output(ld_pin, 0)
raw_input("press any key")
print "trying static levels fg=1, ld=0"
GPIO.output(fg_pin, 1)
GPIO.output(ld_pin, 0)
raw_input("press any key")
print "trying static levels fg=0, ld=1"
GPIO.output(fg_pin, 0)
GPIO.output(ld_pin, 1)
raw_input("press any key")
print "trying static levels fg=1, ld=1"
GPIO.output(fg_pin, 1)
GPIO.output(ld_pin, 1)
raw_input("press any key")

print "Now pulsing ld, fg=1 100 times, 1ms interleave"
GPIO.output(fg_pin, 1)
for _ in range(100):
    GPIO.output(ld_pin, 1)
    time.sleep(1/1000)
    GPIO.output(ld_pin, 0)
    time.sleep(1/1000)

print "Now pulsing fg, ld=1 100 times, 1ms interleave"
GPIO.output(ld_pin, 1)
for _ in range(100):
    GPIO.output(fg_pin, 1)
    time.sleep(1/1000)
    GPIO.output(fg_pin, 0)
    time.sleep(1/1000)

GPIO.output(fg_pin, 0)
GPIO.output(ld_pin, 0)
time.sleep(1)
GPIO.cleanup()
