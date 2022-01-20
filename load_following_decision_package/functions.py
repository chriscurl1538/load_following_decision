"""
Calculates the economics for electrical and thermal load following
 Assumptions:
 Fuel = NG
 Prime Mover = ICE
 Building = Mid-rise Apartment, 50 units, 700 scf each
 Other Equipment = Aux Boiler, TES
"""

import classes
import command_line
from pint import UnitRegistry as ureg


def calc_fuel_use():    # Create class to track this?
    """
    Calculates the amount of fuel used by the auxiliary boiler and mCHP package.
    Requires part-load efficiency data for the mCHP system, electrical and thermal
    load profiles for the building, heat to power ratio, and the HHV value for the fuel.
    :return: Sum of annual fuel use
    """
    return None


def sum_energy_wasted():    # Tracked in a class
    return None


if __name__ == '__main__':
    print('executed')
