"""
Module Description:
    Contains  test functions for functions located in the "chp.py" file

NOT READY FOR TESTING
"""

import pytest
from load_following_decision_package import classes

from load_following_decision_package import chp as elf

import numpy as np


# # TODO: Update data stored in class to modify hourly demand data for testing
# def test_is_electric_utility_needed():
#     # Test default input
#     assert elf.calc_utility_electricity_needed() is None
#
#     # Test input array dtype
#     a = np.ones(shape=(8759, 1))
#     demand_dtype = np.append(a, ["demand"])
#     exp_dtype = ValueError
#     obs_dtype = is_electric_utility_needed(demand_hourly=demand_dtype)
#     assert exp_dtype == obs_dtype
#
#     # Test acceptable demand values
#     a = np.ones(shape=(8759, 1))
#     demand_range = np.append(a, [-40])
#     exp_range = AssertionError
#     obs_range = is_electric_utility_needed(demand_hourly=demand_range)
#     assert exp_range == obs_range
#
#     # Test function outputs
#     a = np.ones(shape=(8757, 1))
#     demand_output = np.append(a, [[50], [45], [55]], axis=0)
#     exp_output = [False, False, True]
#     obs_output = is_electric_utility_needed(demand_hourly=demand_output)
#     assert exp_output[-1] == obs_output[-1]
#     assert exp_output[-2] == obs_output[-2]
#     assert exp_output[-3] == obs_output[-3]
#

# def test_calculate_ELF_annual_electricity_cost():
#     return None
#
#
# def test_calculate_part_load_efficiency():
#     return None
