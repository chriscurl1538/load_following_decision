"""
Module Description:
    Contains functions needed to calculate the economics of electrical load following
    mCHP energy dispatch option

Assumptions:
    Fuel = Natural gas
    Prime Mover = Internal combustion engine
    Building = Mid-rise Apartment
    Other Equipment = Auxiliary Boiler, Thermal energy storage (TES) system
    Net metering is not allowed

Current prioritization of equipment in order of which addresses energy needs first:
    mCHP
    Aux Boiler
    Thermal storage
"""

import classes
import numpy as np


def calc_utility_electricity_needed():
    """
    This function compares mCHP capacity and minimum allowed electrical generation
    with hourly electrical demand. If demand is too high or too low, it calculates
    how much electricity needs to be purchased from the utility.

    Returns
    -------
    utility_needed: list
        contains float values for how many kWh of electricity needs to be purchased
        from the utility
    """
    chp = classes.CHP()
    chp_cap = chp.cap
    try:
        chp_min = chp_cap / chp.td
    except ZeroDivisionError:
        chp_min = 0

    demand = classes.EnergyDemand()
    demand_hourly = demand.el

    utility_needed = []

    for i in range(demand_hourly.shape[0]):
        # Verifies input dtype
        demand = float(demand_hourly[i])

        # Verifies acceptable input value range
        assert demand >= 0

        if chp_min <= demand <= chp_cap:
            supply = 0
            utility_needed.append(supply)
        elif demand < chp_min:
            supply = demand
            utility_needed.append(supply)
        elif chp_cap < demand:
            supply = abs(demand - chp_cap)
            utility_needed.append(supply)
        else:
            raise Exception("Error in ELF calc_utility_electricity_needed function")

    return utility_needed


def calc_annual_electric_cost():
    """
    Calculates the cost of electricity provided by the local utility.

    This function calls the calc_utility_electricity_needed function and uses the
    calculated utility electricity needed. Assumes that energy dispatch for the
    mCHP system is electric load following (ELF)

    Returns
    -------
    annual_cost: float
        The total annual cost of electricity bought from the local utility
    """

    demand = classes.EnergyDemand()
    electric_rate = demand.el_cost

    cost = []

    utility_needed = calc_utility_electricity_needed()

    for i in range(len(utility_needed)):
        hourly_cost = utility_needed[i] * electric_rate
        cost.append(hourly_cost)
    annual_cost = sum(cost)
    return annual_cost


# TODO: Change this to TES storage assignment (storage should be prioritized over running the boiler)
def calc_aux_boiler_output():
    """
    Using CHP turn down ratio and heat to power ratio, this function determines when the
    heat demand exceeds the heat produced by the electric load following CHP system. Heat
    demand not met by CHP is then assigned to the aux boiler (added to boiler_heat list).
    Items in the list are then verified to be within boiler operating parameters.

    Returns
    -------
    boiler_heat: list
        Hourly heat output of the auxiliary boiler
    """
    chp = classes.CHP()
    chp_cap = chp.cap
    chp_hp = chp.hp
    try:
        chp_min = chp_cap / chp.td
    except ZeroDivisionError:
        chp_min = 0

    demand = classes.EnergyDemand()
    el_demand_hourly = demand.el
    heat_demand_hourly = demand.hl

    ab = classes.AuxBoiler()
    ab_cap = ab.cap
    ab_min = ab.cap / ab.td

    boiler_heat = []

    for i in range(el_demand_hourly.shape[0]):
        # Verifies input dtype
        el_demand = float(el_demand_hourly[i])
        heat_demand = float(heat_demand_hourly[i])

        # Verifies acceptable input value range
        assert el_demand >= 0
        assert heat_demand >= 0

        if chp_min <= el_demand <= chp_cap:
            chp_heat = el_demand * chp_hp   # Compare heat generated to heat demand
            if chp_heat < heat_demand:
                ab_heat = abs(heat_demand - chp_heat)
                boiler_heat.append(ab_heat)
            else:
                ab_heat = 0
                boiler_heat.append(ab_heat)
        elif el_demand < chp_min:
            heat = heat_demand
            boiler_heat.append(heat)
        elif chp_cap < el_demand:
            chp_heat = chp_cap * chp_hp
            heat = abs(heat_demand - chp_heat)
            boiler_heat.append(heat)
        else:
            raise Exception("Error in ELF calc_aux_boiler_output function: Heat demand is less than minimum allowed aux"
                            "boiler output")

    # Check that hourly heat demand is within aux boiler operating parameters
    for i in boiler_heat:
        if ab_min < i < ab_cap:
            pass
        elif i < ab_min:
            i = 0
        elif ab_cap < i:
            i = ab_cap

    return boiler_heat


