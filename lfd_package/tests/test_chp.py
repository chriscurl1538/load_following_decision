"""
Module Description:
    Contains  test functions for functions located in the chp.py file
"""

from lfd_package.modules import chp as cogen


def test_calc_electricity_bought_and_generated(class_info):
    chp = class_info[0]
    demand = class_info[2]
    func = cogen.calc_electricity_bought_and_generated(chp=chp, demand=demand)

    assert isinstance(func[0], list)
    assert len(func[0]) == 8760
    assert 0 < sum(func[0])
    for index, i in enumerate(func[0]):
        assert 0 <= i <= demand.el[index]

    assert isinstance(func[1], list)
    assert len(func[1]) == 8760
    for index, i in enumerate(func[1]):
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


def test_calc_hourly_heat_generated(class_info):
    chp = class_info[0]
    demand = class_info[2]
    func = cogen.calc_hourly_heat_generated(chp=chp, demand=demand)

    assert isinstance(func, list)
    assert len(func) == 8760
    for index, i in enumerate(func):
        assert 0 <= i.magnitude


def test_calculate_annual_fuel_use(class_info):
    chp = class_info[0]
    demand = class_info[2]
    func = cogen.calculate_annual_fuel_use(chp=chp, demand=demand)

    assert 0 <= func


def test_calc_annual_fuel_cost(class_info):
    chp = class_info[0]
    demand = class_info[2]
    func = cogen.calc_annual_fuel_cost(chp=chp, demand=demand)

    demand_mmbtu = sum(demand.hl) * 1000000
    max_cost = demand_mmbtu * demand.fuel_cost

    assert 0 <= func <= max_cost
