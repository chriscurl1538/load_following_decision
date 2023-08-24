"""
Description: Where energy costs are calculated
"""

from lfd_package.modules.__init__ import ureg, Q_


# TODO: De-couple apartment energy charges from office and corridor charges. Modify payback period calc accordingly.
def calc_electric_charges(class_dict=None, electricity_bought_hourly=None, office_only=False, apt_only=False):
    """
    Calculates electricity charges based on the utility rate schedule for the given location.

    Parameters
    ----------
    apt_only: bool
        Determines whether charges assessed are for tenant loads only
    office_only: bool
        Determines whether charges assessed are for non-tenant loads only
    class_dict: dict
        contains initialized class data using CLI inputs (see command_line.py)
    electricity_bought_hourly: list
        contains hourly electricity bought from utility in units of kWh.

    Returns
    -------
    total: Quantity
        contains the total electricity charges for the year. Units are dimensionless.
    """
    if office_only is True or apt_only is True:
        assert office_only != apt_only

    # Adjust calculation depending on whether we are analyzing total building loads or non-tenant loads
    if office_only is True:
        pct = 1 / (class_dict["costs"].no_apts + 1)
    elif apt_only is True:
        pct = class_dict["costs"].no_apts / (class_dict["costs"].no_apts + 1)
    else:
        pct = 1

    if sum(electricity_bought_hourly) == 0:
        return Q_(0, '')
    else:
        summer_weight, winter_weight = \
            class_dict['demand'].seasonal_weights_hourly_data(dem_profile=electricity_bought_hourly)
        summer_start = class_dict['demand'].summer_start_month
        winter_start = class_dict['demand'].winter_start_month

        monthly_energy_bought_list = class_dict['demand'].monthly_energy_sums(dem_profile=electricity_bought_hourly)
        min_energy_use_annual = min(monthly_energy_bought_list)
        annual_base_cost = []
        annual_rate_cost = []

        # Check metering type
        if class_dict['costs'].meter_type_el == "master_metered_el":
            el_cost_dict = class_dict['costs'].master_meter_el_dict
        elif class_dict['costs'].meter_type_el == "single_metered_el":
            el_cost_dict = class_dict['costs'].single_meter_el_dict
        else:
            raise Exception("Issue parsing electric metering type (master meter vs individually metered apartments)")

        # Loop through possible electric rate schedule types for the chosen meter type
        for item in class_dict['costs'].schedule_type_el:
            if class_dict['costs'].meter_type_el == "single_metered_el":
                building_base_cost = el_cost_dict[item]["monthly_base_charge"] * class_dict['costs'].no_apts
                annual_base_cost.append(Q_(12 * building_base_cost, ''))
            else:
                annual_base_cost.append(Q_(12 * el_cost_dict[item]["monthly_base_charge"], ''))
            units = el_cost_dict[item]["units"]

            if item == "schedule_basic":
                monthly_rate = Q_(el_cost_dict[item]["monthly_energy_charge"], '1/{}'.format(units))
                annual_electricity_bought = sum(monthly_energy_bought_list)
                annual_rate_cost = monthly_rate * annual_electricity_bought
                total_base_cost = sum(annual_base_cost)
                total = annual_rate_cost + total_base_cost
                total.ito('')
                return total * pct

            elif item == "schedule_energy_block":
                block1_cap = Q_(el_cost_dict[item]["energy_block1_cap"], str(units))
                rate_b1 = Q_(el_cost_dict[item]["energy_charge_block1"], '1/{}'.format(units))
                rate_b2 = Q_(el_cost_dict[item]["energy_charge_block2"], '1/{}'.format(units))

                if min_energy_use_annual < block1_cap:
                    annual_b1_rate_cost = rate_b1 * sum(monthly_energy_bought_list)
                    annual_rate_cost.append(annual_b1_rate_cost)

                elif block1_cap <= min_energy_use_annual:
                    b1_cost = rate_b1 * block1_cap * 12
                    annual_base_cost.append(b1_cost)

                    monthly_energy_bought_b2 = [item - block1_cap for item in monthly_energy_bought_list]
                    annual_b2_rate_cost = rate_b2 * sum(monthly_energy_bought_b2)
                    annual_rate_cost.append(annual_b2_rate_cost)

            elif item == "schedule_seasonal_energy":
                rate_summer = Q_(el_cost_dict[item]["energy_charge_summer"], '1/{}'.format(units))
                rate_winter = Q_(el_cost_dict[item]["energy_charge_winter"], '1/{}'.format(units))
                effective_rate = (rate_winter * winter_weight) + (rate_summer * summer_weight)
                cost = effective_rate * sum(monthly_energy_bought_list)
                annual_rate_cost.append(cost.to(''))

            elif item == "schedule_seasonal_demand":
                rate_summer = Q_(el_cost_dict[item]["dem_charge_summer"], '1/{}'.format(units))
                rate_winter = Q_(el_cost_dict[item]["dem_charge_winter"], '1/{}'.format(units))
                monthly_dem_peaks = class_dict["demand"].monthly_demand_peaks(dem_profile=electricity_bought_hourly)
                for i, peak in enumerate(monthly_dem_peaks):
                    if summer_start <= i+1 < winter_start:
                        rate_cost_item = (rate_summer * peak).to_reduced_units()
                    else:
                        rate_cost_item = (rate_winter * peak).to_reduced_units()
                    annual_rate_cost.append(rate_cost_item)

            elif item == "schedule_seasonal_energy_block":
                base_cost, rate_cost = seasonal_block_rates(sch=item, units=units, el_cost_dict=el_cost_dict,
                                                            costs_class=class_dict['costs'],
                                                            electricity_bought_hourly=electricity_bought_hourly)
                annual_base_cost.append(base_cost)
                annual_rate_cost.append(rate_cost)

            elif item == "schedule_seasonal_demand_block":
                base_cost, rate_cost = seasonal_block_rates(sch=item, units=units, el_cost_dict=el_cost_dict,
                                                            costs_class=class_dict['costs'],
                                                            electricity_bought_hourly=electricity_bought_hourly)
                annual_base_cost.append(base_cost)
                annual_rate_cost.append(rate_cost)

        total = sum(annual_base_cost) + sum(annual_rate_cost)
        total.ito_reduced_units()
        return total * pct


