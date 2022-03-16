"""
Module Description:
    Contains  test functions for functions located in the thermal_storage.py file

NOT READY FOR TESTING
"""

import pytest
from lfd_package import thermal_storage as storage
from lfd_package import chp as cogen
from lfd_package.tests.__init__ import ureg


def test_calc_excess_heat(class_info):
    chp = class_info[0]
    demand = class_info[2]

    func = storage.calc_excess_heat(chp=chp, demand=demand)
    chp_gen = cogen.calc_hourly_heat_generated(chp=chp, demand=demand)

    assert isinstance(func, list)
    assert len(func) == 8760
    for index, i in enumerate(func):
        if 0 < i.magnitude:
            assert demand.hl[index].magnitude < chp_gen[index].magnitude


def test_calc_heat_deficit(class_info):
    chp = class_info[0]
    demand = class_info[2]

    func = storage.calc_excess_heat(chp=chp, demand=demand)
    chp_gen = cogen.calc_hourly_heat_generated(chp=chp, demand=demand)

    assert isinstance(func, list)
    assert len(func) == 8760
    for index, i in enumerate(func):
        if i.magnitude < 0:
            assert chp_gen[index].magnitude < demand.hl[index].magnitude


def test_tes_heat_stored(class_info):
    chp = class_info[0]
    demand = class_info[2]
    tes = class_info[3]

    func = storage.tes_heat_stored(chp=chp, demand=demand, tes=tes)

    assert isinstance(func, list)
    assert len(func) == 8760
    for index, i in enumerate(func):
        assert 0 <= i.magnitude <= tes.cap.magnitude
