"""
Module description:
    This program tests the classes.py file
"""

from lfd_package.classes import CHP
from lfd_package.classes import AuxBoiler
from lfd_package.classes import EnergyDemand
# from lfd_package.classes import TES

import numpy as np

# TODO: Add tests for unacceptable inputs (negative numbers, capacity above 50, etc)


# Testing CHP Class
EMPTY_ARRAY = np.empty([10, 2])
chp_test = CHP(capacity=50, heat_power=4, turn_down_ratio=3.3, part_load=EMPTY_ARRAY)


def test_chp_class():
    exp_cap = 50
    obs_cap = chp_test.cap
    assert exp_cap == obs_cap

    exp_hp = 4
    obs_hp = chp_test.hp
    assert exp_hp == obs_hp

    exp_td = 3.3
    obs_td = chp_test.td
    assert exp_td == obs_td

    exp_pl = EMPTY_ARRAY
    obs_pl = chp_test.pl
    np.testing.assert_allclose(actual=obs_pl, desired=exp_pl, rtol=0.01)


# Testing AuxBoiler Class
AB_test = AuxBoiler(capacity=50, efficiency=0.8, turn_down_ratio=3.3)


def test_aux_boiler_class():
    exp_cap = 50
    obs_cap = AB_test.cap
    assert exp_cap == obs_cap

    exp_eff = 0.8
    obs_eff = AB_test.eff
    assert exp_eff == obs_eff

    exp_td = 3.3
    obs_td = AB_test.td
    assert exp_td == obs_td


# Testing EnergyDemand Class

def test_energy_demand_class():
    # TODO: Test that electrical and heating demands have been imported correctly
    energy_demand = EnergyDemand()

    # Verifies electrical load array size
    rows_el = energy_demand.el.shape[0]
    try:
        cols_el = energy_demand.el.shape[1]
    except IndexError:
        cols_el = 1
    assert rows_el == 8760
    assert cols_el == 1

    # Verifies heating load array size
    rows_hl = energy_demand.hl.shape[0]
    try:
        cols_hl = energy_demand.hl.shape[1]
    except IndexError:
        cols_hl = 1
    assert rows_hl == 8760
    assert cols_hl == 1

    # Verifies default values
    assert energy_demand.demand_file_name == "default_file.csv"
    assert energy_demand.el_cost == 0
    assert energy_demand.fuel_cost == 0

    # Verifies that values pass to class correctly
    pass_values = EnergyDemand(file_name="name.csv", electric_cost=0.24, fuel_cost=0.5)
    assert pass_values.el_cost == 0.24
    assert pass_values.fuel_cost == 0.5
    assert pass_values.demand_file_name == "name.csv"


# # Testing TES Class
# tes_test = TES(capacity=50, state_of_charge=0.5, charge=True, discharge=True)


# def test_TES_class():
#     exp_cap = 50
#     obs_cap = tes_test.cap
#     assert exp_cap == obs_cap
#
#     exp_soc = 0.5
#     obs_soc = tes_test.soc
#     assert exp_soc == obs_soc
#
#     exp_charge = True
#     obs_charge = tes_test.charge
#     assert exp_charge == obs_charge
#
#     exp_discharge = True
#     obs_discharge = tes_test.discharge
#     assert exp_discharge == obs_discharge
