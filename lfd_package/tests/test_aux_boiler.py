"""
Module Description:
    Contains  test functions for functions located in the aux_boiler.py file
"""

from lfd_package.modules import aux_boiler as boiler
from lfd_package.modules.__init__ import ureg


def test_calc_aux_boiler_output(class_info):
    chp = class_info[0]
    ab = class_info[1]
    demand = class_info[2]
    tes = class_info[3]

    data_res = 1 * ureg.hour
    ab_min_btu = data_res * ab.min
    ab_max_btu = data_res * ab.cap

    func = boiler.calc_aux_boiler_output(chp=chp, demand=demand, tes=tes, ab=ab)

    assert isinstance(func, list)
    assert len(func) == 8760
    for index, i in enumerate(func):
        assert ab_min_btu <= i <= ab_max_btu or i.magnitude == 0
        assert i <= demand.hl[index]


def test_calc_annual_fuel_use(class_info):
    chp = class_info[0]
    ab = class_info[1]
    demand = class_info[2]
    tes = class_info[3]

    func = boiler.calc_annual_fuel_use(chp=chp, demand=demand, tes=tes, ab=ab)

    assert 0 <= func.magnitude


def test_calc_annual_fuel_cost(class_info):
    chp = class_info[0]
    ab = class_info[1]
    demand = class_info[2]
    tes = class_info[3]

    func = boiler.calc_annual_fuel_cost(chp=chp, demand=demand, tes=tes, ab=ab)

    assert 0 <= func.magnitude