def seasonal_block_rates(sch=None, units=None, el_cost_dict=None, costs_class=None, electricity_bought_hourly=None):
    """
    Calculates seasonal block rates for use in the calc_electricity_charges() function.

    Parameters
    ----------
    sch: str
        represents the rate schedule type, but must be from list of keys for the rate dictionary.
    units: str
        represents the units that the rate values are associated with (ie: "therm" for $/therm rate).
    el_cost_dict: dict
        contains the electricity rate schedule data for cost evaluation.
    costs_class: EnergyCosts class
        the initialized EnergyCosts class.
    electricity_bought_hourly: list
        contains the hourly electricity bought from the grid in units of kWh

    Returns
    -------
    total_base_cost: Quantity
        Dimensionless value representing annual electrical base costs (monthly base charge).
    total_rate_cost: Quantity
        Dimensionless value representing costs associated with rate schedule (excludes base charges).
    """
    summer_length = costs_class.winter_start_month - costs_class.summer_start_month

    annual_base_cost = []
    annual_rate_cost = []

    if electricity_bought_hourly[0].units == ureg.kWh:
        electricity_bought_hourly = \
            costs_class.convert_units(values_list=electricity_bought_hourly, units_to_str="kW")

    if sch == "schedule_seasonal_energy_block":
        block1_cap = Q_(el_cost_dict[sch]["energy_block1_cap"], '{}'.format(units))
        rate_summer_b1 = Q_(el_cost_dict[sch]["energy_charge_summer_block1"], '1/{}'.format(units))
        rate_winter_b1 = Q_(el_cost_dict[sch]["energy_charge_winter_block1"], '1/{}'.format(units))
        rate_summer_b2 = Q_(el_cost_dict[sch]["energy_charge_summer_block2"], '1/{}'.format(units))
        rate_winter_b2 = Q_(el_cost_dict[sch]["energy_charge_winter_block2"], '1/{}'.format(units))
        monthly_energy_or_peaks_list = costs_class.monthly_energy_sums(dem_profile=electricity_bought_hourly)
        monthly_min = min(monthly_energy_or_peaks_list)
    elif sch == "schedule_seasonal_demand_block":
        block1_cap = Q_(el_cost_dict[sch]["dem_block1_cap"], '{}'.format(units))
        rate_summer_b1 = Q_(el_cost_dict[sch]["dem_charge_summer_block1"], '1/{}'.format(units))
        rate_winter_b1 = Q_(el_cost_dict[sch]["dem_charge_winter_block1"], '1/{}'.format(units))
        rate_summer_b2 = Q_(el_cost_dict[sch]["dem_charge_summer_block2"], '1/{}'.format(units))
        rate_winter_b2 = Q_(el_cost_dict[sch]["dem_charge_winter_block2"], '1/{}'.format(units))
        monthly_energy_or_peaks_list = costs_class.monthly_demand_peaks(dem_profile=electricity_bought_hourly)
        monthly_min = min(monthly_energy_or_peaks_list)
    else:
        raise Exception("schedule must be either seasonal demand block or seasonal energy block")

    if block1_cap <= monthly_min:
        summer_b1_cost = rate_summer_b1 * block1_cap * summer_length
        winter_b1_cost = rate_winter_b1 * block1_cap * (Q_(12, '') - summer_length)
        b1_total = summer_b1_cost + winter_b1_cost
        annual_base_cost.append(b1_total)

        monthly_energy_bought_b2 = [item - block1_cap for item in monthly_energy_or_peaks_list]
        summer_weight_b2, winter_weight_b2 = \
            costs_class.seasonal_weights_monthly_data(monthly_data=monthly_energy_bought_b2)

        effective_rate_b2 = (rate_summer_b2 * summer_weight_b2) + (rate_winter_b2 * winter_weight_b2)
        annual_b2_rate_cost = effective_rate_b2 * sum(monthly_energy_bought_b2)
        annual_rate_cost.append(annual_b2_rate_cost)
        total_base_cost = sum(annual_base_cost)
        total_rate_cost = sum(annual_rate_cost)
        return total_base_cost, total_rate_cost
    else:
        monthly_cost = []
        for index, monthly_energy in enumerate(monthly_energy_or_peaks_list):
            if costs_class.summer_start_month <= int(index + 1) < costs_class.winter_start_month:
                if monthly_energy < block1_cap:
                    monthly_cost.append(monthly_energy * rate_summer_b1)
                else:
                    monthly_cost.append(monthly_energy * rate_summer_b2)
            else:
                if monthly_energy < block1_cap:
                    monthly_cost.append(monthly_energy * rate_winter_b1)
                else:
                    monthly_cost.append(monthly_energy * rate_winter_b2)
        annual_rate_cost.append(sum(monthly_cost))
        total_base_cost = sum(annual_base_cost)
        total_rate_cost = sum(annual_rate_cost)
        return total_base_cost, total_rate_cost


