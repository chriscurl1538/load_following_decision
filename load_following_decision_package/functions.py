"""
Module Description:
    Contains functions needed to calculate the economics of electrical load following
    and thermal load following mCHP energy dispatch options
 Assumptions:
 Fuel = Natural gas
 Prime Mover = Internal combustion engine
 Building = Mid-rise Apartment
 Other Equipment = Auxiliary Boiler, Thermal energy storage (TES) system
"""
import numpy as np
from load_following_decision_package import classes

# TODO: Replace arguments with inputs from command line
# TODO: Create main() function within which classes and functions are called in order

"""
Global Variables (to be replaced with main() function)
"""
energy_demand = classes.EnergyDemand(file_name="test_input_load_profiles_hourly")
electric_demand_with_timestamp = energy_demand.el
electric_demand_hourly = electric_demand_with_timestamp[1:, -1]

chp = classes.CHP(capacity=50, heat_power=4, turn_down_ratio=3.3, part_load=np.array(
        [[30, 34.4], [40, 37.9], [50, 40.7], [60, 42.0], [70, 42.7], [80, 43.7], [90, 44.9], [100, 45.7]]))
chp_cap = chp.cap
chp_min = chp_cap / chp.td
chp_pl = chp.pl

"""
Functions
"""


def is_electric_utility_needed(demand_hourly=electric_demand_hourly):
    """
    This function compares mCHP capacity with hourly electrical demand.

    Parameters
    ----------
    demand_hourly: numpy.ndarray
        contains 8760 rows and 1 column. Items in the array must be convertible to float.

    Returns
    -------
    utility_needed: list
        contains boolean values that are true if mCHP operating parameters are
        insufficient to satisfy electricity demand
    """

    # Verifies input array size
    rows = demand_hourly.shape[0]
    try:
        cols = demand_hourly.shape[1]
    except IndexError:
        cols = 1

    try:
        assert rows == 8760
        assert cols == 1
    except AssertionError:
        return AssertionError

    utility_needed = []

    for i in range(rows):
        # Verifies input dtype
        try:
            demand = float(demand_hourly[i])
        except ValueError:
            return ValueError

        # Verifies acceptable input value range
        try:
            assert demand >= 0
        except AssertionError:
            return AssertionError

        if chp_min <= demand <= chp_cap:
            utility_needed.append(False)
        else:
            utility_needed.append(True)

    return utility_needed


def calculate_ELF_annual_electricity_cost(demand_hourly=electric_demand_hourly, electric_rate=0.1331):
    """
    Calculates the cost of electricity provided by the local utility.

    This function calls the is_electric_utility_needed function and uses the
    boolean array from that function. Assumes that energy dispatch for the
    mCHP system is electric load following (ELF)

    Parameters
    ----------
    demand_hourly: numpy.ndarray
        contains 8760 rows and 1 column. Items in the array must be convertible to float.

    electric_rate: float
        The cost of electricity in $/kWh

    Returns
    -------
    annual_cost: float
        The total annual cost of electricity bought from the local utility
    """
    cost = []

    utility_needed = is_electric_utility_needed()
    for i in range(len(utility_needed)):
        demand = float(demand_hourly[i])
        if utility_needed[i] is True and chp_cap < demand:
            diff = abs(chp_cap - demand)
            hour_cost = diff * electric_rate
            cost.append(hour_cost)
        elif utility_needed[i] is True and chp_min > demand:
            hour_cost = demand * electric_rate
            cost.append(hour_cost)
        else:
            pass
    annual_cost = sum(cost)
    return annual_cost


def calculate_part_load_efficiency():
    # TODO: Can be improved by linearizing the array for a more accurate efficiency value
    """
    Calculates the hourly mCHP efficiency using part-load efficiency data.

    Parameters
    ----------
    chp_pl: numpy.ndarray
        Array of partload percentages and efficiency values for the mCHP system.
        (Currently passed as a global variable rather than an argument.)

    Returns
    -------
    efficiency_array: numpy.ndarray
        Array of efficiency values from the chp_pl array that correspond to the
        partload closest to the actual partload during that hour.
    """
    rows = electric_demand_hourly.shape[0]
    partload_list = []

    for i in range(1, rows):
        demand = float(electric_demand_hourly[i, -1])
        partload_actual = demand/chp_cap
        idx = np.searchsorted(chp_pl[:, 0], partload_actual, side="left")
        partload_list.append(chp_pl[idx])
    partload_array = np.array(partload_list)
    efficiency_array = partload_array[:, 1]
    return efficiency_array


# TODO: Function is unfinished
def calculate_ELF_annual_chp_fuel_cost():
    """
    Calculates the fuel cost for the mCHP system.

    Assumes that energy dispatch for the mCHP system is electric load
    following (ELF).

    Parameters
    ---------

    Returns
    -------

    """
    return None


if __name__ == '__main__':
    print('executed')
