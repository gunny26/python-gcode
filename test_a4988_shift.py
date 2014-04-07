#!/usr/bin/python
"""
test program for a4988 breakoutboard behind shift register

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
import pyximport
#pyximport.install(pyimport = True) # if you want to compile every py file
pyximport.install()
import logging
logging.basicConfig(level=logging.DEBUG)
# from RPi import GPIO
# use own GPIO implementation
#from GpioObject import GpioObject
#GPIO = GpioObject(0)
from RPi import GPIO

from GPIOWrapper import GPIOWrapper as gpio
from ShiftRegister import ShiftRegister as ShiftRegister
from ShiftGPIOWrapper import ShiftGPIOWrapper as ShiftGPIOWrapper
import time
import sys

def main():
    # cleanup state and set pin naming mode
    try:
        # for GpioObject
        GPIO.cleanup_existing()
        GPIO.setmode(GPIO.BOARD)
    except AttributeError:
        # for RPi.GPIO
        GPIO.cleanup()
        GPIO.setmode(GPIO.BCM)
    print type(GPIO)
    print GPIO.OUT
    # define necessary pins for shift register
    ser = gpio(7, GPIO) # labeled S
    ser.setup(GPIO.OUT) 
    rclk = gpio(8, GPIO) # labeled R
    rclk.setup(GPIO.OUT)
    srclk = gpio(25, GPIO) # labeled SR
    srclk.setup(GPIO.OUT)
    # and shift register, 16 bits wide
    shift_register = ShiftRegister(ser, rclk, srclk, 16, autocommit=False)
    # use some virtual bits in shift register
    # act like GPIO Pins with this Wrapper Class
    # driver 1 dir and step
    d_1_dir_pin = ShiftGPIOWrapper(shift_register, 0)
    d_1_step_pin = ShiftGPIOWrapper(shift_register, 1)
    # driver 2 dir and step
    d_2_dir_pin = ShiftGPIOWrapper(shift_register, 2)
    d_2_step_pin = ShiftGPIOWrapper(shift_register, 3)
    # driver 3 dir and step
    d_3_dir_pin = ShiftGPIOWrapper(shift_register, 4)
    d_3_step_pin = ShiftGPIOWrapper(shift_register, 5)
    
    steps = 0

    try:
        d_1_dir_pin.output(DIRECTION)
        d_2_dir_pin.output(DIRECTION)
        d_3_dir_pin.output(DIRECTION)
        shift_register.commit()
        start = time.time()
        while (start + DURATION_S) >= time.time():
            d_1_step_pin.output(True)
            d_2_step_pin.output(True)
            d_3_step_pin.output(True)
            shift_register.commit()
            # time.sleep(0.0001)
            d_1_step_pin.output(False)
            d_2_step_pin.output(False)
            d_3_step_pin.output(False)
            shift_register.commit()
            # time.sleep(STEP_INTERVAL)
            steps += 1
    except KeyboardInterrupt:
        pass
    print "%d steps done" % steps
    shift_register.clear()
    GPIO.cleanup()

if __name__ == "__main__":
    import cProfile
    import pstats
    if len(sys.argv) != 4:
        print "use %s DIRECTION STEP_INTERVAL DURATION_S"
        sys.exit(1)
    DIRECTION = bool(sys.argv[1])
    STEP_INTERVAL = float(sys.argv[2])
    DURATION_S = int(sys.argv[3])
    profile = "test_a4988_shift.profile"
    cProfile.runctx("main()", globals(), locals(), filename=profile)
    s = pstats.Stats(profile)
    s.sort_stats("time")
    s.print_stats()
