"""
Module Description:
    Contains functions needed to calculate the demand, electricity cost, and fuel use of
    the micro-chp unit for both electrical load following (ELF) and thermal load following
    (TLF) cases. Also accounts for whether net metering is permitted by the local utility.
TODO: Add function that calculated the percent annual runtime of the CHP unit
"""

from lfd_package.modules import sizing_calcs as sizing
from lfd_package.modules.__init__ import ureg, Q_


def calc_annual_fuel_use_and_costs(chp_gen_hourly_btuh=None, chp_size=None, chp=None, demand=None, load_following_type=None, ab=None):
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
        # Get hourly CHP gen in kWh
        # TODO: Optimize - remove functions called in CLI
        if load_following_type == "PP":
            chp_electric_gen_hourly_kwh = pp_calc_electricity_bought_and_generated(chp_size=chp_size, chp=chp,
                                                                                   demand=demand, ab=ab)[1]
        elif load_following_type == "ELF":
            chp_electric_gen_hourly_kwh = elf_calc_electricity_bought_and_generated(chp_size=chp_size, chp=chp,
                                                                                    demand=demand, ab=ab)[1]
        elif load_following_type == "TLF":
            chp_electric_gen_hourly_kwh = tlf_calc_electricity_bought_and_generated(chp_gen_hourly_btuh=chp_gen_hourly_btuh,
                                                                                    chp=chp, demand=demand, ab=ab)[1]
        else:
            raise Exception("Error in calc_annual_fuel_use_and_costs function")

        fuel_use_btu_list = []

        # Calculate fuel use
        for index, el in enumerate(chp_electric_gen_hourly_kwh):
            chp_hourly_electric_kw = (el / Q_(1, ureg.hours)).to(ureg.kW)
            fuel_use_hourly_kw = sizing.electrical_output_to_fuel_consumption(chp_hourly_electric_kw)
            fuel_use_hourly_btu = (fuel_use_hourly_kw * Q_(1, ureg.hours)).to(ureg.Btu)
            fuel_use_btu_list.append(fuel_use_hourly_btu)

        annual_fuel_use_btu = sum(fuel_use_btu_list)

        # Calculate fuel cost
        annual_fuel_use_mmbtu = annual_fuel_use_btu.to(ureg.megaBtu)
        annual_fuel_cost = annual_fuel_use_mmbtu * demand.fuel_cost

        return annual_fuel_use_btu, annual_fuel_cost


def calc_annual_electric_cost(chp_gen_hourly_kwh_dict=None, chp=None, demand=None, load_following_type=None, ab=None):
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
        annual_cost = (sum(chp_gen_hourly_kwh_dict[load_following_type]) * demand.el_cost).to('')
        assert annual_cost.units == ''
        return annual_cost


"""
Power Purchase (PP) Functions
"""


def pp_calc_electricity_bought_and_generated(chp_size=None, chp=None, demand=None, ab=None):
    if any(elem is None for elem in [chp, demand, ab]) is False:
        utility_bought_kwh_list = []
        utility_sold_kwh_list = []
        chp_gen_kwh_list = []

        chp_hourly_kwh = (chp_size * Q_(1, ureg.hours)).to(ureg.kWh)

        for dem in demand.el:     # Units of Joule/hour
            # Verifies acceptable input value range
            assert dem.magnitude >= 0
            d = (dem * Q_(1, ureg.hours)).to(ureg.kWh)

            if d <= chp_hourly_kwh:
                bought = Q_(0, ureg.kWh)
                sold = (chp_hourly_kwh - d).to(ureg.kWh)
                utility_bought_kwh_list.append(bought)
                chp_gen_kwh_list.append(chp_hourly_kwh)
                utility_sold_kwh_list.append(sold)
            elif chp_hourly_kwh < d:
                bought = (d - chp_hourly_kwh).to(ureg.kWh)
                sold = Q_(0, ureg.kWh)
                utility_bought_kwh_list.append(bought)
                chp_gen_kwh_list.append(chp_hourly_kwh)
                utility_sold_kwh_list.append(sold)
            else:
                raise Exception("Error in PP calc_utility_electricity_needed function")

        assert utility_bought_kwh_list[100].units == ureg.kWh
        assert chp_gen_kwh_list[100].units == ureg.kWh
        assert utility_sold_kwh_list[100].units == ureg.kWh

        return utility_bought_kwh_list, chp_gen_kwh_list, utility_sold_kwh_list


