"""
Module Description:
    Contains functions needed to calculate the demand, electricity cost, and fuel use of
    the micro-chp unit for both electrical load following (ELF) and thermal load following
    (TLF) cases. Also accounts for whether net metering is permitted by the local utility.
"""

from lfd_package.modules import chp_tes_sizing as sizing
from lfd_package.modules.__init__ import ureg, Q_


def calc_avg_efficiency(chp=None, demand=None, load_following_type=None, ab=None):
    """
    Docstring updated 9/24/2022

    Calculates the average CHP electrical and thermal efficiencies using part-load
    efficiency data.

    Used in calc_annual_fuel_use_and_costs function

    Parameters
    ---------
    ab: AuxBoiler Class
        contains initialized class data using CLI inputs (see command_line.py)
    chp: CHP Class
        contains initialized class data using CLI inputs (see command_line.py)
    demand: EnergyDemand Class
        contains initialized class data using CLI inputs (see command_line.py)
    load_following_type: string
        specifies whether calculation is for electrical load following (ELF) state
        or thermal load following (TLF) state.

    Returns
    -------
    avg_el_eff: Quantity (dimensionless)
        Average electrical efficiency of the CHP system based on linear fit approximation.
    avg_th_eff: Quantity (dimensionless)
        Average thermal efficiency of CHP system based on second order polynomial fit
        approximation.
    """
    if any(elem is None for elem in [chp, demand, ab, load_following_type]) is False:
        chp_size = sizing.size_chp(load_following_type=load_following_type, demand=demand, ab=ab)
        if chp_size == 0:
            avg_el_eff = Q_(0, '')
            avg_th_eff = Q_(0, '')
            return avg_el_eff, avg_th_eff
        if demand.net_metering_status is True:
            fuel_use_kw = sizing.electrical_output_to_fuel_consumption(electrical_output=chp_size)
            thermal_output_kw = sizing.electrical_output_to_thermal_output(electrical_output=chp_size)
            avg_el_eff = (chp_size / fuel_use_kw).to('')
            avg_th_eff = (thermal_output_kw / fuel_use_kw).to('')
            return avg_el_eff, avg_th_eff
        elif load_following_type is "ELF" and demand.net_metering_status is False:
            chp_electric_gen_hourly_kwh = elf_calc_electricity_bought_and_generated(chp=chp, demand=demand, ab=ab)[1]
        elif load_following_type is "TLF" and demand.net_metering_status is False:
            chp_electric_gen_hourly_kwh = tlf_calc_electricity_bought_and_generated(chp=chp, demand=demand, ab=ab)[1]
        else:
            raise Exception("Error in calc_hourly_efficiency function")

        hours_per_year = Q_(0, ureg.hours)
        for gen in chp_electric_gen_hourly_kwh:
            if gen.magnitude > 0:
                hours_per_year += Q_(1, ureg.hours)
        assert hours_per_year.magnitude > 0

        avg_gen_kw = (sum(chp_electric_gen_hourly_kwh) / hours_per_year).to(ureg.kW)
        fuel_use_kw = sizing.electrical_output_to_fuel_consumption(electrical_output=avg_gen_kw)
        thermal_output_kw = sizing.electrical_output_to_thermal_output(electrical_output=avg_gen_kw)

        avg_el_eff = (avg_gen_kw/fuel_use_kw).to('')
        avg_th_eff = (thermal_output_kw/fuel_use_kw).to('')

        return avg_el_eff, avg_th_eff


