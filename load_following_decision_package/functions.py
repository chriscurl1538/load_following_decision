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


def load_data_processing():
    """
    Analyzes raw hourly load profile data from Building class. Reduces resolution
    from hourly to daily/monthly.
    :return: Graphs, probably
    """
    return None


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


# Note: Can add function def main(): that calls all other functions in the proper order

if __name__ == '__main__':
    # This statement reads true if the file is run from the command line (False if imported)
    # If imported, then __name__ == "functions" and this statement reads False
    print('executed')
