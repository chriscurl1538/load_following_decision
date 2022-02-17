"""
Module Description:
    Contains functions needed to calculate the economics of electrical load following
    and thermal load following mCHP energy dispatch options

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
    electric_demand_hourly: numpy.ndarray
        contains 8760 rows and 1 column. Items in the array must be convertible to float.
    chp_cap: float
        Size of the CHP system in kW (kilowatts)
    chp_min: float
        The minimum load of the system as a percentage of chp_cap. Calculated from the
        turn-down ratio
    chp_pl: numpy.ndarray
        Array of part-loads (first col) and their associated part-load efficiencies
        (second col)
    """
    energy_demand = classes.EnergyDemand()
    electric_cost = energy_demand.el_cost

    chp = classes.CHP()

    electric_demand_hourly = energy_demand.el[1:, -1]
    chp_cap = chp.cap
    chp_pl = chp.pl

    try:
        chp_min = chp_cap / chp.td
    except ZeroDivisionError:
        chp_min = 0

    return electric_demand_hourly, chp_cap, chp_min, chp_pl, electric_cost


def is_electric_utility_needed(demand_hourly=np.empty(shape=[8760, 1])):
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
    if demand_hourly.size is 0:
        return None
    else:

        x = get_class_info()
        chp_cap = x[1]
        chp_min = x[2]

        # Verifies input array size
        rows = demand_hourly.shape[0]
        try:
            cols = demand_hourly.shape[1]
        except IndexError:
            cols = 1
        assert rows == 8760
        assert cols == 1

        utility_needed = []

        for i in range(rows):
            # Verifies input dtype
            try:
                demand = float(demand_hourly[i])
            except ValueError:
                return ValueError

            # Verifies acceptable input value range
            assert demand >= 0

            if chp_min <= demand <= chp_cap:
                utility_needed.append(False)
            else:
                utility_needed.append(True)

        return utility_needed


def calculate_ELF_annual_electricity_cost(demand_hourly=None):
    """
    Calculates the cost of electricity provided by the local utility.

    This function calls the is_electric_utility_needed function and uses the
    boolean array from that function. Assumes that energy dispatch for the
    mCHP system is electric load following (ELF)

    Parameters
    ----------
    demand_hourly: numpy.ndarray
        contains 8760 rows and 1 column. Items in the array must be convertible to float.

    Returns
    -------
    annual_cost: float
        The total annual cost of electricity bought from the local utility
    """
    if demand_hourly is not None:

        x = get_class_info()
        chp_cap = x[1]
        chp_min = x[2]
        electric_rate = x[4]

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


def calculate_part_load_efficiency(demand_hourly=None):
    # TODO: Can be improved by linearizing the array for a more accurate efficiency value
    """
    Calculates the hourly mCHP efficiency using part-load efficiency data.

    Parameters
    ----------
    demand_hourly: numpy.ndarray
        contains 8760 rows and 1 column. Items in the array must be convertible to float.

    Returns
    -------
    efficiency_array: numpy.ndarray
        Array of efficiency values from the chp_pl array that correspond to the
        partload closest to the actual partload during that hour.
    """
    if demand_hourly is not None:

        x = get_class_info()
        chp_cap = x[1]
        chp_pl = x[3]

        rows = demand_hourly.shape[0]
        partload_list = []

        for i in range(1, rows):
            demand = float(demand_hourly[i, -1])
            partload_actual = demand/chp_cap
            idx = np.searchsorted(chp_pl[:, 0], partload_actual, side="left")
            partload_list.append(chp_pl[idx])
        partload_array = np.array(partload_list)
        efficiency_array = partload_array[:, 1]
        return efficiency_array


# TODO: Function is unfinished
# def calculate_ELF_annual_chp_fuel_cost():
#     """
#     Calculates the fuel cost for the mCHP system.
#
#     Assumes that energy dispatch for the mCHP system is electric load
#     following (ELF).
#
#     Parameters
#     ---------
#
#     Returns
#     -------
#
#     """
#     return None


if __name__ == '__main__':
    x = is_electric_utility_needed()
    print(x)
