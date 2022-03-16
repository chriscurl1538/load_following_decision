"""
Module description:
    This program tests the classes.py file
"""
import numpy as np
from lfd_package.tests.__init__ import ureg


from lfd_package import classes


def test_chp_class(class_info, chp_pl):
    # Assign class values
    chp = class_info[0]
    assert isinstance(chp, classes.CHP)

    assert 0 < chp.cap.magnitude <= 50
    # assert chp.cap.unit == ureg.kW

    assert isinstance(chp.hp, float)
    assert 0 < chp.hp

    assert isinstance(chp.td, float)
    assert 0 < chp.td

    np.testing.assert_allclose(actual=chp.pl, desired=chp_pl, rtol=0.01)
    assert chp.pl.shape == (8, 2)

    assert 0 < chp.cost.magnitude
    # assert chp.cost.unit == 1/ureg.kW

    assert 0 < chp.min.magnitude < chp.cap.magnitude
    # assert chp.min.unit == ureg.kW


def test_aux_boiler_class(class_info):
    # Assign class values
    ab = class_info[1]
    assert isinstance(ab, classes.AuxBoiler)

    assert 0 < ab.cap
    # assert ab.cap.unit == ureg.Btu / ureg.hour

    assert isinstance(ab.eff, float)
    assert 0 < ab.eff < 1

    assert isinstance(ab.td, float)
    assert 0 < ab.td

    assert 0 < ab.min < ab.cap
    # assert ab.min.unit == ureg.Btu / ureg.hour


def test_energy_demand_class(class_info):
    # Assign class values
    demand = class_info[2]
    assert isinstance(demand, classes.EnergyDemand)

    assert isinstance(demand.demand_file_name, str)

    assert 0 < demand.el_cost
    # assert demand.el_cost.unit == 1/ureg.kWh

    assert 0 < demand.fuel_cost
    # assert demand.fuel_cost.unit == 1/ureg.megaBtu

    assert demand.hl.shape[0] == 8760
    assert demand.hl.size == 8760
    # assert demand.hl.unit == ureg.Btu

    assert demand.el.shape[0] == 8760
    assert demand.el.size == 8760
    # assert demand.el.unit == ureg.kWh

    assert 0 < demand.annual_el
    # assert demand.annual_el.unit == ureg.kWh

    assert 0 < demand.annual_hl
    # assert demand.annual_hl.unit == ureg.Btu


def test_tes_class(class_info):
    # Assign class values
    tes = class_info[3]
    assert isinstance(tes, classes.TES)

    assert 0 < tes.cap
    # assert tes.cap.unit == ureg.Btu

    assert 0 < tes.cost
    # assert tes.cost.unit == 1/ureg.kWh
