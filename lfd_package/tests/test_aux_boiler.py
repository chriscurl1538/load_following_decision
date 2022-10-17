"""
Module Description:
    Contains  test functions for functions located in the aux_boiler.py file
"""
import pint

from lfd_package.modules import aux_boiler as boiler
from lfd_package.modules.__init__ import ureg, Q_


def test_calc_aux_boiler_output_rate(class_info):
    demand = class_info[0]
    chp = class_info[1]
    tes = class_info[2]
    ab = class_info[3]
    func_elf = boiler.calc_aux_boiler_output_rate(demand=demand, chp=chp, ab=ab, tes=tes, load_following_type='ELF')
    func_tlf = boiler.calc_aux_boiler_output_rate(demand=demand, chp=chp, ab=ab, tes=tes, load_following_type='TLF')

    # Check data types
    assert isinstance(func_elf, list)
    assert isinstance(func_tlf, list)

    # Check array lengths
    assert len(func_tlf) == len(demand.hl)
    assert len(func_elf) == len(demand.el)

    # Check pint units, value ranges
    for index, element in enumerate(func_elf):
        assert element.units == ureg.Btu / ureg.hour
        assert 0 <= element.magnitude <= ab.cap.magnitude
    for index, element in enumerate(func_tlf):
        assert element.units == ureg.Btu / ureg.hour
        assert 0 <= element.magnitude <= ab.cap.magnitude


def test_calc_annual_fuel_use_and_cost(class_info):
    demand = class_info[0]
    chp = class_info[1]
    tes = class_info[2]
    ab = class_info[3]

    func_fuel_elf = boiler.calc_annual_fuel_use_and_cost(chp=chp, demand=demand, tes=tes, ab=ab, load_following_type='ELF')[0]
    func_cost_elf = boiler.calc_annual_fuel_use_and_cost(chp=chp, demand=demand, tes=tes, ab=ab, load_following_type='ELF')[1]
    func_fuel_tlf = boiler.calc_annual_fuel_use_and_cost(chp=chp, demand=demand, tes=tes, ab=ab, load_following_type='TLF')[0]
    func_cost_tlf = boiler.calc_annual_fuel_use_and_cost(chp=chp, demand=demand, tes=tes, ab=ab, load_following_type='TLF')[1]

    # Check data types
    assert isinstance(func_fuel_elf, pint.Quantity)
    assert isinstance(func_cost_elf, pint.Quantity)
    assert isinstance(func_fuel_tlf, pint.Quantity)
    assert isinstance(func_cost_tlf, pint.Quantity)

    # Check pint units
    assert func_fuel_elf.units == ureg.Btu
    assert func_cost_elf.units == ''
    assert func_fuel_tlf.units == ureg.Btu
    assert func_cost_tlf.units == ''

    # Check value ranges
    assert 0 <= func_fuel_elf.magnitude <= (ab.cap.magnitude * len(demand.hl))
    assert 0 <= func_cost_elf.magnitude
    assert 0 <= func_fuel_tlf.magnitude <= (ab.cap.magnitude * len(demand.hl))
    assert 0 <= func_cost_tlf.magnitude
