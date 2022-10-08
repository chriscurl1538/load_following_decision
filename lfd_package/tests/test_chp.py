"""
Module Description:
    Contains  test functions for functions located in the chp.py file
TODO: Fix infinite running of pytest
"""

import pint
from lfd_package.modules.__init__ import ureg
from lfd_package.modules import chp as cogen


def test_calc_avg_efficiency(class_info):
    chp = class_info[1]
    demand = class_info[0]
    ab = class_info[3]
    func_elf = cogen.calc_avg_efficiency(chp=chp, demand=demand, ab=ab, load_following_type='ELF')
    func_tlf = cogen.calc_avg_efficiency(chp=chp, demand=demand, ab=ab, load_following_type='TLF')

    # Check data types
    assert isinstance(func_elf[0], pint.Quantity)
    assert isinstance(func_elf[1], pint.Quantity)
    assert isinstance(func_tlf[0], pint.Quantity)
    assert isinstance(func_tlf[1], pint.Quantity)

    # Check pint units
    assert func_elf[0].units == ''
    assert func_elf[1].units == ''
    assert func_tlf[0].units == ''
    assert func_tlf[1].units == ''

    # Check value ranges
    assert 0 < func_elf[0] <= 1
    assert 0 < func_elf[1] <= 1
    assert 0 < func_tlf[0] <= 1
    assert 0 < func_tlf[1] <= 1


def test_calc_annual_fuel_use_and_costs(class_info):
    chp = class_info[1]
    demand = class_info[0]
    ab = class_info[3]
    func_elf = cogen.calc_annual_fuel_use_and_costs(chp=chp, demand=demand, ab=ab, load_following_type='ELF')
    func_tlf = cogen.calc_annual_fuel_use_and_costs(chp=chp, demand=demand, ab=ab, load_following_type='TLF')

    # Check data types
    assert isinstance(func_elf[0], pint.Quantity)
    assert isinstance(func_elf[1], pint.Quantity)
    assert isinstance(func_tlf[0], pint.Quantity)
    assert isinstance(func_tlf[1], pint.Quantity)

    # Check Pint units
    assert func_elf[0].units == ureg.Btu
    assert func_elf[1].units == ''
    assert func_tlf[0].units == ureg.Btu
    assert func_tlf[1].units == ''

    # Check value ranges
    assert 0 <= func_elf[0].magnitude
    assert 0 <= func_tlf[0].magnitude
    assert 0 <= func_elf[1]
    assert 0 <= func_tlf[1]


def test_calc_annual_electric_cost(class_info):
    chp = class_info[1]
    demand = class_info[0]
    ab = class_info[3]
    func_elf = cogen.calc_annual_electric_cost(chp=chp, demand=demand, ab=ab, load_following_type='ELF')
    func_tlf = cogen.calc_annual_electric_cost(chp=chp, demand=demand, ab=ab, load_following_type='TLF')

    # Check data types
    assert isinstance(func_elf, pint.Quantity)
    assert isinstance(func_tlf, pint.Quantity)

    # Check pint units
    assert func_elf.units == ''
    assert func_tlf.units == ''

    # Check value ranges
    assert 0 <= func_elf.magnitude
    assert 0 <= func_tlf.magnitude


def test_elf_calc_electricity_bought_and_generated(class_info):
    chp = class_info[1]
    demand = class_info[0]
    ab = class_info[3]
    func = cogen.elf_calc_electricity_bought_and_generated(chp=chp, ab=ab, demand=demand)

    # Check array sizes
    assert len(func[0]) == len(demand.el)
    assert len(func[1]) == len(demand.el)

    # Check data types
    assert isinstance(func[0], list)
    assert isinstance(func[1], list)

    # Check value ranges, data types, and pint units
    for index, element in enumerate(func[0]):
        assert 0 <= element.magnitude
        assert element.units == ureg.kWh
    for index, element in enumerate(func[1]):
        assert 0 <= element.magnitude
        assert element.units == ureg.kWh


def test_elf_calc_hourly_heat_generated(class_info):
    chp = class_info[1]
    demand = class_info[0]
    ab = class_info[3]
    func = cogen.elf_calc_hourly_heat_generated(chp=chp, demand=demand, ab=ab)

    # Check data types
    assert isinstance(func, list)

    # Check array sizes
    assert len(func) == len(demand.hl)

    # Check value ranges and pint units
    for index, element in enumerate(func):
        assert element.units == (ureg.Btu / ureg.hour)
        assert 0 <= element.magnitude


def test_tlf_calc_hourly_heat_generated(class_info):
    chp = class_info[1]
    demand = class_info[0]
    ab = class_info[3]
    func = cogen.tlf_calc_hourly_heat_generated(chp=chp, demand=demand, ab=ab)

    # Check data types
    assert isinstance(func, list)

    # Check array sizes
    assert len(func) == len(demand.hl)

    # Check value ranges and pint units
    for index, element in enumerate(func):
        assert element.units == (ureg.Btu / ureg.hour)
        assert 0 <= element.magnitude


def test_tlf_calc_electricity_bought_and_generated(class_info):
    chp = class_info[1]
    demand = class_info[0]
    ab = class_info[3]
    func = cogen.tlf_calc_electricity_bought_and_generated(chp=chp, demand=demand, ab=ab)

    # Check data types
    assert isinstance(func[0], list)
    assert isinstance(func[1], list)

    # Check array sizes
    assert len(func[0]) == len(demand.el)
    assert len(func[1]) == len(demand.el)

    # Check value ranges and pint units
    for index, element in enumerate(func[0]):
        assert element.units == ureg.kWh
        assert 0 <= element.magnitude
    for index, element in enumerate(func[1]):
        assert element.units == ureg.kWh
        assert 0 <= element.magnitude
