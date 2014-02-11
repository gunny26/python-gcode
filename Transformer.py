#/usr/bin/python
# -*- coding: utf-8 -*-
#
# parse Gcode
#
"""
Transforms Steps
"""

import logging
logging.basicConfig(level=logging.INFO, format="%(message)s")


class Transformer(object):
    """class to transfor from motor steps to other steps"""


    def __init__(self):
        pass

    def transform(self, data):
        """
        data is a unit vector in carthesian system
        we transfor this motion into length for makelangelo
        """
        #logging.debug("transform called with %s", data)
        return(data)


class TranformerMakelangelo(Transformer):
    """class to transfor from motor steps to other steps"""


    def __init__(self):
        Transformer.__init__(self)

    def transform(self, data):
        """
        data is a unit vector in carthesian system
        we transfor this motion into length for makelangelo
        """
        #logging.debug("__step called with %s", args)
        data = args[0]
        if self.tranformer is not None:
            data = self.transformer(data)
        for axis in ("X", "Y", "Z"):
            step = data.__dict__[axis]
            assert -1.0 <= step <= 1.0
            if step == 0.0 : 
                continue
            direction = self.get_direction(step)
            self.motors[axis].move_float(direction, abs(step))
        self.stats.update(self)

      
