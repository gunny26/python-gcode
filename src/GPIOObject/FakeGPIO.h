#ifndef __PYX_HAVE__GPIOObject__FakeGPIO
#define __PYX_HAVE__GPIOObject__FakeGPIO


#ifndef __PYX_HAVE_API__GPIOObject__FakeGPIO

#ifndef __PYX_EXTERN_C
  #ifdef __cplusplus
    #define __PYX_EXTERN_C extern "C"
  #else
    #define __PYX_EXTERN_C extern
  #endif
#endif

__PYX_EXTERN_C DL_IMPORT(int) BCM;
__PYX_EXTERN_C DL_IMPORT(int) BOARD;
__PYX_EXTERN_C DL_IMPORT(int) OUT;
__PYX_EXTERN_C DL_IMPORT(int) IN;
__PYX_EXTERN_C DL_IMPORT(int) HIGH;
__PYX_EXTERN_C DL_IMPORT(int) LOW;

#endif /* !__PYX_HAVE_API__GPIOObject__FakeGPIO */

#if PY_MAJOR_VERSION < 3
PyMODINIT_FUNC initFakeGPIO(void);
#else
PyMODINIT_FUNC PyInit_FakeGPIO(void);
#endif

#endif /* !__PYX_HAVE__GPIOObject__FakeGPIO */