def calc_fuel_charges(class_dict=None, fuel_bought_hourly=None, office_only=False, apt_only=False):
    """
    Calculates the cost of natural gas using the rate schedule associated with the gas utility for the given location.

    Parameters
    ----------
    apt_only: bool
        Determines whether charges assessed are for tenant loads only
    office_only: bool
        Determines whether charges assessed are for non-tenant loads only
    class_dict: dict
        contains initialized class data using CLI inputs (see command_line.py)
    fuel_bought_hourly: list
        contains hourly fuel bought in units of Btu.

    Returns
    -------
    total: Quantity
        total annual cost of fuel in dimensionless units
    """
    monthly_energy_bought_list = class_dict['demand'].monthly_energy_sums(dem_profile=fuel_bought_hourly)
    min_energy_use_annual = min(monthly_energy_bought_list)
    annual_base_cost = []
    annual_rate_cost = []

    if office_only is True or apt_only is True:
        assert office_only != apt_only

    # Adjust calculation depending on whether we are analyzing total building loads or non-tenant loads
    if office_only is True:
        pct = 1 / (class_dict["costs"].no_apts + 1)
    elif apt_only is True:
        pct = class_dict["costs"].no_apts / (class_dict["costs"].no_apts + 1)
    else:
        pct = 1

    # Check metering type
    if class_dict['costs'].meter_type_fuel == "master_metered_fuel":
        fuel_cost_dict = class_dict['costs'].master_meter_fuel_dict
    elif class_dict['costs'].meter_type_fuel == "single_metered_fuel":
        fuel_cost_dict = class_dict['costs'].single_meter_fuel_dict
    else:
        raise Exception("Issue parsing fuel metering type (master meter vs individually metered apartments)")

    # Ensure units are consistent. We want units of power for hourly fuel bought.
    if fuel_bought_hourly[0].check('[energy]'):
        fuel_bought_hourly = class_dict['demand'].convert_units(values_list=fuel_bought_hourly,
                                                                units_to_str="kW")

    # Loop through possible ng rate schedule types for the chosen meter type
    for item in class_dict['costs'].schedule_type_fuel:
        # Add annual base costs to list
        if class_dict['costs'].meter_type_fuel == "single_metered_fuel":
            building_base_cost = fuel_cost_dict[item]["monthly_base_charge"] * class_dict['costs'].no_apts
            annual_base_cost.append(Q_(12 * building_base_cost, ''))
        else:
            annual_base_cost.append(Q_(12 * fuel_cost_dict[item]["monthly_base_charge"], ''))
        units = fuel_cost_dict[item]["units"]

        # Convert units if needed
        if fuel_bought_hourly[0].check('[power]'):
            fuel_bought_hourly = class_dict['demand'].convert_units(units_to_str=str(units),
                                                                    values_list=fuel_bought_hourly)
        elif str(fuel_bought_hourly[0].units) != str(units):
            for fuel in fuel_bought_hourly:
                fuel.to(str(units))

        if item == "schedule_basic":
            monthly_rate = Q_(fuel_cost_dict[item]["monthly_energy_charge"], '1/{}'.format(units))
            annual_rate_cost = monthly_rate * sum(fuel_bought_hourly)
            total = annual_rate_cost + sum(annual_base_cost)
            total.ito_reduced_units()
            return total

        elif item == "schedule_energy_block":
            block1_cap = Q_(fuel_cost_dict[item]["energy_block1_cap"], str(units))
            block2_cap = Q_(fuel_cost_dict[item]["energy_block2_cap"], str(units))
            rate_b1 = Q_(fuel_cost_dict[item]["energy_charge_block1"], '1/{}'.format(units))
            rate_b2 = Q_(fuel_cost_dict[item]["energy_charge_block2"], '1/{}'.format(units))
            rate_b3 = Q_(fuel_cost_dict[item]["energy_charge_block3"], '1/{}'.format(units))

            if min_energy_use_annual < block1_cap:
                annual_b1_rate_cost = (rate_b1 * sum(monthly_energy_bought_list)).to('')
                annual_rate_cost.append(annual_b1_rate_cost)

            elif block1_cap <= min_energy_use_annual < block2_cap:
                b1_cost = (rate_b1 * block1_cap * 12).to('')
                annual_base_cost.append(b1_cost)

                monthly_energy_bought_b2 = [item - block1_cap for item in monthly_energy_bought_list]
                annual_b2_rate_cost = rate_b2 * sum(monthly_energy_bought_b2)
                annual_rate_cost.append(annual_b2_rate_cost)

            elif block2_cap <= min_energy_use_annual:
                b1_cost = rate_b1 * block1_cap * 12
                b2_cost = rate_b2 * (block2_cap - block1_cap) * 12
                annual_base_cost.append(b1_cost + b2_cost)

                monthly_energy_bought_b3 = [item - block2_cap for item in monthly_energy_bought_list]
                annual_b3_rate_cost = rate_b3 * sum(monthly_energy_bought_b3)
                annual_rate_cost.append(annual_b3_rate_cost)

            total = sum(annual_base_cost) + sum(annual_rate_cost)
            total.ito_reduced_units()
            return total


