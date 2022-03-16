"""
Module Description:
    Contains  test functions for functions located in the thermal_storage.py file
"""

from lfd_package.modules import chp as cogen, thermal_storage as storage


def test_calc_excess_and_deficit_heat(class_info):
    chp = class_info[0]
    demand = class_info[2]

    func = storage.calc_excess_and_deficit_heat(chp=chp, demand=demand)
    chp_gen = cogen.calc_hourly_heat_generated(chp=chp, demand=demand)

    assert isinstance(func, list)
    assert len(func) == 8760
    for index, i in enumerate(func):
        if 0 < i:
            assert demand.hl[index].magnitude < chp_gen[index].magnitude
        elif i < 0:
            assert chp_gen[index].magnitude < demand.hl[index].magnitude


def test_tes_heat_stored(class_info):
    chp = class_info[0]
    demand = class_info[2]
    tes = class_info[3]

    charge, status = storage.tes_heat_stored(chp=chp, demand=demand, tes=tes)

    assert isinstance(charge, list)
    assert isinstance(status, list)
    assert len(charge) == 8760
    assert len(status) == 8760
    for index, i in enumerate(status):
        s = status[index]
        c = charge[index]
        assert 0 <= s.magnitude <= tes.cap.magnitude
        assert abs(c.magnitude) <= tes.cap.magnitude
