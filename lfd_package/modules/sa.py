"""
Module Description:
    This module performs a sensitivity analysis on the following Python variables:
    - Electricity costs
    - Fuel costs
    - Incentives
    - TES Size
"""


def make_param_list(base=None, dev=None, allow_neg=False):
    lower = round(base.magnitude) - dev
    upper = round(base.magnitude) + dev
    unit = base.units
    if lower < 0 and allow_neg is False:
        diff = abs(lower)
        lower = lower + diff
        upper = upper + diff
    return [lower, upper], unit
