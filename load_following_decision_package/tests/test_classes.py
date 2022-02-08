"""
Module description:
    This program tests the classes.py file
"""

from load_following_decision_package.classes import CHP
from load_following_decision_package.classes import AuxBoiler
from load_following_decision_package.classes import EnergyDemand
from load_following_decision_package.classes import TES

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
energy_demand_test = EnergyDemand(file_name="test_input_load_profiles_hourly", net_metering=True)


def test_energy_demand_class():
    # TODO: Test that electrical and heating demands have been imported correctly

    exp_nm = True
    obs_nm = energy_demand_test.nm
    assert exp_nm == obs_nm


# Testing TES Class
tes_test = TES(capacity=50, state_of_charge=0.5, charge=True, discharge=True)


def test_TES_class():
    exp_cap = 50
    obs_cap = tes_test.cap
    assert exp_cap == obs_cap

    exp_soc = 0.5
    obs_soc = tes_test.soc
    assert exp_soc == obs_soc

    exp_charge = True
    obs_charge = tes_test.charge
    assert exp_charge == obs_charge

    exp_discharge = True
    obs_discharge = tes_test.discharge
    assert exp_discharge == obs_discharge


if __name__ == '__main__':
    test_chp_class()
    test_aux_boiler_class()
    test_energy_demand_class()
    test_TES_class()
