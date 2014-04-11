from distutils.core import setup
from distutils.extension import Extension
from Cython.Build import cythonize
import sys

# set profiling globally
from Cython.Compiler.Options import directive_defaults
directive_defaults['profile'] = False

# extra compile flags
extra_compile_args = ["-O3"]

sys.argv.append("build_ext")
sys.argv.append("--inplace")

extensions = [
    Extension("Controller", ["src/Controller.pyx"], extra_compile_args=extra_compile_args),
    Extension("BaseMotor", ["src/Motor/BaseMotor.pyx"], extra_compile_args=extra_compile_args),
    Extension("UnipolarStepperMotor", ["src/Motor/UnipolarStepperMotor.pyx"], extra_compile_args=extra_compile_args),
    Extension("BipolarStepperMotor", ["src/Motor/BipolarStepperMotor.pyx"], extra_compile_args=extra_compile_args),
    Extension("LaserMotor", ["src/Motor/LaserMotor.pyx"], extra_compile_args=extra_compile_args),
    Extension("A5988DriverMotor", ["src/Motor/A5988DriverMotor.pyx"], extra_compile_args=extra_compile_args),
    Extension("Parser", ["src/Parser.pyx"], extra_compile_args=extra_compile_args),
    Extension("Point3d", ["src/Point3d.pyx"], extra_compile_args=extra_compile_args),
    Extension("LaserSpindle", ["src/Spindle/LaserSpindle.pyx"], extra_compile_args=extra_compile_args),
    Extension("BaseSpindle", ["src/Spindle/BaseSpindle.pyx"], extra_compile_args=extra_compile_args),
    Extension("ShiftRegister", ["src/ShiftRegister/ShiftRegister.pyx"], extra_compile_args=extra_compile_args),
    Extension("ShiftGPIOWrapper", ["src/ShiftRegister/ShiftGPIOWrapper.pyx"], extra_compile_args=extra_compile_args),
    Extension("GPIOObject", ["src/GPIOObject/GPIOObject.pyx"], extra_compile_args=extra_compile_args),
    Extension("FakeGPIO", ["src/GPIOObject/FakeGPIO.pyx"], extra_compile_args=extra_compile_args),
    Extension("GPIOWrapper", ["src/GPIOObject/GPIOWrapper.pyx"], extra_compile_args=extra_compile_args),
    Extension("Transformer", ["src/Transformer/Transformer.pyx"], extra_compile_args=extra_compile_args),
    Extension("GcodeGuiConsole", ["src/GcodeGuiConsole.pyx"], extra_compile_args=extra_compile_args),
]

setup(
    name = "python-gcode",
    ext_modules = cythonize(extensions), # accepts a glob pattern
)
