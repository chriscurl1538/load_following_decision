"""
Module Description:
    This module performs a sensitivity analysis on the following Python variables:
    - Electricity costs
    - Fuel costs
    - Incentives
    - TES Size
"""

from sensitivity import SensitivityAnalyzer as sa
from lfd_package.modules.__init__ import ureg, Q_


def make_param_list(base=None, increm=None, variation=None):
    start_val = base - variation
    stop_val = base + variation + 1
    param_list = []
    for value in range(start_val, stop_val, increm):
        param_list.append(value)
    return param_list


def model_payback_calc(thermal_cost_baseline=None, thermal_cost_new=None, electrical_cost_baseline=None,
                       electrical_cost_new=None, load_following_type=None, chp_size=None, class_dict=None,
                       chp_gen_hourly_kwh_dict=None, tes_size=None, tes_heat_flow_list=None,
                       electricity_sold_hourly=None, incentives=None):
    # Initialization
    costs = class_dict["costs"]

    # Calculate Cost Savings
    thermal_cost_savings = thermal_cost_baseline - thermal_cost_new
    if load_following_type == "PP" or "Peak":
        revenue = costs.calc_pp_revenue(class_dict=class_dict, electricity_sold_hourly=electricity_sold_hourly)
        electrical_cost_savings = electrical_cost_baseline - electrical_cost_new + revenue
    else:
        electrical_cost_savings = electrical_cost_baseline - electrical_cost_new
    total_cost_savings = electrical_cost_savings + thermal_cost_savings

    # Implementation Cost (material cost + installation cost)
    installed_cost_chp = costs.calc_installed_cost(class_dict=class_dict, size=chp_size, class_str="chp",
                                                   dispatch_hourly=chp_gen_hourly_kwh_dict[str(load_following_type)])
    installed_cost_tes = costs.calc_installed_cost(class_dict=class_dict, size=tes_size, class_str="tes",
                                                   dispatch_hourly=tes_heat_flow_list)
    implementation_cost = installed_cost_chp + installed_cost_tes - incentives

    # Simple Payback Period (implementation cost / annual cost savings)
    simple_payback = (implementation_cost / total_cost_savings) * ureg.year
    return simple_payback


if __name__ == "__main__":
    test_list = make_param_list(base=20, increm=1, variation=4)
    test_model = model_payback_calc()

    base_value_dict = {
        "thermal_cost_baseline": Q_(1000, ''),
        "thermal_cost_new": Q_(900, ''),
        "electrical_cost_baseline": Q_(2000, ''),
        "electrical_cost_new": Q_(1500, ''),
        "chp_size": Q_(20, ureg.kW),
        "tes_size": Q_(500, ureg.Btu),
        "incentives": Q_(1000, '')
    }

    sa_electric_cost_list = make_param_list(base=base_value_dict["electrical_cost_new"], increm=100, variation=4)
    sa_thermal_cost_list = make_param_list(base=base_value_dict["thermal_cost_new"], increm=100, variation=4)
    sa_incentives_list = make_param_list(base=base_value_dict["incentives"], increm=100, variation=4)
    sa_tes_size_list = make_param_list(base=base_value_dict["tes_size"], increm=100, variation=4)

    sa_dict = {
        "electricity_cost_annual": sa_electric_cost_list,
        "thermal_cost_annual": sa_thermal_cost_list,
        "incentives": sa_incentives_list,
        "tes_size": sa_tes_size_list
    }

    sense = sa(sa_dict, model_payback_calc())
