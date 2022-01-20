"""
Calculates the optimal load dispatch for a CHP system
 Assumptions:
 Fuel = NG
 Prime Mover = ICE
 Building = Mid-rise Apartment, 50 units, 700 scf each
 Other Equipment = Aux Boiler, TES
"""

import classes
from pint import UnitRegistry as ureg


def calc_fuel_use():    # Create class to track this?
    """
    Calculates the amount of fuel used by the auxiliary boiler and mCHP package.
    Requires part-load efficiency data for the mCHP system, electrical and thermal
    load profiles for the building, and the HHV value for the fuel.
    :param part_load_eff: Array of part-load conditions and corresponding electrical
    efficiency values
    :param heat_power_ratio: Ratio of heat produced by the mCHP package per unit of
    electricity produced
    :param thermal_load_profile: Thermal demand for the building (annual)
    :param electrical_load_profile: Electrical demand for the building (annual)
    :param fuel_HHV: Fuel HHV value
    :return: Sum of annual fuel use
    """
    return None


def sum_energy_wasted():    # Tracked in a class
    return None


if __name__ == '__main__':
    print('executed')