def calc_annual_fuel_use_and_costs(chp=None, demand=None, load_following_type=None, ab=None):
    """
    Docstring updated 9/24/2022

    Uses average electrical efficiency and average CHP electricity generation to calculate
    annual fuel use and annual fuel costs.

    Used in the command_line.py module

    Parameters
    ---------
    ab: AuxBoiler Class
        contains initialized class data using CLI inputs (see command_line.py)
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
    annual_fuel_cost: Quantity (float)
        Annual fuel cost for the CHP unit in USD (dimensionless Quantity)
    """
    if any(elem is None for elem in [chp, demand, ab, load_following_type]) is False:
        chp_size = sizing.size_chp(load_following_type=load_following_type, demand=demand, ab=ab)
        avg_el_eff = calc_avg_efficiency(chp=chp, demand=demand, ab=ab, load_following_type=load_following_type)[0]

        if demand.net_metering_status is True:
            fuel_use_kw = sizing.electrical_output_to_fuel_consumption(electrical_output=chp_size)
            annual_fuel_use_btu = (fuel_use_kw * chp.available_hours).to(ureg.Btu)
            annual_fuel_use_mmbtu = annual_fuel_use_btu.to(ureg.megaBtu)
            annual_fuel_cost = annual_fuel_use_mmbtu * demand.fuel_cost
            return annual_fuel_use_btu, annual_fuel_cost
        elif load_following_type is "ELF" and demand.net_metering_status is False:
            chp_electric_gen_hourly_kwh = elf_calc_electricity_bought_and_generated(chp=chp, demand=demand, ab=ab)[1]
        elif load_following_type is "TLF" and demand.net_metering_status is False:
            chp_electric_gen_hourly_kwh = tlf_calc_electricity_bought_and_generated(chp=chp, demand=demand, ab=ab)[1]
        else:
            raise Exception("Error in calc_annual_fuel_use_and_costs function")

        # Calculate fuel use
        hours_per_year = len(chp_electric_gen_hourly_kwh) * ureg.hours
        avg_electric_gen_kw = (sum(chp_electric_gen_hourly_kwh) / hours_per_year).to(ureg.kW)
        annual_electric_gen_kwh = (avg_electric_gen_kw * chp.available_hours).to(ureg.kWh)
        if avg_el_eff.magnitude == 0:
            annual_fuel_use_kwh = Q_(0, ureg.kWh)
        else:
            annual_fuel_use_kwh = annual_electric_gen_kwh / avg_el_eff
        annual_fuel_use_btu = annual_fuel_use_kwh.to(ureg.Btu)

        # Calculate fuel cost
        annual_fuel_use_mmbtu = annual_fuel_use_btu.to(ureg.megaBtu)
        annual_fuel_cost = annual_fuel_use_mmbtu * demand.fuel_cost

        return annual_fuel_use_btu, annual_fuel_cost


def calc_annual_electric_cost(chp=None, demand=None, load_following_type=None, ab=None):
    """
    Docstring updated 9/24/2022

    Calculates the annual cost of electricity bought from the local utility.

    Used in the command_line.py module

    Parameters
    ---------
    ab: AuxBoiler Class
        contains initialized class data using CLI inputs (see command_line.py)
    chp: CHP Class
        contains initialized class data using CLI inputs (see command_line.py)
    demand: EnergyDemand Class
        contains initialized class data using CLI inputs (see command_line.py)
    load_following_type: string
        specifies whether calculation is for electrical load following (ELF) state
        or thermal load following (TLF) state.

    Returns
    -------
    annual_cost: Quantity (float)
        The total annual cost of electricity bought from the local utility in USD
        (dimensionless Quantity)
    """
    if any(elem is None for elem in [chp, demand, ab, load_following_type]) is False:
        chp_size = sizing.size_chp(load_following_type=load_following_type, demand=demand, ab=ab)
        if demand.net_metering_status is True:
            annual_cost = (chp_size * chp.available_hours * demand.el_cost).to('')
            return annual_cost
        elif load_following_type is "ELF" and demand.net_metering_status is False:
            total_bought_kwh = sum(elf_calc_electricity_bought_and_generated(chp=chp, demand=demand, ab=ab)[0])
        elif load_following_type is "TLF" and demand.net_metering_status is False:
            total_bought_kwh = sum(tlf_calc_electricity_bought_and_generated(chp=chp, demand=demand, ab=ab)[0])
        else:
            raise Exception("Error in chp.py function, calc_annual_electric_cost")
        annual_cost = (total_bought_kwh * demand.el_cost).to('')
        assert annual_cost.units == ''

        return annual_cost


"""
ELF Functions
"""


