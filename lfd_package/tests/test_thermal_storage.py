"""
Module Description:
    Contains  test functions for functions located in the thermal_storage.py file
"""

import pint
from lfd_package.modules.__init__ import ureg
from lfd_package.modules import thermal_storage as storage


def test_calc_excess_and_deficit_chp_heat_gen(class_info):
    demand = class_info[0]
    chp = class_info[1]
    ab = class_info[3]
    func_elf = storage.calc_excess_and_deficit_chp_heat_gen(chp=chp, demand=demand, ab=ab,
                                                            load_following_type='ELF')
    func_tlf = storage.calc_excess_and_deficit_chp_heat_gen(chp=chp, demand=demand, ab=ab,
                                                            load_following_type='TLF')

    # Check data types
    assert isinstance(func_tlf, list)
    assert isinstance(func_elf, list)

    # Check array sizes
    assert len(func_elf) == len(demand.el)
    assert len(func_tlf) == len(demand.hl)

    # Check value ranges, pint units
    for index, element in enumerate(func_tlf):
        assert element.units == (ureg.Btu / ureg.hour)
    for index, element in enumerate(func_elf):
        assert element.units == (ureg.Btu / ureg.hour)


def test_calc_tes_heat_flow_and_soc(class_info):
    demand = class_info[0]
    chp = class_info[1]
    tes = class_info[2]
    ab = class_info[3]
    heat_rates_elf, soc_list_elf = storage.calc_tes_heat_flow_and_soc(chp=chp, demand=demand, tes=tes, ab=ab,
                                                                      load_following_type='ELF')
    heat_rates_tlf, soc_list_tlf = storage.calc_tes_heat_flow_and_soc(chp=chp, demand=demand, tes=tes, ab=ab,
                                                                      load_following_type='TLF')

    # Check data types
    assert isinstance(soc_list_elf, list)
    assert isinstance(heat_rates_elf, list)
    assert isinstance(heat_rates_tlf, list)
    assert isinstance(soc_list_tlf, list)

    # Check array sizes
    assert len(soc_list_elf) == len(demand.el)
    assert len(heat_rates_elf) == len(demand.el)
    assert len(heat_rates_tlf) == len(demand.hl)
    assert len(soc_list_tlf) == len(demand.hl)

    # Check value ranges and pint units
    for index, element in enumerate(soc_list_elf):
        assert isinstance(element, pint.Quantity)
        assert 0 <= element.magnitude <= 1
        assert element.units == ''
    for index, element in enumerate(heat_rates_elf):
        assert isinstance(element, pint.Quantity)
        assert element.units == (ureg.Btu / ureg.hour)
    for index, element in enumerate(heat_rates_tlf):
        assert isinstance(element, pint.Quantity)
        assert element.units == (ureg.Btu / ureg.hour)
    for index, element in enumerate(soc_list_tlf):
        assert isinstance(element, pint.Quantity)
        assert 0 <= element.magnitude <= 1
        assert element.units == ''
