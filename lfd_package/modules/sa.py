"""
Module Description:
    This module performs a sensitivity analysis on the following Python variables:
    - Electricity costs
    - Fuel costs
    - Incentives
    - TES Size
"""

from lfd_package.modules.__init__ import ureg, Q_
from sensitivity import SensitivityAnalyzer


def make_param_list(base=None, variation=None):    # TODO: Manage potential negative values
    start_val = round(base.magnitude) - variation
    stop_val = round(base.magnitude) + variation + 1
    increm = round((base.magnitude - start_val) / variation)
    param_list = []
    value_list = range(start_val, stop_val, increm)
    for value in value_list:
        param_list.append(Q_(value, base.units))
    return param_list