def calc_pp_revenue(class_dict=None, electricity_sold_hourly=None):
    """
    Calculates the annual revenue from selling electricity to the grid. This function uses the same rate schedule
    as that used for buying electricity from the utility.

    Parameters
    ----------
    class_dict: dict
        contains initialized class data using CLI inputs (see command_line.py)
    electricity_sold_hourly: list
        contains electricity sold to the grid each hour. Units are in kWh.

    Returns
    -------
    rev: Quantity
        sum of annual revenue from selling electricity. Units are dimensionless.
    """
    rev = calc_electric_charges(class_dict=class_dict, electricity_bought_hourly=electricity_sold_hourly)
    return rev


def calc_installed_om_cost(class_dict=None, dispatch_hourly=None, size=None, class_str=None):
    """
    Calculates the installed cost (materials, installation, labor) for CHP or TES. Also calculates the operation
    and maintenance cost.

    Parameters
    ----------
    class_dict: dict
        contains initialized class data using CLI inputs (see command_line.py)
    dispatch_hourly: list
        contains the hourly heat or electricity dispatched by the TES or CHP system.
    size: Quantity
        the size of the CHP or TES system in kW or Btu.
    class_str: str
        a string value representing whether the data passed is for CHP or TES.

    Returns
    -------
    installed_cost: Quantity
        the total cost of the CHP or TES system installation.
    om_cost: Quantity
        the yearly operation and maintenance cost of the equipment.
    """
    class_info = class_dict[str(class_str)]
    om_cost_list = []

    if size.magnitude == 0:
        return Q_(0, ''), Q_(0, '')

    for rate in dispatch_hourly:
        if class_str == "tes":
            rate = rate * Q_(1, ureg.hours)
        cost_hourly = (abs(rate) * class_info.om_cost).to('')
        om_cost_list.append(cost_hourly)

    om_cost = sum(om_cost_list)
    installed_cost = (size * class_info.installed_cost).to('')
    return installed_cost, om_cost


