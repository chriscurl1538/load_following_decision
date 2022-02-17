"""
Module Description:
    Contains functions needed to calculate the economics of thermal load following
    mCHP energy dispatch option

Assumptions:
    Fuel = Natural gas
    Prime Mover = Internal combustion engine
    Building = Mid-rise Apartment
    Other Equipment = Auxiliary Boiler, Thermal energy storage (TES) system
    Net metering is not allowed
"""

from load_following_decision_package import classes
import numpy as np


def get_class_info():
    """
    Retrieves data stored in classes from classes.py for use in this module.

    This function prevents classes from needing to be called in every function.

    Returns
    -------
    heat_demand_hourly: numpy.ndarray
        contains 8760 rows and 1 column. Items in the array must be convertible to float.
    chp_cap: float
        Size of the CHP system in kW (kilowatts)
    chp_min: float
        The minimum load of the system as a percentage of chp_cap. Calculated from the
        turn-down ratio
    chp_pl: numpy.ndarray
        Array of part-loads (first col) and their associated part-load efficiencies
        (second col)
    fuel_cost: float
        Cost of fuel in units of $/hr
    """
    energy_demand = classes.EnergyDemand()
    if energy_demand.demand_file_name == "default_file.csv":
        return None
    else:
        fuel_cost = energy_demand.fuel_cost
        heat_demand_hourly = energy_demand.hl

        chp = classes.CHP()

        chp_cap = chp.cap
        chp_pl = chp.pl

        try:
            chp_min = chp_cap / chp.td
        except ZeroDivisionError:
            chp_min = 0

        return heat_demand_hourly, chp_cap, chp_min, chp_pl, fuel_cost


def is_aux_boiler_needed():
    return None


def calculate_ab_fuel_use():
    return None


def calculate_chp_fuel_use():
    return None


def is_electric_utility_needed():
    return None


