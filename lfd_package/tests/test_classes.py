"""
Module description:
    This program tests the classes.py file
"""
import numpy as np
import pint

from lfd_package.modules import classes
from lfd_package.modules.__init__ import ureg


def test_energy_demand_class(class_info):
    """
    TODO: Test updated 9/24/2022
    Checks that the data types, units, array sizes, and value ranges for this
    function are within expectations

    Parameters
    ----------
    class_info: Module
        Contains all classes from the classes.py module
    """
    # Assign class values
    demand = class_info[0]

    # Check that argument passed is correct
    assert demand is not None
    assert isinstance(demand, classes.EnergyDemand)

    # Check data types
    assert isinstance(demand.demand_file_name, str)
    assert isinstance(demand.net_metering_status, bool)
    assert isinstance(demand.grid_efficiency, float)
    assert isinstance(demand.el_cost, pint.Quantity)
    assert isinstance(demand.fuel_cost, pint.Quantity)
    assert isinstance(demand.hl, pint.Quantity)
    assert isinstance(demand.el, pint.Quantity)
    assert isinstance(demand.annual_el, pint.Quantity)
    assert isinstance(demand.annual_hl, pint.Quantity)

    # Check Pint units
    assert demand.el_cost.units == 1/ureg.kWh
    assert demand.fuel_cost.units == 1/ureg.megaBtu
    assert demand.hl.units == ureg.Btu / ureg.hour
    assert demand.el.units == ureg.kW
    assert demand.annual_el.units == ureg.kWh
    assert demand.annual_hl.units == ureg.Btu

    # Check array sizes
    assert demand.hl.shape[0] == 8760
    assert demand.hl.size == 8760
    assert demand.el.shape[0] == 8760
    assert demand.el.size == 8760

    # Check value ranges
    assert 0 <= demand.grid_efficiency <= 1
    assert 0 < demand.el_cost
    assert 0 < demand.fuel_cost.magnitude
    assert 0 < demand.annual_el.magnitude
    assert 0 < demand.annual_hl.magnitude


def test_chp_class(class_info):
    # Assign class values
    chp = class_info[1]

    # Check that argument passed is correct
    assert chp is not None
    assert isinstance(chp, classes.CHP)

    # Check data types
    assert isinstance(chp.fuel_type, str)
    assert isinstance(chp.fuel_input_rate, pint.Quantity)
    assert isinstance(chp.el_pl_eff, np.ndarray)
    assert isinstance(chp.th_pl_eff, np.ndarray)
    assert isinstance(chp.el_nominal_eff, float or int)
    assert isinstance(chp.th_nominal_eff, float or int)
    assert isinstance(chp.incremental_cost, pint.Quantity)
    assert isinstance(chp.min_pl, float or int)
    assert isinstance(chp.available_hours, pint.Quantity)

    # Check Pint units
    assert chp.fuel_input_rate.units == ureg.Btu / ureg.hour
    assert chp.available_hours.units == ureg.hour
    assert chp.incremental_cost.units == 1/ureg.kW

    # Check array sizes
    assert len(chp.el_pl_eff) == 3  # checks number of rows
    assert chp.el_pl_eff.size == 6  # ndarray.size checks number of items in array
    assert len(chp.th_pl_eff) == 3
    assert chp.th_pl_eff.size == 6

    # Check value ranges
    assert 0 < chp.cap.magnitude <= 100
    assert chp.fuel_type == "Natural Gas"
    assert 0 < chp.fuel_input_rate.magnitude
    assert 0 < chp.el_nominal_eff < 1
    assert 0 < chp.th_nominal_eff < 1
    assert 0 <= chp.system_cost
    assert 0 < chp.min_pl < 1
    assert 0 < chp.available_hours.magnitude <= 8760


def test_tes_class(class_info):
    # Assign class values
    tes = class_info[2]

    # Check that argument passed is correct
    assert tes is not None
    assert isinstance(tes, classes.TES)

    # Check data types
    assert isinstance(tes.cap, pint.Quantity)
    assert isinstance(tes.start, pint.Quantity)
    assert isinstance(tes.discharge, pint.Quantity)
    assert isinstance(tes.system_cost, pint.Quantity)

    # Check Pint units
    assert tes.cap.units == ureg.Btu
    assert tes.start.units == ureg.Btu
    assert tes.discharge.units == (ureg.Btu / ureg.hour)
    assert tes.system_cost.units == ''

    # Check value ranges
    assert 0 < tes.cap.magnitude
    assert 0 <= tes.start.magnitude <= tes.cap.magnitude
    assert 0 < tes.discharge.magnitude    # TODO: Check that this is not supposed to be negative for sign convention
    assert 0 <= tes.system_cost


def test_aux_boiler_class(class_info):
    # Assign class values
    ab = class_info[3]

    # Check that argument passed is correct
    assert ab is not None
    assert isinstance(ab, classes.AuxBoiler)

    # Check data types
    assert isinstance(ab.cap, pint.Quantity)
    assert isinstance(ab.eff, float)
    assert isinstance(ab.min_pl, float or int)

    # Check Pint units
    assert ab.cap.units == (ureg.Btu / ureg.hour)

    # Check value ranges
    assert 0 < ab.cap.magnitude
    assert 0 < ab.eff < 1
    assert 0 < ab.min_pl < ab.cap.magnitude