def calc_costs(thermal_cost_new=None, electrical_cost_new=None, tes_size=None, pct_incentive=0, class_dict=None,
               thermal_cost_baseline=None, electrical_cost_baseline=None, load_following_type="ELF", chp_size=None,
               chp_gen_hourly_kwh=None, tes_heat_flow_list=None, electricity_sold_hourly=None):
    """
    Calculates the payback period of CHP and TES installation.

    Parameters
    ----------
    thermal_cost_new: Quantity
        Dimensionless quantity representing annual sum of natural gas cost for CHP + TES
    electrical_cost_new: Quantity
        Dimensionless quantity representing annual sum of electricity costs for CHP + TES
    tes_size: Quantity
        The size of the TES unit in units of Btu.
    pct_incentive: float
        The percent of the total installed cost of CHP + TES covered by incentives.
    thermal_cost_baseline: Quantity
        Dimensionless quantity representing the natural gas costs associated with the Baseline case (non-CHP).
    electrical_cost_baseline: Quantity
        Dimensionless quantity representing the electricity costs associated with the Baseline case (non-CHP).
    load_following_type: str
        String representing the operating mode of the CHP unit (ELF, TLF, PP, Peak).
    chp_size: Quantity
        The size of the CHP unit in units of kW.
    class_dict: dict
        contains initialized class data using CLI inputs (see command_line.py)
    chp_gen_hourly_kwh: list
        contains electricity generated hourly by CHP in units of kWh.
    tes_heat_flow_list: list
        Storage heat rate for each hour. Values are positive for heat added and
        negative for heat discharged.Units are Btu/hr
    electricity_sold_hourly: list
        contains excess electricity generated hourly by CHP and sold to grid.
        Units are in kWh.

    Returns
    -------
    cost_data_dict: dict
        This dictionary contains the equipment installed costs, O&M costs, buyback revenue, and payback period
        (with and without incentives). All units are dimensionless.
    """
    # Calculate Cost Savings
    thermal_cost_savings = thermal_cost_baseline - thermal_cost_new
    if load_following_type == "PP" or load_following_type == "Peak":
        revenue = calc_pp_revenue(class_dict=class_dict, electricity_sold_hourly=electricity_sold_hourly)
    else:
        revenue = Q_(0, '')
    electrical_cost_savings = electrical_cost_baseline - electrical_cost_new + revenue
    total_cost_savings = electrical_cost_savings + thermal_cost_savings

    # Implementation Cost (material cost + installation cost)
    installed_cost_chp, om_cost_chp = calc_installed_om_cost(class_dict=class_dict, size=chp_size,
                                                             class_str="chp",
                                                             dispatch_hourly=chp_gen_hourly_kwh)
    installed_cost_tes, om_cost_tes = calc_installed_om_cost(class_dict=class_dict, size=tes_size, class_str="tes",
                                                             dispatch_hourly=tes_heat_flow_list)
    incremental_cost = om_cost_chp + om_cost_tes
    total_installed_cost = installed_cost_chp + installed_cost_tes
    implementation_cost_incent = installed_cost_chp + installed_cost_tes - (pct_incentive * total_installed_cost)
    implementation_cost_norm = installed_cost_chp + installed_cost_tes

    # Simple Payback Period (implementation cost / annual cost savings)
    incentive_payback = implementation_cost_incent / (total_cost_savings - incremental_cost) * ureg.year
    simple_payback = implementation_cost_norm / (total_cost_savings - incremental_cost) * ureg.year

    cost_data_dict = {
        "chp_installed_cost": installed_cost_chp,
        "tes_installed_cost": installed_cost_tes,
        "chp_om_cost": om_cost_chp,
        "tes_om_cost": om_cost_tes,
        "pp_rev": revenue,
        "simple_payback": simple_payback,
        "incentive_payback": incentive_payback
    }

    return cost_data_dict
