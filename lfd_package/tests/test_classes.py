"""
Module description:
    This program tests the classes.py file
"""
import datetime

import numpy as np
import pint
import random as rand

from lfd_package.modules import classes
from lfd_package.modules.__init__ import ureg, Q_


def test_energy_demand_class(class_info):
    """
    Checks that the data types, units, array sizes, and value ranges for this
    class are within expectations

    Parameters
    ----------
    class_info: dict
        Contains all initialized classes from the conftest.py file
    """
    # Assign class values
    demand = class_info['demand']

    # Check that argument passed is correct
    assert demand is not None
    assert isinstance(demand, classes.EnergyDemand)

    # Check data types
    assert isinstance(demand.demand_file_name, str)
    assert isinstance(demand.meter_months_hourly, np.ndarray)     # array of datetime months
    # assert isinstance(demand.meter_months_hourly[0], int or datetime.datetime)      # TODO: What dtype is this?
    assert isinstance(demand.grid_efficiency, float)
    assert isinstance(demand.sim_ab_efficiency, float)
    assert isinstance(demand.city, str)
    assert isinstance(demand.state, str)
    assert isinstance(demand.summer_start_month, int)
    assert isinstance(demand.winter_start_month, int)
    assert isinstance(demand.hl, pint.Quantity)     # array of quantities
    assert isinstance(demand.hl[0], pint.Quantity)
    assert isinstance(demand.el, pint.Quantity)     # array of quantities
    assert isinstance(demand.el[0], pint.Quantity)
    assert isinstance(demand.summer_weight_el, pint.Quantity)
    assert isinstance(demand.summer_weight_hl, pint.Quantity)
    assert isinstance(demand.winter_weight_el, pint.Quantity)
    assert isinstance(demand.winter_weight_hl, pint.Quantity)
    assert isinstance(demand.annual_sum_el, pint.Quantity)
    assert isinstance(demand.annual_sum_hl, pint.Quantity)
    assert isinstance(demand.annual_peak_el, pint.Quantity)
    assert isinstance(demand.annual_peak_hl, pint.Quantity)
    assert isinstance(demand.monthly_peaks_list_el, list)  # List of quantities
    assert isinstance(demand.monthly_peaks_list_el[0], pint.Quantity)
    assert isinstance(demand.monthly_peaks_list_hl, list)  # List of quantities
    assert isinstance(demand.monthly_peaks_list_hl[0], pint.Quantity)
    assert isinstance(demand.monthly_sums_list_el, list)  # List of quantities
    assert isinstance(demand.monthly_sums_list_el[0], pint.Quantity)    # TODO: Left off here
    assert isinstance(demand.monthly_sums_list_hl, list)  # List of quantities
    assert isinstance(demand.monthly_sums_list_hl[0], pint.Quantity)

    # Check class methods
    # TODO: standardize_date_str
    # TODO: convert_units
    # TODO: convert_to_float_numpy
    # TODO: sum_annual_demand
    # TODO: seasonal_weights_hourly_data
    # TODO: seasonal_weights_monthly_data
    # TODO: monthly_demand_peaks
    # TODO: monthly_energy_sums

    # Check Pint units
    assert demand.hl[-1].units == ureg.Btu / ureg.hour
    assert demand.el[-1].units == ureg.kW
    assert demand.summer_weight_el.units == ''
    assert demand.summer_weight_hl.units == ''
    assert demand.winter_weight_el.units == ''
    assert demand.winter_weight_hl.units == ''
    assert demand.monthly_peaks_list_el[-1].units == ureg.kW
    assert demand.monthly_peaks_list_hl[-1].units == ureg.Btu / ureg.hour
    assert demand.monthly_sums_list_el[-1].units == ureg.kWh
    assert demand.monthly_sums_list_hl[-1].units == ureg.Btu
    assert demand.annual_sum_el.units == ureg.kWh
    assert demand.annual_sum_hl.units == ureg.Btu
    assert demand.annual_peak_el.units == ureg.kW
    assert demand.annual_peak_hl.units == ureg.Btu / ureg.hour

    # Check array sizes
    assert demand.meter_months_hourly.shape[0] == 8760
    assert demand.meter_months_hourly.size == 8760
    assert demand.hl.shape[0] == 8760
    assert demand.hl.size == 8760
    assert demand.el.shape[0] == 8760
    assert demand.el.size == 8760
    assert len(demand.monthly_peaks_list_el) == 12
    assert len(demand.monthly_peaks_list_hl) == 12
    assert len(demand.monthly_sums_list_el) == 12
    assert len(demand.monthly_sums_list_hl) == 12

    # Check value ranges
    assert 0 < min(demand.meter_months_hourly)
    assert max(demand.meter_months_hourly) < 12
    assert Q_(0, ureg.kW) <= min(demand.el)
    assert max(demand.el) == demand.annual_peak_el <= max(demand.monthly_peaks_list_el)
    assert Q_(0, ureg.Btu / ureg.hour) <= min(demand.hl)
    assert max(demand.hl) == demand.annual_peak_hl <= max(demand.monthly_peaks_list_hl)
    assert 0 < demand.grid_efficiency < 1
    assert 0 < demand.sim_ab_efficiency < 1
    assert 1 <= demand.summer_start_month <= 12
    assert 1 <= demand.winter_start_month <= 12
    assert 0 < demand.summer_weight_el.magnitude < 1
    assert 0 < demand.summer_weight_hl.magnitude < 1
    assert 0 < demand.winter_weight_el.magnitude < 1
    assert 0 < demand.winter_weight_hl.magnitude < 1
    assert Q_(0, ureg.kWh) < demand.annual_sum_el
    assert Q_(0, ureg.Btu) < demand.annual_peak_hl
    assert Q_(0, ureg.kWh) <= min(demand.monthly_sums_list_el)
    assert Q_(0, ureg.Btu) <= min(demand.monthly_sums_list_hl)
    assert max(demand.monthly_sums_list_el) <= demand.annual_sum_el
    assert max(demand.monthly_sums_list_hl) <= demand.annual_sum_hl