def pp_calc_hourly_heat_generated(chp_gen_hourly_kwh=None, chp=None, demand=None, ab=None):
    if any(elem is None for elem in [chp, demand, ab]) is False:
        hourly_heat_rate = []

        for i, el_gen_kwh in enumerate(chp_gen_hourly_kwh):
            el_gen = (el_gen_kwh / Q_(1, ureg.hours)).to(ureg.kW)
            heat_kw = sizing.electrical_output_to_thermal_output(el_gen)
            heat = heat_kw.to(ureg.Btu / ureg.hour)
            hourly_heat_rate.append(heat)

        return hourly_heat_rate


"""
ELF Functions
"""


def elf_calc_electricity_bought_and_generated(chp_size=None, chp=None, demand=None, ab=None):
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

        chp_min_output = (chp.min_pl * chp_size).to(ureg.kW)

        for d in demand.el:
            # Verifies acceptable input value range
            assert d.magnitude >= 0
            d.to(ureg.kW)

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


def elf_calc_hourly_heat_generated(chp_gen_hourly_kwh=None, chp=None, demand=None, ab=None):
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
        hourly_heat_rate = []

        for i, el_gen_kwh in enumerate(chp_gen_hourly_kwh):
            el_gen = (el_gen_kwh / Q_(1, ureg.hours)).to(ureg.kW)
            heat_kw = sizing.electrical_output_to_thermal_output(el_gen)
            heat = heat_kw.to(ureg.Btu / ureg.hour)
            hourly_heat_rate.append(heat)

        return hourly_heat_rate


"""
TLF Functions
"""


