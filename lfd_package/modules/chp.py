"""
Module Description:
    Contains functions needed to calculate the demand, electricity cost, and fuel use of
    the micro-chp unit for both electrical load following (ELF) and thermal load following
    (TLF) cases.
"""

import numpy as np
from lfd_package.modules.__init__ import ureg


def calc_hourly_efficiency(chp=None, demand=None, load_following_type=None):
    """
    Calculates the hourly mCHP efficiency using part-load electrical efficiency data.

    Note: This can be improved by linearizing the array for a more accurate efficiency value

    Parameters
    ---------
    chp: CHP Class
        contains initialized CHP class data using CLI inputs (see command_line.py)
    demand: EnergyDemand Class
        contains initialized EnergyDemand class data using CLI inputs (see command_line.py)
    load_following_type: string
        specifies whether calculation is for electrical load following (ELF) state
        or thermal load following (TLF) state.

    Returns
    -------
    eff_list: list
        Array of efficiency values from the chp_pl array that correspond to the
        part-load closest to the actual part-load during that hour.
    """
    if chp is not None and demand is not None and load_following_type is not None:
        # Convert chp max output to kWh using data resolution
        data_res = 1 * ureg.hour
        chp_max_kwh = chp.cap * data_res
        chp_pl = chp.pl
        eff_list = []

        if load_following_type is "ELF":
            chp_electric_gen_hourly = elf_calc_electricity_bought_and_generated(chp=chp, demand=demand)[1]
        elif load_following_type is "TLF":
            chp_electric_gen_hourly = tlf_calc_electricity_bought_and_generated(chp=chp, demand=demand)[1]
        else:
            raise Exception("Error in calc_hourly_efficiency function")

        for i, k in enumerate(chp_electric_gen_hourly):
            gen = k
            partload_actual = gen/chp_max_kwh

            # Grabs the first column and calculates difference
            part_loads = chp_pl[:, 0]
            desired_shape = np.shape(part_loads)
            actual_load_array = np.full(shape=desired_shape, fill_value=partload_actual.magnitude)
            diff = np.abs(part_loads, actual_load_array)
            idx = diff.argmin()

            part_effs = chp_pl[idx, 1]
            eff_list.append(part_effs)
        return eff_list


def calc_annual_fuel_use_and_costs(chp=None, demand=None, load_following_type=None):
    """
    Uses hourly electrical efficiency values (electricity generated / fuel used)
    and hourly electricity generated to calculate fuel use for each hour. Also
    calculates the annual fuel costs.

    Parameters
    ---------
    chp: CHP Class
        contains initialized CHP class data using CLI inputs (see command_line.py)
    demand: EnergyDemand Class
        contains initialized EnergyDemand class data using CLI inputs (see command_line.py)
    load_following_type: string
        specifies whether calculation is for electrical load following (ELF) state
        or thermal load following (TLF) state.

    Returns
    -------
    annual_fuel_use_btu: float
        Annual fuel use in Btu.
    annual_fuel_cost: float
        annual fuel cost for the mCHP unit
    """
    if chp is not None and demand is not None:
        efficiency_list = calc_hourly_efficiency(chp=chp, demand=demand, load_following_type=load_following_type)
        if load_following_type is "ELF":
            chp_electric_gen_hourly = elf_calc_electricity_bought_and_generated(chp=chp, demand=demand)[1]
        elif load_following_type is "TLF":
            chp_electric_gen_hourly = tlf_calc_electricity_bought_and_generated(chp=chp, demand=demand)[1]
        else:
            raise Exception("Error in calc_annual_fuel_use_and_costs function")

        fuel_use = []

        for i, k in enumerate(efficiency_list):
            if k is not 0:
                electricity_gen_kwh = chp_electric_gen_hourly[i]
                fuel_kwh = electricity_gen_kwh / k
                fuel_btu = fuel_kwh.to(ureg.Btu)
                fuel_use.append(fuel_btu)
            else:
                fuel_use.append(0 * ureg.Btu)

        annual_fuel_use_btu = sum(fuel_use)
        annual_fuel_use_mmbtu = annual_fuel_use_btu.to(ureg.megaBtu)
        annual_fuel_cost = annual_fuel_use_mmbtu * demand.fuel_cost
        return annual_fuel_use_btu, annual_fuel_cost


def calc_annual_electric_cost(chp=None, demand=None, load_following_type=None):
    """
    Calculates the annual cost of electricity bought from the local utility.

    This function calls either the elf_calc_electricity_bought_and_generated function
    (or the tlf_calc_electricity_bought_and_generated function) and uses the
    calculated utility electricity needed.

    Parameters
    ---------
    chp: CHP Class
        contains initialized CHP class data using CLI inputs (see command_line.py)
    demand: EnergyDemand Class
        contains initialized EnergyDemand class data using CLI inputs (see command_line.py)
    load_following_type: string
        specifies whether calculation is for electrical load following (ELF) state
        or thermal load following (TLF) state.

    Returns
    -------
    annual_cost: float
        The total annual cost of electricity bought from the local utility
    """
    if demand is not None and chp is not None and load_following_type is not None:
        electric_rate = demand.el_cost

        if load_following_type is "ELF":
            total_bought = sum(elf_calc_electricity_bought_and_generated(chp=chp, demand=demand)[0])
        elif load_following_type is "TLF":
            total_bought = sum(tlf_calc_electricity_bought_and_generated(chp=chp, demand=demand)[0])
        else:
            raise Exception("Error in chp.py function, calc_annual_electric_cost")
        annual_cost = total_bought * electric_rate

        return annual_cost