def elf_calc_electricity_bought_and_generated(chp=None, demand=None, ab=None):
    """
    Updated 9/29/2022

    Calculates the electricity generated by the chp system and the electricity bought
    from the local utility to make up the difference.

    This function compares max and min CHP capacity with the hourly electrical
    demand of the building. If demand is above the max or below the min, it calculates
    how much electricity needs to be purchased from the utility for that hour. Also
    calculates electricity generated by the CHP unit each hour.

    Used in the elf_calc_hourly_heat_generated, calc_avg_efficiency,
    calc_annual_fuel_use_and_costs, and calc_annual_electric_cost functions

    Parameters
    ---------
    ab: AuxBoiler Class
        contains initialized class data using CLI inputs (see command_line.py)
    chp: CHP Class
        contains initialized class data using CLI inputs (see command_line.py)
    demand: EnergyDemand Class
        contains initialized class data using CLI inputs (see command_line.py)

    Returns
    -------
    utility_bought_kwh_list: list
        contains Quantity float values for electricity purchased hourly in units of kWh
    chp_gen_kwh_list: list
        contains Quantity float values for electricity generated hourly in units of kWh
    """
    if any(elem is None for elem in [chp, demand, ab]) is False:
        utility_bought_kwh_list = []
        chp_gen_kwh_list = []

        chp_size = sizing.size_chp(load_following_type='ELF', demand=demand, ab=ab)
        chp_min_output = (chp.min_pl * chp_size).to(ureg.kW)

        for d in demand.el:
            # Verifies acceptable input value range
            assert d.magnitude >= 0

            if chp_min_output <= d <= chp_size:
                bought = 0 * ureg.kWh
                gen = (d * ureg.hour).to(ureg.kWh)
                utility_bought_kwh_list.append(bought)
                chp_gen_kwh_list.append(gen)
            elif d < chp_min_output:
                bought = (d * ureg.hour).to(ureg.kWh)
                gen = 0 * ureg.kWh
                utility_bought_kwh_list.append(bought)
                chp_gen_kwh_list.append(gen)
            elif chp_size < d:
                bought = (d * ureg.hour).to(ureg.kWh) - (chp_size * ureg.hour).to(ureg.kWh)
                gen = (chp_size * ureg.hour).to(ureg.kWh)
                assert bought.units == ureg.kWh
                utility_bought_kwh_list.append(bought)
                chp_gen_kwh_list.append(gen)
            else:
                raise Exception("Error in ELF calc_utility_electricity_needed function")

        return utility_bought_kwh_list, chp_gen_kwh_list


def elf_calc_hourly_heat_generated(chp=None, demand=None, ab=None):
    """
    Updated 9/28/2022

    Uses the hourly electricity generated by CHP to calculate the
    hourly thermal output of the CHP unit. Assumes electrical load
    following (ELF) operation.

    Used in the thermal_storage module: calc_excess_and_deficit_heat function

    Parameters
    ---------
    ab: AuxBoiler Class
        contains initialized class data using CLI inputs (see command_line.py)
    chp: CHP Class
        contains initialized class data using CLI inputs (see command_line.py)
    demand: EnergyDemand Class
        contains initialized class data using CLI inputs (see command_line.py)

    Returns
    -------
    hourly_heat_rate: list
        Contains Quantity float values for hourly thermal output of the CHP unit
        in units of Btu/hour
    """
    if any(elem is None for elem in [chp, demand, ab]) is False:
        electricity_generated = elf_calc_electricity_bought_and_generated(chp=chp, demand=demand, ab=ab)[1]
        hourly_heat_rate = []

        for i, el_gen in enumerate(electricity_generated):
            heat_kw = sizing.electrical_output_to_thermal_output(el_gen)
            heat = heat_kw.to(ureg.Btu / ureg.hour)
            hourly_heat_rate.append(heat)

        return hourly_heat_rate


"""
TLF Functions
"""