def tlf_calc_hourly_heat_generated(chp_size=None, chp=None, demand=None, ab=None, tes=None):
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
        chp_min_output = (chp.min_pl * chp_size).to(ureg.kW)

        chp_hourly_heat_rate_list = []
        chp_heat_rate_min = (sizing.electrical_output_to_thermal_output(chp_min_output)).to(ureg.Btu / ureg.hour)
        chp_heat_rate_cap = sizing.electrical_output_to_thermal_output(chp_size).to(ureg.Btu / ureg.hour)

        # TES sizing does not require electrical demand argument if operation mode is TLF
        tes_size = sizing.size_tes(chp_size=chp_size, demand=demand, chp=chp, ab=ab, load_following_type="TLF")

        tes_heat_rate_list_btu_hour = []
        soc_list = []

        for i, dem in enumerate(demand.hl):
            # Verifies acceptable input value range
            assert dem.magnitude >= 0
            if i == 0:
                current_status = tes.start * tes_size

            if chp_heat_rate_min <= dem <= chp_heat_rate_cap and tes_size == current_status:
                # If TES is full and chp meets demand, follow thermal load
                gen = dem.to(ureg.Btu / ureg.hour)
                chp_hourly_heat_rate_list.append(gen)
                stored_heat = Q_(0, ureg.Btu / ureg.hour)
                tes_heat_rate_list_btu_hour.append(stored_heat)
                new_status = (stored_heat * Q_(1, ureg.hour)) + current_status
                soc_list.append(new_status / tes_size)
                current_status = new_status
            elif chp_heat_rate_min <= dem <= chp_heat_rate_cap and current_status < tes_size:
                # If TES needs heat and chp meets demand, run CHP at full power and put excess in TES
                gen = chp_heat_rate_cap
                chp_hourly_heat_rate_list.append(gen)
                # Make sure SOC does not exceed 1 when heat is added
                soc_check = ((current_status / Q_(1, ureg.hours)) + gen - dem) / (tes_size / Q_(1, ureg.hours))
                if soc_check.magnitude < 1:
                    stored_heat = gen - dem
                    assert stored_heat >= 0
                else:
                    stored_heat = (tes_size - current_status) / Q_(1, ureg.hours)
                    assert stored_heat >= 0
                tes_heat_rate_list_btu_hour.append(stored_heat)
                new_status = (stored_heat * Q_(1, ureg.hours)) + current_status
                soc_list.append(new_status / tes_size)
                current_status = new_status
            elif dem < chp_heat_rate_min and dem <= (current_status / Q_(1, ureg.hours)):
                # If TES not empty, then let out heat to meet demand
                gen = Q_(0, ureg.Btu / ureg.hour)
                chp_hourly_heat_rate_list.append(gen)
                discharged_heat = gen - dem     # Should be negative
                assert discharged_heat <= 0
                tes_heat_rate_list_btu_hour.append(discharged_heat)
                new_status = (discharged_heat * Q_(1, ureg.hours)) + current_status
                soc_list.append(new_status / tes_size)
                current_status = new_status
            elif dem < chp_heat_rate_min and (current_status / Q_(1, ureg.hours)) < dem:
                # If TES is empty (or does not have enough to meet demand), then run CHP at full power
                gen = chp_heat_rate_cap
                chp_hourly_heat_rate_list.append(gen)

                soc_check = ((current_status / Q_(1, ureg.hours)) + gen - dem) / (tes_size / Q_(1, ureg.hours))
                if soc_check >= 1:
                    stored_heat = (tes_size - current_status) / Q_(1, ureg.hours)
                    assert stored_heat >= 0
                else:
                    stored_heat = gen - dem
                    assert stored_heat >= 0

                new_status = (stored_heat * Q_(1, ureg.hour)) + current_status
                tes_heat_rate_list_btu_hour.append(stored_heat)
                soc_list.append(new_status / tes_size)
                current_status = new_status
            elif chp_heat_rate_cap < dem and dem < (current_status / Q_(1, ureg.hours)):
                # If demand exceeds CHP generation, use TES
                gen = chp_heat_rate_cap
                chp_hourly_heat_rate_list.append(gen)

                soc_check = ((current_status / Q_(1, ureg.hours)) + gen - dem) / (tes_size / Q_(1, ureg.hours))
                if soc_check <= 0:
                    discharged_heat = -1 * current_status / Q_(1, ureg.hours)
                    assert discharged_heat <= 0
                else:
                    discharged_heat = gen - dem     # Should be negative
                    assert discharged_heat <= 0

                tes_heat_rate_list_btu_hour.append(discharged_heat)
                new_status = (discharged_heat * Q_(1, ureg.hour)) + current_status
                soc_list.append(new_status / tes_size)
                current_status = new_status
            elif chp_heat_rate_cap < dem and (current_status / Q_(1, ureg.hours)) < dem:
                # Discharge everything from TES
                gen = chp_heat_rate_cap
                chp_hourly_heat_rate_list.append(gen)
                discharged_heat = -1 * current_status / Q_(1, ureg.hours)  # Should be negative
                assert discharged_heat <= 0
                tes_heat_rate_list_btu_hour.append(discharged_heat)
                new_status = (discharged_heat * Q_(1, ureg.hours)) + current_status
                soc_list.append(new_status / tes_size)
                current_status = new_status
            else:
                raise Exception("Error in TLF calc_utility_electricity_needed function")

        return chp_hourly_heat_rate_list, tes_heat_rate_list_btu_hour, soc_list


def tlf_calc_electricity_bought_and_generated(chp_gen_hourly_btuh=None, chp=None, demand=None, ab=None):
    """
    Updated 9/29/2022

    Calculates the electricity generated by the CHP system and the electricity bought
    from the local utility to make up the difference.

    For hourly heat generated by CHP, this function calculates the associated electrical
    output and compares this with the hourly electrical demand for the building. If
    demand is above the generated electricity,
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
        hourly_electricity_gen = []
        hourly_electricity_bought = []

        electric_demand = demand.el

        for i, hourly_heat_rate in enumerate(chp_gen_hourly_btuh):
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
