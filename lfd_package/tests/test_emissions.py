"""
Module description:
    This program tests the emissions.py file
"""
import pint
import pytest

from lfd_package.modules import emissions
from lfd_package.modules.__init__ import ureg


def test_identify_subgrid_coefficients(class_info):
    demand = class_info[0]
    city1 = 'seattle'
    city2 = 'Seattle'
    city3 = 'seatle'
    state1 = 'wa'
    state2 = 'WA'
    state3 = 'mt'
    func_pass1 = emissions.identify_subgrid_coefficients(demand=demand, state=state1, city=city1)
    func_pass2 = emissions.identify_subgrid_coefficients(demand=demand, state=state2, city=city2)

    # Check if exceptions are raised correctly
    with pytest.raises(Exception, match="City and State must be one of the 5 accepted locations"):
        emissions.identify_subgrid_coefficients(demand=demand, state=state2, city=city3)
        emissions.identify_subgrid_coefficients(demand=demand, state=state3, city=city1)

    # Check data types
    assert isinstance(func_pass1[0], pint.Quantity)
    assert isinstance(func_pass1[1], pint.Quantity)
    assert isinstance(func_pass2[0], pint.Quantity)
    assert isinstance(func_pass2[1], pint.Quantity)

    # Check array sizes
    assert len(func_pass1) == 2
    assert len(func_pass2) == 2

    # Check pint units
    assert func_pass1[0].units == ureg.lbs / ureg.MWh
    assert func_pass1[1].units == ureg.lbs / ureg.MWh
    assert func_pass2[0].units == ureg.lbs / ureg.MWh
    assert func_pass2[1].units == ureg.lbs / ureg.MWh

    # Check value ranges
    assert 0 < func_pass1[0]
    assert 0 < func_pass1[1]
    assert 0 < func_pass2[0]
    assert 0 < func_pass2[1]


def test_calc_grid_emissions(class_info):
    demand = class_info[0]
    city = 'pheonix'
    state = 'az'
    func = emissions.calc_grid_emissions(demand=demand, city=city, state=state)

    # Check data types
    assert isinstance(func[0], pint.Quantity)
    assert isinstance(func[1], pint.Quantity)

    # Check array sizes
    assert len(func) == 2

    # Check pint units
    assert func[0].units == ureg.lbs
    assert func[1].units == ureg.lbs

    # Check value ranges
    assert 0 < func[0]
    assert 0 < func[1]


def test_calc_fuel_emissions(class_info):
    demand = class_info[0]
    func = emissions.calc_fuel_emissions(demand=demand)

    # Check data types
    assert isinstance(func, pint.Quantity)

    # Check pint units
    assert func.units == ureg.lbs

    # Check value ranges
    assert 0 < func.magnitude


def test_calc_chp_emissions(class_info):
    demand = class_info[0]
    chp = class_info[1]
    tes = class_info[2]
    ab = class_info[3]

    city = 'miami'
    state = 'fl'
    load_following1 = 'ELF'
    load_following2 = 'TLF'
    func1 = emissions.calc_chp_emissions(demand=demand, chp=chp, tes=tes, ab=ab, city=city, state=state,
                                         load_following_type=load_following1)
    func2 = emissions.calc_chp_emissions(demand=demand, chp=chp, tes=tes, ab=ab, city=city, state=state,
                                         load_following_type=load_following2)

    # Check data types
    assert isinstance(func1[0], pint.Quantity)
    assert isinstance(func1[1], pint.Quantity)
    assert isinstance(func2[0], pint.Quantity)
    assert isinstance(func2[1], pint.Quantity)

    # Check array sizes
    assert len(func1) == 2
    assert len(func2) == 2

    # Check pint units
    assert func1[0].units == ureg.lbs
    assert func1[1].units == ureg.lbs
    assert func2[0].units == ureg.lbs
    assert func2[1].units == ureg.lbs

    # Check value ranges
    assert 0 < func1[0]
    assert 0 < func1[1]
    assert 0 < func2[0]
    assert 0 < func2[1]


def test_compare_emissions(class_info):
    demand = class_info[0]
    chp = class_info[1]
    tes = class_info[2]
    ab = class_info[3]

    city = 'miami'
    state = 'fl'
    load_following1 = 'ELF'
    load_following2 = 'TLF'
    func1 = emissions.compare_emissions(chp=chp, demand=demand, tes=tes, ab=ab, city=city, state=state,
                                        load_following_type=load_following1)
    func2 = emissions.compare_emissions(chp=chp, demand=demand, tes=tes, ab=ab, city=city, state=state,
                                        load_following_type=load_following2)

    # Check data types
    assert isinstance(func1, pint.Quantity)
    assert isinstance(func2, pint.Quantity)

    # Check pint units
    assert func1.units == ureg.lbs
    assert func2.units == ureg.lbs
