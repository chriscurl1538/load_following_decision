"""
Module Description:
    Contains  test functions for functions located in the chp.py file
"""

from lfd_package.modules import chp as cogen


# TODO: test units
# TODO: test passing bad values in (namely None or trying to put negative numbers in the yaml file)


def test_calc_hourly_electricity_bought(class_info):
    chp = class_info[0]
    demand = class_info[2]
    func = cogen.calc_hourly_electricity_bought(chp=chp, demand=demand)

    assert isinstance(func, list)
    assert len(func) == 8760
    assert 0 < sum(func)
    for index, i in enumerate(func):
        assert 0 <= i <= demand.el[index]


def test_calc_annual_electric_cost(class_info):
    chp = class_info[0]
    demand = class_info[2]
    func = cogen.calc_annual_electric_cost(chp=chp, demand=demand)

    assert 0 < func


def test_calc_hourly_efficiency(class_info):
    chp = class_info[0]
    demand = class_info[2]
    func = cogen.calc_hourly_efficiency(chp=chp, demand=demand)

    assert isinstance(func, list)
    assert len(func) == 8760
    for i in func:
        assert 0 < i < 1


def test_calc_hourly_generated_electricity(class_info):
    chp = class_info[0]
    demand = class_info[2]
    func = cogen.calc_hourly_generated_electricity(chp=chp, demand=demand)

    assert isinstance(func, list)
    assert len(func) == 8760
    for index, i in enumerate(func):
        assert 0 <= i <= demand.el[index]


def test_calc_hourly_heat_generated(class_info):
    chp = class_info[0]
    demand = class_info[2]
    func = cogen.calc_hourly_heat_generated(chp=chp, demand=demand)

    assert isinstance(func, list)
    assert len(func) == 8760
    for index, i in enumerate(func):
        assert 0 <= i.magnitude


# def test_calculate_annual_fuel_use(class_info):
#     chp = class_info[0]
#     demand = class_info[2]
#     func = cogen.calculate_annual_fuel_use(chp=chp, demand=demand)


def test_calc_annual_fuel_cost(class_info):
    chp = class_info[0]
    demand = class_info[2]
    func = cogen.calc_annual_fuel_cost(chp=chp, demand=demand)

    demand_mmbtu = sum(demand.hl) * 1000000
    max_cost = demand_mmbtu * demand.fuel_cost
    assert 0 <= func <= max_cost
