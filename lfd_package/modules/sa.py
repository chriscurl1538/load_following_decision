"""
Module Description:
    This module performs a sensitivity analysis on the following Python variables:
    - Electricity costs
    - Fuel costs
    - Incentives
    - TES Size
"""


def make_param_list(base=None, dev=None, allow_neg=False, has_units=True):
    if has_units is True:
        lower = base.magnitude - dev
        upper = base.magnitude + dev
        unit = base.units
    else:
        lower = base - dev
        upper = base + dev
        unit = None
    if lower < 0 and allow_neg is False:
        diff = abs(lower)
        lower = lower + diff
        upper = upper + diff
    return [lower, upper], unit
