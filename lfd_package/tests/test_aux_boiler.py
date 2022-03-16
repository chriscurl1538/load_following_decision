"""
Module Description:
    Contains  test functions for functions located in the aux_boiler.py file

NOT READY FOR TESTING
"""

import pytest
from lfd_package import aux_boiler as boiler


def test_calc_aux_boiler_output(class_info):
    chp = class_info[0]
    ab = class_info[1]
    demand = class_info[2]
    tes = class_info[3]

    func = boiler.calc_aux_boiler_output(chp=chp, demand=demand, tes=tes, ab=ab)

    assert isinstance(func, list)
    assert len(func) == 8760
    for index, i in enumerate(func):
        assert ab.min <= i.magnitude <= ab.cap.magnitude or i.magnitude == 0
        assert i.magnitude <= demand.hl[index]


def test_calc_annual_fuel_use(class_info):
    chp = class_info[0]
    ab = class_info[1]
    demand = class_info[2]
    tes = class_info[3]

    func = boiler.calc_annual_fuel_use(chp=chp, demand=demand, tes=tes, ab=ab)

    assert 0 < func


def test_calc_annual_fuel_cost(class_info):
    chp = class_info[0]
    ab = class_info[1]
    demand = class_info[2]
    tes = class_info[3]

    func = boiler.calc_annual_fuel_cost(chp=chp, demand=demand, tes=tes, ab=ab)

    assert 0 < func