"""
ELF Functions
"""


def elf_calc_electricity_bought_and_generated(chp=None, demand=None):
    """
    Calculates the electricity generated by the chp system and the electricity bought
    from the local utility to make up the difference.

    This function compares mCHP capacity and minimum allowed electrical generation
    with hourly electrical demand. If demand is too high or too low, it calculates
    how much electricity needs to be purchased from the utility each hour. Also
    calculates electricity generated by the mCHP unit each hour.

    Assumes the load following state is electrical load following (ELF).

    Parameters
    ---------
    chp: CHP Class
        contains initialized CHP class data using CLI inputs (see command_line.py)
    demand: EnergyDemand Class
        contains initialized EnergyDemand class data using CLI inputs (see command_line.py)

    Returns
    -------
    utility_bought_list: list
        contains float values for electricity purchased hourly
    chp_gen_list: list
        contains float values for electricity generated hourly
    """
    if chp is not None and demand is not None:
        # Convert max and min chp output to kWh using data resolution
        data_res = 1 * ureg.hour
        chp_max_kwh = chp.cap * data_res
        chp_min_kwh = chp.min * data_res
        demand_hourly = demand.el

        utility_bought_list = []
        chp_gen_list = []

        for d in demand_hourly:
            # Verifies acceptable input value range
            assert d >= 0

            if chp_min_kwh <= d <= chp_max_kwh:
                bought = 0 * ureg.kWh
                gen = d
                utility_bought_list.append(bought)
                chp_gen_list.append(gen)
            elif d < chp_min_kwh:
                bought = d
                gen = 0 * ureg.kWh
                utility_bought_list.append(bought)
                chp_gen_list.append(gen)
            elif chp_max_kwh < d:
                bought = d - chp_max_kwh
                gen = chp_max_kwh
                utility_bought_list.append(bought)
                chp_gen_list.append(gen)
            else:
                raise Exception("Error in ELF calc_utility_electricity_needed function")

        return utility_bought_list, chp_gen_list


def elf_calc_hourly_heat_generated(chp=None, demand=None):
    """
    Uses heat to power ratio and hourly electricity generated to calculate
    hourly thermal output of the mCHP unit.

    Assumes the load following state is electrical load following (ELF).

    Parameters
    ---------
    chp: CHP Class
        contains initialized CHP class data using CLI inputs (see command_line.py)
    demand: EnergyDemand Class
        contains initialized EnergyDemand class data using CLI inputs (see command_line.py)

    Returns
    -------
    hourly_heat: list
        Hourly thermal output of the mCHP unit
    """
    if chp is not None and demand is not None:
        heat_to_power = chp.hp
        electricity_generated = elf_calc_electricity_bought_and_generated(chp=chp, demand=demand)[1]
        hourly_heat = []

        for i, k in enumerate(electricity_generated):
            heat_kwh = heat_to_power * electricity_generated[i]
            heat = heat_kwh.to(ureg.Btu)
            hourly_heat.append(heat)

        return hourly_heat


"""
TLF Functions
"""


def tlf_calc_hourly_heat_generated(chp=None, demand=None):
    """
    Calculates the hourly heat generated by the chp system.

    This function compares the thermal demand of the building with the max and
    min heat that can be generated by the chp system. Unlike the ELF case, this
    function allows generation when demand is below chp minimum heat output with
    excess sent to heat storage (TES).

    Assumes the load following state is thermal load following (TLF).

    Parameters
    ----------
    chp: CHP Class
        contains initialized CHP class data using CLI inputs (see command_line.py)
    demand: EnergyDemand Class
        contains initialized EnergyDemand class data using CLI inputs (see command_line.py)

    Returns
    -------
    chp_gen_list: list
        contains hourly heat generated by the chp system in Btu.
    """
    if chp is not None and demand is not None:
        # Convert max and min chp output to kWh thermal using data resolution
        data_res = 1 * ureg.hour
        chp_max_kwh = chp.cap * data_res * chp.hp
        chp_min_kwh = chp.min * data_res * chp.hp
        demand_hourly = demand.hl

        chp_gen_list = []

        for i, d in enumerate(demand_hourly):
            # Verifies acceptable input value range
            assert d >= 0

            if chp_min_kwh <= d <= chp_max_kwh:
                gen = d
                chp_gen_list.append(gen.to(ureg.Btu))
            elif d < chp_min_kwh:                   # TODO: Account for excess gen going to storage?
                gen = 0 * ureg.Btu
                chp_gen_list.append(gen.to(ureg.Btu))
            elif chp_max_kwh < d:
                gen = chp_max_kwh
                chp_gen_list.append(gen.to(ureg.Btu))
            else:
                raise Exception("Error in TLF calc_utility_electricity_needed function")

        return chp_gen_list


def tlf_calc_electricity_bought_and_generated(chp=None, demand=None):
    if chp is not None and demand is not None:
        heat_to_power = chp.hp
        heat_generated = tlf_calc_hourly_heat_generated(chp=chp, demand=demand)

        hourly_electricity_gen = []
        hourly_electricity_bought = []

        electric_demand = demand.el

        for i, k in enumerate(heat_generated):
            heat_gen_kwh = k.to(ureg.kWh)
            electric_kwh = heat_gen_kwh / heat_to_power
            hourly_electricity_gen.append(electric_kwh)
            if electric_demand[i] > electric_kwh:
                bought = electric_demand[i] - electric_kwh
                hourly_electricity_bought.append(bought)
            else:
                bought = 0 * ureg.kWh
                hourly_electricity_bought.append(bought)
        return hourly_electricity_bought, hourly_electricity_gen