def tlf_calc_hourly_heat_generated(chp=None, demand=None, ab=None):
    """
    Updated 9/29/2022

    Calculates the hourly heat generated by the CHP system.

    This function compares the thermal demand of the building with the max and
    min heat that can be generated by the chp system. Unlike the ELF case, this
    function allows generation when demand is below chp minimum heat output with
    excess sent to heat storage (TES). Assumes the load following state is thermal
    load following (TLF).

    Used in the thermal_storage module: calc_excess_and_deficit_heat function

    Parameters
    ----------
    ab: AuxBoiler Class
        contains initialized class data using CLI inputs (see command_line.py)
    chp: CHP Class
        contains initialized class data using CLI inputs (see command_line.py)
    demand: EnergyDemand Class
        contains initialized class data using CLI inputs (see command_line.py)

    Returns
    -------
    chp_hourly_heat_rate_list: list
        contains Quantity float values for hourly heat generated by the CHP
        system in units of Btu/hour.
    """
    if any(elem is None for elem in [chp, demand, ab]) is False:
        chp_size = sizing.size_chp(load_following_type='TLF', demand=demand, ab=ab)     # TODO: Size is zero (expected)
        chp_min_output = (chp.min_pl * chp_size).to(ureg.kW)

        chp_hourly_heat_rate_list = []
        chp_heat_rate_min = (sizing.electrical_output_to_thermal_output(chp_min_output)).to(ureg.Btu / ureg.hour)
        chp_heat_rate_cap = sizing.electrical_output_to_thermal_output(chp_size).to(ureg.Btu / ureg.hour)

        for i, dem in enumerate(demand.hl):
            # Verifies acceptable input value range
            assert dem.magnitude >= 0

            if chp_heat_rate_min <= dem <= chp_heat_rate_cap:
                chp_heat_rate_item = dem.to(ureg.Btu / ureg.hour)
                chp_hourly_heat_rate_list.append(chp_heat_rate_item)
            elif dem < chp_heat_rate_min:
                gen = 0 * (ureg.Btu / ureg.hour)
                chp_hourly_heat_rate_list.append(gen)
            elif chp_heat_rate_cap < dem:
                gen = chp_heat_rate_cap.to(ureg.Btu / ureg.hour)
                chp_hourly_heat_rate_list.append(gen)
            else:
                raise Exception("Error in TLF calc_utility_electricity_needed function")

        return chp_hourly_heat_rate_list


def tlf_calc_electricity_bought_and_generated(chp=None, demand=None, ab=None):
    """
    Updated 9/29/2022

    Calculates the electricity generated by the CHP system and the electricity bought
    from the local utility to make up the difference.

    For hourly heat generated by CHP, this function calculates the associated electrical
    output and compares this with the hourly electrical demand for the building. If
    demand is above the generated electricity (TODO: why not compare with heat demand?),
    it calculates how much electricity needs to be purchased from the utility for that
    hour. Also calculates electricity generated by the CHP unit each hour.

    Used in the calc_avg_efficiency, calc_annual_fuel_use_and_costs, and
    calc_annual_electric_cost functions

    Parameters
    ----------
    ab: AuxBoiler Class
        contains initialized class data using CLI inputs (see command_line.py)
    chp: CHP Class
        contains initialized class data using CLI inputs (see command_line.py)
    demand: EnergyDemand Class
        contains initialized class data using CLI inputs (see command_line.py)

    Returns
    -------
    hourly_electricity_bought: list
        contains Quantity float values for electricity bought each hour in units of kWh
    hourly_electricity_gen: list
        contains Quantity float values for CHP electricity generated each hour in
        units of kWh
    """
    if any(elem is None for elem in [chp, demand, ab]) is False:
        heat_generated_btu_hr = tlf_calc_hourly_heat_generated(chp=chp, demand=demand, ab=ab)

        hourly_electricity_gen = []
        hourly_electricity_bought = []

        electric_demand = demand.el

        for i, hourly_heat_rate in enumerate(heat_generated_btu_hr):
            heat_gen_kw = hourly_heat_rate.to(ureg.kW)
            electric_gen_kwh = (sizing.thermal_output_to_electrical_output(heat_gen_kw) * Q_(1, ureg.hour)).to(ureg.kWh)
            hourly_electricity_gen.append(electric_gen_kwh)
            electric_demand_item_kwh = (electric_demand[i] * Q_(1, ureg.hour)).to(ureg.kWh)
            if electric_demand_item_kwh >= electric_gen_kwh:
                bought = electric_demand_item_kwh - electric_gen_kwh
                hourly_electricity_bought.append(bought)
            else:
                bought = Q_(0, ureg.kWh)
                hourly_electricity_bought.append(bought)
        return hourly_electricity_bought, hourly_electricity_gen
