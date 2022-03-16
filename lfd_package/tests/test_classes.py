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

    assert 0 < chp.hp

    assert 0 < chp.td

    assert chp.pl == chp_pl
    assert chp.pl.shape == (2, 8)

    assert 0 < chp.cost.magnitude
    # assert chp.cost.unit == 1/ureg.kW

    assert 0 < chp.min.magnitude < chp.cap.magnitude
    # assert chp.min.unit == ureg.kW


def test_aux_boiler_class(class_info):
    # Assign class values
    ab = class_info[1]
    assert isinstance(ab, classes.AuxBoiler)

    cap_type = type(ab.cap.magnitude)
    assert isinstance(cap_type, float)
    assert 0 < ab.cap
    # assert ab.cap.unit == ureg.Btu / ureg.hour

    eff_type = type(ab.eff.magnitude)
    assert isinstance(ab.eff, float)
    assert 0 < ab.eff < 1

    td_type = type(ab.td.magnitude)
    assert isinstance(td_type, float)
    assert 0 < ab.td

    min_type = type(ab.min.magnitude)
    assert isinstance(min_type, float)
    assert 0 < ab.min < ab.cap
    # assert ab.min.unit == ureg.Btu / ureg.hour


def test_energy_demand_class(class_info):
    # Assign class values
    demand = class_info[2]
    assert isinstance(demand, classes.EnergyDemand)

    assert isinstance(demand.demand_file_name, str)

    assert isinstance(demand.el_cost, float)
    assert 0 < demand.el_cost
    # assert demand.el_cost.unit == 1/ureg.kWh

    assert isinstance(demand.fuel_cost, float)
    assert 0 < demand.fuel_cost
    # assert demand.fuel_cost.unit == 1/ureg.megaBtu

    assert isinstance(demand.hl, np.ndarray)
    assert isinstance(demand.hl[0], float)
    assert demand.hl.shape[0] == 8760
    assert demand.hl.size == 8760
    # assert demand.hl.unit == ureg.Btu

    assert isinstance(demand.el, np.ndarray)
    assert isinstance(demand.el[0], float)
    assert demand.el.shape[0] == 8760
    assert demand.el.size == 8760
    # assert demand.el.unit == ureg.kWh

    assert isinstance(demand.annual_el, float)
    assert 0 < demand.annual_el
    # assert demand.annual_el.unit == ureg.kWh

    assert isinstance(demand.annual_hl, float)
    assert 0 < demand.annual_hl
    # assert demand.annual_hl.unit == ureg.Btu


def test_tes_class(class_info):
    # Assign class values
    tes = class_info[3]
    assert isinstance(tes, classes.TES)

    assert isinstance(tes.cap, float)
    assert 0 < tes.cap
    # assert tes.cap.unit == ureg.Btu

    assert isinstance(tes.cost, float)
    assert 0 < tes.cost
    # assert tes.cost.unit == 1/ureg.kWh
