"""
Module Description:
    Contains functions needed to calculate the demand, electricity cost, and fuel use of
    the micro-chp unit for both electrical load following (ELF) and thermal load following
    (TLF) cases. Also accounts for whether net metering is permitted by the local utility.
"""

from lfd_package.modules import chp_tes_sizing as sizing
from lfd_package.modules.__init__ import ureg, Q_


def calc_avg_efficiency(chp=None, demand=None, load_following_type=None):
    """
    TODO: Docstring updated 9/24/2022
    Calculates the average CHP electrical and thermal efficiencies using part-load
    efficiency data.

    Used in calc_annual_fuel_use_and_costs function

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
    avg_el_eff: float
        Average electrical efficiency of the CHP system based on linear fit approximation.
    avg_th_eff: float
        Average thermal efficiency of CHP system based on second order polynomial fit
        approximation.
    """
    if chp is not None and demand is not None and load_following_type is not None:
        if demand.net_metering_status is True:
            fuel_use_kw = sizing.electrical_output_to_fuel_consumption(chp.cap)
            thermal_output_kw = sizing.electrical_output_to_thermal_output(chp.cap)
            avg_el_eff = chp.cap / fuel_use_kw
            avg_th_eff = thermal_output_kw / fuel_use_kw
            return avg_el_eff, avg_th_eff
        elif load_following_type is "ELF" and demand.net_metering_status is False:
            chp_electric_gen_hourly = elf_calc_electricity_bought_and_generated(chp=chp, demand=demand)[1]
        elif load_following_type is "TLF" and demand.net_metering_status is False:
            chp_electric_gen_hourly = tlf_calc_electricity_bought_and_generated(chp=chp, demand=demand)[1]
        else:
            raise Exception("Error in calc_hourly_efficiency function")

        # Efficiency lists
        el_eff_list = []
        th_eff_list = []

        for i, el_gen in enumerate(chp_electric_gen_hourly):
            # Calculate efficiencies
            fuel_use_kw = sizing.electrical_output_to_fuel_consumption(el_gen)
            thermal_output_kw = sizing.electrical_output_to_thermal_output(el_gen)
            el_eff_item = el_gen/fuel_use_kw
            th_eff_item = thermal_output_kw/fuel_use_kw

            el_eff_list.append(el_eff_item)
            th_eff_list.append(th_eff_item)

        avg_el_eff = sum(el_eff_list) / len(el_eff_list)
        avg_th_eff = sum(th_eff_list) / len(th_eff_list)

        return avg_el_eff, avg_th_eff


def calc_annual_fuel_use_and_costs(chp=None, demand=None, load_following_type=None):
    """
    TODO: Docstring updated 9/24/2022
    Uses average electrical efficiency and average CHP electricity generation to calculate
    annual fuel use and annual fuel costs.

    Used in the command_line.py module

    Parameters
    ---------
    chp: CHP Class
        contains initialized class data using CLI inputs (see command_line.py)
    demand: EnergyDemand Class
        contains initialized class data using CLI inputs (see command_line.py)
    load_following_type: string
        specifies whether calculation is for electrical load following (ELF) state
        or thermal load following (TLF) state.

    Returns
    -------
    annual_fuel_use_btu: Quantity (float)
        Annual fuel use in units of Btu.
    annual_fuel_cost: float
        Annual fuel cost for the CHP unit in USD
    """
    if chp is not None and demand is not None:
        avg_el_eff = calc_avg_efficiency(chp=chp, demand=demand, load_following_type=load_following_type)[0]

        if demand.net_metering_status is True:
            fuel_use_kw = sizing.electrical_output_to_fuel_consumption(chp.cap)
            annual_fuel_use_btu = (fuel_use_kw * chp.available_hours).to(ureg.Btu)
            annual_fuel_use_mmbtu = annual_fuel_use_btu.to(ureg.megaBtu)
            annual_fuel_cost = annual_fuel_use_mmbtu * demand.fuel_cost
            return annual_fuel_use_btu, annual_fuel_cost
        elif load_following_type is "ELF" and demand.net_metering_status is False:
            chp_electric_gen_hourly = elf_calc_electricity_bought_and_generated(chp=chp, demand=demand)[1]
        elif load_following_type is "TLF" and demand.net_metering_status is False:
            chp_electric_gen_hourly = tlf_calc_electricity_bought_and_generated(chp=chp, demand=demand)[1]
        else:
            raise Exception("Error in calc_annual_fuel_use_and_costs function")

        # Calculate fuel use
        avg_electric_gen_kw = sum(chp_electric_gen_hourly) / len(chp_electric_gen_hourly)
        annual_electric_gen_kwh = avg_electric_gen_kw * chp.available_hours
        annual_fuel_use_kwh = annual_electric_gen_kwh / avg_el_eff
        annual_fuel_use_btu = annual_fuel_use_kwh.to(ureg.Btu)

        # Calculate fuel cost
        annual_fuel_use_mmbtu = annual_fuel_use_btu.to(ureg.megaBtu)
        annual_fuel_cost = annual_fuel_use_mmbtu * demand.fuel_cost

        return annual_fuel_use_btu, annual_fuel_cost


