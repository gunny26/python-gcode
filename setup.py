from distutils.core import setup
from distutils.extension import Extension
from Cython.Build import cythonize
import sys


sys.argv.append("build_ext")
sys.argv.append("--inplace")

extensions = [
    Extension("Controller", ["src/Controller.pyx"]),
    Extension("BaseMotor", ["src/Motor/BaseMotor.pyx"]),
    Extension("UnipolarStepperMotor", ["src/Motor/UnipolarStepperMotor.pyx"]),
    Extension("BipolarStepperMotor", ["src/Motor/BipolarStepperMotor.pyx"]),
    Extension("LaserMotor", ["src/Motor/LaserMotor.pyx"]),
    Extension("A5988DriverMotor", ["src/Motor/A5988DriverMotor.pyx"]),
    Extension("Parser", ["src/Parser.pyx"]),
    Extension("Point3d", ["src/Point3d.pyx"]),
    Extension("LaserSpindle", ["src/Spindle/LaserSpindle.pyx"]),
    Extension("BaseSpindle", ["src/Spindle/BaseSpindle.pyx"]),
    Extension("ShiftRegister", ["src/ShiftRegister/ShiftRegister.pyx"]),
    Extension("ShiftGPIOWrapper", ["src/ShiftRegister/ShiftGPIOWrapper.pyx"]),
    Extension("GPIOObject", ["src/GPIOObject/GPIOObject.pyx"]),
    Extension("FakeGPIO", ["src/GPIOObject/FakeGPIO.pyx"]),
    Extension("GPIOWrapper", ["src/GPIOObject/GPIOWrapper.pyx"]),
    Extension("Transformer", ["src/Transformer/Transformer.pyx"]),
]

setup(
    name = "python-gcode",
    ext_modules = cythonize(extensions), # accepts a glob pattern
)