# TODO: Change to aux boiler (storage should be prioritized over running the boiler)
def calc_heat_storage_needed():
    """
    Using the list of hourly boiler heat output from the calc_aux_boiler_output() function,
    heat demands not met by CHP and the aux boiler are assigned to TES storage.

    Returns
    -------
    stored_heat: list
        Heat stored in the thermal storage system each hour
    """
    ab = classes.AuxBoiler()
    ab_cap = ab.cap

    boiler_heat = calc_aux_boiler_output()

    storage_needed = []
    stored_heat = []

    for i in range(len(boiler_heat)):
        if ab_cap < boiler_heat[i]:
            heat_diff = abs(boiler_heat[i] - ab_cap)
            stored_heat.append(heat_diff)
            storage_needed.append(True)
        elif boiler_heat[i] <= ab_cap:
            heat_diff = 0
            stored_heat.append(heat_diff)
            storage_needed.append(False)
        else:
            raise Exception("Error in ELF calc_heat_storage_needed function")

    return storage_needed, stored_heat


def calculate_electrical_part_load_efficiency():
    # TODO: Can be improved by linearizing the array for a more accurate efficiency value
    """
    Calculates the hourly mCHP efficiency using part-load efficiency data.

    Returns
    -------
    efficiency_array: numpy.ndarray
        Array of efficiency values from the chp_pl array that correspond to the
        partload closest to the actual partload during that hour.
    """
    chp = classes.CHP()
    chp_cap = chp.cap
    chp_pl = chp.pl

    demand = classes.EnergyDemand()
    demand_hourly = demand.el

    if demand_hourly is not None:

        rows = demand_hourly.shape[0]
        partload_list = []

        for i in range(rows):
            demand = float(demand_hourly[i])
            partload_actual = demand/chp_cap
            idx = np.searchsorted(chp_pl[:, 0], partload_actual, side="left")
            partload_list.append(chp_pl[idx])
        partload_array = np.array(partload_list)
        efficiency_array = partload_array[:, 1]
        return efficiency_array


# Uses the above part load efficiency function
def calculate_hourly_chp_fuel_use():
    """
    Calculates the fuel use of the mCHP system. First it uses the heat to power ratio
    and hourly electrical demand to calculate the hourly heat output of the CHP unit
    in MMBtu. Then it uses the hourly heat output and the thermal output to fuel input
    ratio to calculate the hourly fuel use in MMBtu.

    Assumes that energy dispatch for the mCHP system is electric load
    following (ELF).

    Returns
    -------
    fuel_use: float
        Annual sum of mCHP fuel use.
    """

    chp = classes.CHP()
    chp_cap = chp.cap
    heat_power = chp.hp
    thermal_out_fuel_in = chp.out_in

    demand = classes.EnergyDemand()
    demand_hourly = demand.el

    utility_needed = calc_utility_electricity_needed()

    heat_out = []
    fuel_use = []

    for i in range(len(utility_needed)):
        if utility_needed[i] is False:
            heat = demand_hourly[i] * heat_power
            fuel_btu = heat / thermal_out_fuel_in
            heat_out.append(heat)
            fuel_use.append(fuel_btu)
        elif utility_needed[i] is True and demand_hourly[i] >= chp_cap:
            heat = chp_cap * heat_power
            fuel_btu = heat / thermal_out_fuel_in
            heat_out.append(heat)
            fuel_use.append(fuel_btu)
        else:
            heat = 0
            fuel_btu = 0
            heat_out.append(heat)
            fuel_use.append(fuel_btu)

        return fuel_use


if __name__ == '__main__':
    x = calc_utility_electricity_needed()
    print(x)
