"""
Module description:
    This program tests the classes.py file
"""

import numpy as np
from lfd_package.modules import classes


def test_chp_class(class_info, chp_pl):
    # Assign class values
    chp = class_info[0]
    assert chp is not None
    assert isinstance(chp, classes.CHP)

    assert 0 < chp.cap.magnitude <= 50
    # assert chp.cap.unit == ureg.kW

    assert isinstance(chp.hp, float or int)
    assert 0 < chp.hp

    assert isinstance(chp.td, float or int)
    assert 0 < chp.td

    np.testing.assert_allclose(actual=chp.pl, desired=chp_pl, rtol=0.01)
    assert chp.pl.shape == (8, 2)

    assert 0 < chp.cost.magnitude

    assert 0 < chp.min.magnitude < chp.cap.magnitude


def test_aux_boiler_class(class_info):
    # Assign class values
    ab = class_info[1]
    assert ab is not None
    assert isinstance(ab, classes.AuxBoiler)

    assert 0 < ab.cap

    assert isinstance(ab.eff, float)
    assert 0 < ab.eff < 1

    assert isinstance(ab.td, float or int)
    assert 0 < ab.td

    assert 0 < ab.min < ab.cap


def test_energy_demand_class(class_info):
    # Assign class values
    demand = class_info[2]
    assert demand is not None
    assert isinstance(demand, classes.EnergyDemand)

    assert isinstance(demand.demand_file_name, str)
    assert demand.demand_file_name == "default_file.csv"

    assert 0 < demand.el_cost

    assert 0 < demand.fuel_cost

    assert demand.hl.shape[0] == 8760
    assert demand.hl.size == 8760

    assert demand.el.shape[0] == 8760
    assert demand.el.size == 8760

    assert 0 < demand.annual_el

    assert 0 < demand.annual_hl


def test_tes_class(class_info):
    # Assign class values
    tes = class_info[3]
    assert tes is not None
    assert isinstance(tes, classes.TES)

    assert 0 < tes.cap

    assert 0 < tes.cost
