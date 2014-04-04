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
# from RPi import GPIO
# use own GPIO implementation
from GpioObject import GpioObject
GPIO = GpioObject(GpioObject.BOARD)
from FakeGPIO import GPIOWrapper as gpio
from ShiftRegister import ShiftRegister as ShiftRegister
from ShiftRegister import ShiftGPIOWrapper as ShiftGPIOWrapper
import time
import sys

def main():
    # cleanup state and set pin naming mode
    GPIO.cleanup_existing()
    GPIO.setmode(GPIO.BOARD)

    # define necessary pins for shift register
    ser = gpio(7, GPIO) # labeled S
    ser.setup(GPIO.OUT) 
    rclk = gpio(8, GPIO) # labeled R
    rclk.setup(GPIO.OUT)
    srclk = gpio(25, GPIO) # labeled SR
    srclk.setup(GPIO.OUT)
    # and shift register, 16 bits wide
    shift_register = ShiftRegister(ser, rclk, srclk, 16, autocommit=True)
    # driver 1 dir and step
    d_1_dir_pin = ShiftGPIOWrapper(shift_register, 0)
    d_1_step_pin = ShiftGPIOWrapper(shift_register, 1)
    # driver 2 dir and step
    d_2_dir_pin = ShiftGPIOWrapper(shift_register, 2)
    d_2_step_pin = ShiftGPIOWrapper(shift_register, 3)
    # driver 3 dir and step
    d_3_dir_pin = ShiftGPIOWrapper(shift_register, 4)
    d_4_step_pin = ShiftGPIOWrapper(shift_register, 5)

    try:
        d_1_dir_pin.output(DIRECTION)
        start = time.time()
        while (start + DURATION_S) >= time.time():
            d_1_step_pin.output(1)
            # time.sleep(0.0001)
            d_1_step_pin.output(0)
            time.sleep(STEP_INTERVAL)
    except KeyboardInterrupt:
        pass
    shift_register.clear()
    GPIO.cleanup()

if __name__ == "__main__":
    import cProfile
    import pstats
    DIRECTION = int(sys.argv[1])
    STEP_INTERVAL = float(sys.argv[2])
    DURATION_S = int(sys.argv[3])
    profile = "test_a4988_shift.profile"
    cProfile.runctx("main()", globals(), locals(), filename=profile)
    s = pstats.Stats(profile)
    s.sort_stats("time")
    s.print_stats()