def test_emissions_class(class_info):
    """
   Checks that the data types, units, array sizes, and value ranges for this
   class are within expectations

   Parameters
   ----------
   class_info: dict
       Contains all initialized classes from the conftest.py file
   """
    # Assign class values
    em = class_info['emissions']

    # Check that argument passed is correct
    assert em is not None
    assert isinstance(em, classes.Emissions)

    # Check data types
    assert isinstance(em.ng_co2, pint.Quantity)
    assert isinstance(em.avg_emissions, dict)

    # Check pint units
    assert em.ng_co2.units == ureg.kg / ureg.megaBtu
    test_index = rand.sample(population=em.avg_emissions.keys(), k=1)[0]
    assert em.avg_emissions[test_index].units == ureg.lbs / ureg.MWh

    # Check array sizes
    assert len(em.avg_emissions) == 12

    # Check value ranges
    assert 0 < em.ng_co2.magnitude < 20
    assert 0 < em.avg_emissions[test_index].magnitude < 1800


def test_costs_class(class_info):
    """
   Checks that the data types, units, array sizes, and value ranges for this
   class are within expectations

   Parameters
   ----------
   class_info: dict
       Contains all initialized classes from the conftest.py file
   """
    # Assign class values
    costs_class = class_info['costs']

    # Check that argument passed is correct
    assert costs_class is not None
    assert isinstance(costs_class, classes.EnergyCosts)

    # Check data types
    assert isinstance(costs_class.meter_type_el, str)
    assert isinstance(costs_class.meter_type_fuel, str)
    assert isinstance(costs_class.schedule_type_el, list)
    assert isinstance(costs_class.schedule_type_el[0], str)
    assert isinstance(costs_class.schedule_type_fuel, list)
    assert isinstance(costs_class.schedule_type_fuel[0], str)
    assert isinstance(costs_class.master_meter_el_dict, dict)
    assert isinstance(costs_class.single_meter_el_dict, dict)
    assert isinstance(costs_class.master_meter_fuel_dict, dict)
    assert isinstance(costs_class.single_meter_fuel_dict, dict)


def test_chp_class(class_info):
    """
    Checks that the data types, units, array sizes, and value ranges for this
    class are within expectations

    Parameters
    ----------
    class_info: dict
        Contains all initialized classes from the conftest.py file
    """
    # Assign class values
    chp = class_info['chp']

    # Check that argument passed is correct
    assert chp is not None
    assert isinstance(chp, classes.CHP)

    # Check data types
    assert isinstance(chp.min_pl, float)
    assert isinstance(chp.installed_cost, pint.Quantity)

    # Check Pint units
    assert chp.installed_cost.units == 1/ureg.kW

    # Check value ranges
    assert 0 <= chp.min_pl < 1
    assert 0 < chp.installed_cost.magnitude


def test_tes_class(class_info):
    """
    Checks that the data types, units, array sizes, and value ranges for this
    class are within expectations

    Parameters
    ----------
    class_info: dict
        Contains all initialized classes from the conftest.py file
    """
    # Assign class values
    tes = class_info['tes']

    # Check that argument passed is correct
    assert tes is not None
    assert isinstance(tes, classes.TES)

    # Check data types
    assert isinstance(tes.start, float)
    assert isinstance(tes.vol_rate, pint.Quantity)
    assert isinstance(tes.energy_density, pint.Quantity)
    assert isinstance(tes.discharge_kw, pint.Quantity)
    assert isinstance(tes.size_cost, pint.Quantity)     # TODO: raname variable?
    assert isinstance(tes.rate_cost, pint.Quantity)     # TODO: raname variable?

    # Check Pint units
    assert tes.vol_rate.check('[volume]/[time]')
    assert tes.energy_density.check('[energy]/[volume]')
    assert tes.discharge_kw.check('[power]')
    assert tes.size_cost.check('1/[energy]')
    assert tes.rate_cost.check('1/[power]')

    # Check value ranges
    assert 0 <= tes.start <= 1
    assert 0 < tes.vol_rate.magnitude
    assert 0 < tes.energy_density.magnitude
    assert 0 < tes.discharge_kw.magnitude
    assert 0 < tes.size_cost.magnitude
    assert 0 < tes.rate_cost.magnitude


def test_aux_boiler_class(class_info):
    """
    Checks that the data types, units, array sizes, and value ranges for this
    class are within expectations

    Parameters
    ----------
    class_info: dict
        Contains all initialized classes from the conftest.py file
    """
    # Assign class values
    ab = class_info['ab']

    # Check that argument passed is correct
    assert ab is not None
    assert isinstance(ab, classes.AuxBoiler)

    # Check data types
    assert isinstance(ab.eff, float)

    # Check value ranges
    assert 0 < ab.eff < 1
