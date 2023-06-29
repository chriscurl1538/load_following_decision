"""
Description: Where energy costs are calculated
"""

from lfd_package.modules.__init__ import ureg, Q_

#####################################
# Baseline Cost Calculations
#####################################


def calc_electric_charges(class_dict=None, electricity_bought_hourly=None):
    if sum(electricity_bought_hourly) == 0:
        charges = []
        for index in range(0, len(class_dict['demand'].el)):
            charges.append(Q_(0, ''))
        return charges
    else:
        summer_weight, winter_weight = class_dict['demand'].seasonal_weights_hourly_data(dem_profile=electricity_bought_hourly)

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
            annual_base_cost.append(12 * el_cost_dict[item]["monthly_base_charge"])
            units = el_cost_dict[item]["units"]

            if item == "schedule_basic":
                monthly_rate = Q_(el_cost_dict[item]["monthly_energy_charge"], '1/{}'.format(units))
                annual_rate_cost = monthly_rate * sum(electricity_bought_hourly).to(str(units))
                return annual_rate_cost + sum(annual_base_cost)

            if item == "schedule_energy_block":
                block1_cap = Q_(el_cost_dict[item]["energy_block1_cap"], str(units))
                rate_b1 = Q_(el_cost_dict[item]["energy_charge_block1"], '1/{}'.format(units))
                rate_b2 = Q_(el_cost_dict[item]["energy_charge_block2"], '1/{}'.format(units))

                if block1_cap <= min_energy_use_annual:
                    b1_cost = rate_b1 * block1_cap * 12
                    annual_base_cost.append(b1_cost)

                    monthly_energy_bought_b2 = [item - block1_cap for item in monthly_energy_bought_list]
                    annual_b2_rate_cost = rate_b2 * sum(monthly_energy_bought_b2)
                    annual_rate_cost.append(annual_b2_rate_cost)
                    return sum(annual_base_cost), sum(annual_rate_cost)

            elif item == "schedule_seasonal_energy":
                rate_summer = Q_(el_cost_dict[item]["energy_charge_summer"], '1/{}'.format(units))
                rate_winter = Q_(el_cost_dict[item]["energy_charge_winter"], '1/{}'.format(units))
                effective_rate = (rate_winter * winter_weight) + (rate_summer * summer_weight)
                annual_rate_cost = effective_rate * sum(electricity_bought_hourly).to(str(units))
                return annual_rate_cost + sum(annual_base_cost)

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

        return sum(annual_base_cost) + sum(annual_rate_cost)


def seasonal_block_rates(sch=None, units=None, el_cost_dict=None, costs_class=None, electricity_bought_hourly=None):
    summer_length = costs_class.winter_start_month - costs_class.summer_start_month

    annual_base_cost = []
    annual_rate_cost = []

    if electricity_bought_hourly[0].units == ureg.kWh:
        electricity_bought_hourly = \
            costs_class.convert_electricity_units(values_list=electricity_bought_hourly, units_from=ureg.kWh, units_to=ureg.kW)

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
        return sum(annual_base_cost), sum(annual_rate_cost)
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
        return sum(annual_base_cost), sum(annual_rate_cost)


def calc_baseline_fuel_charges():   # TODO: Implement
    return None


def calc_pp_revenue(class_dict=None, electricity_sold_hourly=None):      # Assumes same rate as charged TODO: Update
    return calc_electric_charges(class_dict=class_dict, electricity_bought_hourly=electricity_sold_hourly)