def calc_annual_electric_cost(chp=None, demand=None, load_following_type=None):
    """
    TODO: Docstring updated 9/24/2022
    Calculates the annual cost of electricity bought from the local utility.

    Used in the command_line.py module

    Parameters
    ---------
    chp: CHP Class
        contains initialized class data using CLI inputs (see command_line.py)
    demand: EnergyDemand Class
        contains initialized class data using CLI inputs (see command_line.py)
    load_following_type: string
        specifies whether calculation is for electrical load following (ELF) state
        or thermal load following (TLF) state.

    Returns
    -------
    annual_cost: float
        The total annual cost of electricity bought from the local utility in USD
    """
    if demand is not None and chp is not None and load_following_type is not None:
        if demand.net_metering_status is True:
            annual_cost = chp.cap * chp.available_hours * demand.el_cost
            return annual_cost
        elif load_following_type is "ELF" and demand.net_metering_status is False:
            total_bought = sum(elf_calc_electricity_bought_and_generated(chp=chp, demand=demand)[0])
        elif load_following_type is "TLF" and demand.net_metering_status is False:
            total_bought = sum(tlf_calc_electricity_bought_and_generated(chp=chp, demand=demand)[0])
        else:
            raise Exception("Error in chp.py function, calc_annual_electric_cost")
        annual_cost = total_bought * demand.el_cost

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
        utility_bought_kwh_list = []
        chp_gen_kwh_list = []

        for d in demand.el:
            # Verifies acceptable input value range
            assert d >= 0

            if chp.min <= d <= chp.cap:
                bought = 0 * ureg.kWh
                gen = d * ureg.hour
                utility_bought_kwh_list.append(bought)
                chp_gen_kwh_list.append(gen)
            elif d < chp.min:
                bought = d * ureg.hour
                gen = 0 * ureg.kWh
                utility_bought_kwh_list.append(bought)
                chp_gen_kwh_list.append(gen)
            elif chp.cap < d:
                bought = d * ureg.hour - chp.cap * ureg.hour
                gen = chp.cap * ureg.hour
                utility_bought_kwh_list.append(bought)
                chp_gen_kwh_list.append(gen)
            else:
                raise Exception("Error in ELF calc_utility_electricity_needed function")

        return utility_bought_kwh_list, chp_gen_kwh_list


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
        electricity_generated = elf_calc_electricity_bought_and_generated(chp=chp, demand=demand)[1]
        hourly_heat_rate = []

        for i, el_gen in enumerate(electricity_generated):
            heat_kw = sizing.electrical_output_to_thermal_output(el_gen)
            heat = heat_kw.to(ureg.Btu / ureg.hour)
            hourly_heat_rate.append(heat)

        return hourly_heat_rate


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
        chp_hourly_heat_rate_list = []
        chp_heat_rate_min = sizing.electrical_output_to_thermal_output(chp.min)
        chp_heat_rate_cap = sizing.electrical_output_to_thermal_output(chp.cap)

        for i, dem in enumerate(demand.hl):
            # Verifies acceptable input value range
            assert dem >= 0

            if chp_heat_rate_min <= dem <= chp_heat_rate_cap:
                chp_heat_rate_item = dem
                chp_hourly_heat_rate_list.append(chp_heat_rate_item)
            elif dem < chp_heat_rate_min:                   # TODO: Account for excess gen going to storage?
                gen = 0 * (ureg.Btu / ureg.hour)
                chp_hourly_heat_rate_list.append(gen)
            elif chp_heat_rate_cap < dem:
                gen = chp_heat_rate_cap
                chp_hourly_heat_rate_list.append(gen)
            else:
                raise Exception("Error in TLF calc_utility_electricity_needed function")

        return chp_hourly_heat_rate_list


def tlf_calc_electricity_bought_and_generated(chp=None, demand=None):
    if chp is not None and demand is not None:
        heat_generated = tlf_calc_hourly_heat_generated(chp=chp, demand=demand)

        hourly_electricity_gen = []
        hourly_electricity_bought = []

        electric_demand = demand.el

        for i, hourly_heat_rate in enumerate(heat_generated):
            heat_gen_kw = hourly_heat_rate.to(ureg.kW)
            electric_gen_kwh = sizing.thermal_output_to_electrical_output(heat_gen_kw) * Q_(1, ureg.hour)
            hourly_electricity_gen.append(electric_gen_kwh)
            electric_demand_item_kwh = electric_demand[i] * Q_(1, ureg.hour)
            if electric_demand_item_kwh > electric_gen_kwh:
                bought = electric_demand_item_kwh - electric_gen_kwh
                hourly_electricity_bought.append(bought)
            else:
                bought = Q_(0, ureg.kWh)
                hourly_electricity_bought.append(bought)
        return hourly_electricity_bought, hourly_electricity_gen
