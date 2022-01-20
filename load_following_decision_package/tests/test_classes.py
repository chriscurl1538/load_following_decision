# This program tests the classes.py file

from load_following_decision_package.classes import CHP
from load_following_decision_package.classes import AuxBoiler
from load_following_decision_package.classes import Building
from load_following_decision_package.classes import EnergyWasted


# Testing CHP Class
chp_test = CHP(capacity=1, heat_power=2, turn_down_ratio=3)


def test_chp_class():
    exp_cap = 1
    obs_cap = chp_test.cap
    assert exp_cap == obs_cap

    exp_hp = 2
    obs_hp = chp_test.hp
    assert exp_hp == obs_hp

    exp_td = 3
    obs_td = chp_test.td
    assert exp_td == obs_td

    exp_pl = 40
    obs_pl = chp_test.part_load[1][0]
    assert exp_pl == obs_pl


# Testing AuxBoiler Class
AB_test = AuxBoiler(capacity=1, max_efficiency=2, turn_down_ratio=3)


def test_aux_boiler_class():
    exp_cap = 1
    obs_cap = AB_test.cap
    assert exp_cap == obs_cap

    exp_eff = 2
    obs_eff = AB_test.eff
    assert exp_eff == obs_eff

    exp_td = 3
    obs_td = AB_test.td
    assert exp_td == obs_td


# Testing Building Class
build_test = Building(heat_load=1, electrical_load=2, net_metering=True)


def test_building_class():
    exp_hl = 1
    obs_hl = build_test.hl
    assert exp_hl == obs_hl

    exp_el = 2
    obs_el = build_test.el
    assert exp_el == obs_el

    exp_nm = True
    obs_nm = build_test.nm
    assert exp_nm == obs_nm


# Testing EnergyWasted Class
ew_test = EnergyWasted(heat_wasted=1, electricity_wasted=2)


def test_energy_wasted_class():
    exp_hw = 1
    obs_hw = ew_test.hw
    assert exp_hw == obs_hw

    exp_ew = 2
    obs_ew = ew_test.ew
    assert exp_ew == obs_ew


if __name__ == '__main__':
    test_chp_class()
    test_aux_boiler_class()
    test_building_class()
    test_energy_wasted_class()
