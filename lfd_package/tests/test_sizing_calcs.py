"""
Module description:
    This program tests the sizing_calcs.py file
"""
import numpy as np
from random import randint
import pint
from lfd_package.modules import sizing_calcs as sizing
from lfd_package.modules.__init__ import ureg, Q_


def test_create_demand_curve_array(class_info):
    demand = class_info[0]
    func_el = sizing.create_demand_curve_array(array=demand.el)
    func_hl = sizing.create_demand_curve_array(array=demand.hl)

    # Check data types
    assert isinstance(func_el[0], np.ndarray)
    assert isinstance(func_el[1], pint.Quantity)
    assert isinstance(func_hl[0], np.ndarray)
    assert isinstance(func_hl[1], pint.Quantity)

    # Check array sizes
    assert len(func_el[0]) == len(demand.el)
    assert len(func_el[1]) == len(demand.el)
    assert len(func_hl[0]) == len(demand.hl)
    assert len(func_hl[1]) == len(demand.hl)

    # Check value ranges and pint units
    for index, element in enumerate(func_el[0]):
        assert 0 <= element <= 100
    for index, element in enumerate(func_el[1]):
        assert 0 <= element.magnitude
        assert isinstance(element, pint.Quantity)
        assert element.units == ureg.kW
    for index, element in enumerate(func_hl[0]):
        assert 0 <= element <= 100
    for index, element in enumerate(func_hl[1]):
        assert 0 <= element
        assert isinstance(element, pint.Quantity)
        assert element.units == (ureg.Btu / ureg.hours)


def test_electrical_output_to_fuel_consumption(class_info):
    func_input = randint(0, 100) * ureg.kW
    func = sizing.electrical_output_to_fuel_consumption(electrical_output=func_input)

    # Check data types
    assert isinstance(func, pint.Quantity)

    # Check pint units
    assert func.units == ureg.kW

    # Check value range
    assert 0 <= func.magnitude


def test_electrical_output_to_thermal_output(class_info):
    func_input = randint(0, 100) * ureg.kW
    func = sizing.electrical_output_to_thermal_output(electrical_output=func_input)

    # Check data types
    assert isinstance(func, pint.Quantity)

    # Check pint units
    assert func.units == ureg.kW

    # Check value range
    assert 0 <= func.magnitude


def test_thermal_output_to_electrical_output(class_info):
    func_input = randint(0, 100) * ureg.kW
    func = sizing.thermal_output_to_electrical_output(thermal_output=func_input)

    # Check data types
    assert isinstance(func, pint.Quantity)

    # Check Pint units
    assert func.units == ureg.kW

    # Check value ranges
    assert 0 <= func.magnitude


def test_size_chp(class_info):
    demand = class_info[0]
    ab = class_info[3]
    func_elf = sizing.size_chp(load_following_type='ELF', demand=demand, ab=ab)
    func_tlf = sizing.size_chp(load_following_type='TLF', demand=demand, ab=ab)

    # Check data types
    assert isinstance(func_elf, pint.Quantity)
    assert isinstance(func_tlf, pint.Quantity)

    # Check Pint units
    assert func_elf.units == ureg.kW
    assert func_tlf.units == ureg.kW

    # Check value ranges TODO: Add maximum size value
    assert 0 <= func_elf.magnitude
    assert 0 <= func_tlf.magnitude


def test_calc_max_rect_chp_size(class_info):
    demand = class_info[0]
    func_el = sizing.calc_max_rect_chp_size(array=demand.el)
    func_hl = sizing.calc_max_rect_chp_size(array=demand.hl)

    # Check data types
    assert isinstance(func_el, pint.Quantity)
    assert isinstance(func_hl, pint.Quantity)

    # Check Pint units
    assert func_el.units == ureg.kW
    assert func_hl.units == (ureg.Btu / ureg.hour)

    # Check value ranges TODO: Add maximum size value
    assert 0 <= func_el.magnitude
    assert 0 <= func_hl.magnitude


def test_calc_min_pes_chp_size(class_info):
    demand = class_info[0]
    ab = class_info[3]
    func = sizing.calc_min_pes_chp_size(demand=demand, ab=ab)

    # Check data types
    assert isinstance(func, pint.Quantity)

    # Check Pint units
    assert func.units == ureg.kW

    # Check value ranges TODO: Add upper limit on CHP size
    assert 0 <= func.magnitude


def test_size_tes(class_info):
    demand = class_info[0]
    chp = class_info[1]
    ab = class_info[3]
    func_elf = sizing.size_tes(demand=demand, chp=chp, ab=ab, load_following_type='ELF')
    func_tlf = sizing.size_tes(demand=demand, chp=chp, ab=ab, load_following_type='TLF')

    # Check data types
    assert isinstance(func_elf, pint.Quantity)
    assert isinstance(func_tlf, pint.Quantity)

    # Check pint units
    assert func_elf.units == ureg.Btu
    assert func_tlf.units == ureg.Btu

    # Check value ranges TODO: Add upper limit on TES size
    assert 0 <= func_elf.magnitude
    assert 0 <= func_tlf.magnitude

