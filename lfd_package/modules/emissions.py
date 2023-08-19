"""
Module description:
    Calculate CO2e emissions for grid and CHP system. Compare the two.
"""

from lfd_package.modules.__init__ import ureg
from lfd_package.modules import chp as cogen, aux_boiler as boiler


def identify_subgrid_coefficients(class_dict=None):
    """
    Assumes city,state is one of 5 accepted locations

    Returns
    -------

    """
    emissions_class = class_dict['emissions']

    dict_key = "{}, {}".format(emissions_class.city, emissions_class.state)
    subgrid_coefficient_average = emissions_class.avg_emissions[dict_key]
    return subgrid_coefficient_average


def calc_baseline_grid_emissions(class_dict=None):
    """
    Calc grid emissions for electrical demand pre-CHP retrofit

    Returns
    -------

    """
    emissions_class = class_dict['emissions']

    subgrid_coefficient_average = identify_subgrid_coefficients(class_dict=class_dict)
    electric_demand_annual = emissions_class.annual_sum_el
    assert electric_demand_annual.units == ureg.kWh

    electric_emissions_annual_avg = (electric_demand_annual * subgrid_coefficient_average).to('lbs')

    return electric_emissions_annual_avg


def calc_baseline_fuel_emissions(class_dict=None):
    """
    Calc NG emissions for heating demand pre-CHP retrofit

    Returns
    -------

    """
    emissions_class = class_dict['emissions']

    heating_demand_annual = emissions_class.annual_sum_hl
    assert heating_demand_annual.units == ureg.Btu

    fuel_emissions_annual = (heating_demand_annual * emissions_class.ng_co2).to('lbs')
    assert fuel_emissions_annual.units == ureg.lbs

    return fuel_emissions_annual


def calc_chp_emissions(chp_gen_hourly_kwh_dict=None, chp_gen_hourly_btuh=None, tes_size=None, chp_size=None,
                       ab_output_rate_list=None, load_following_type=None, class_dict=None):
    """
    Calc CHP emissions using CHP efficiency data.
    Accounts for bought electricity as well.

    Returns
    -------

    """
    args_list = [chp_gen_hourly_kwh_dict, chp_gen_hourly_btuh, tes_size, chp_size, load_following_type, class_dict]
    if any(elem is None for elem in args_list) is False:

        # Emissions from electricity bought
        # TODO: Optimize - remove functions called in CLI
        key = str(load_following_type)
        chp_gen_hourly_kwh = chp_gen_hourly_kwh_dict[key]
        electricity_bought_annual = sum(cogen.calc_electricity_bought(chp_gen_hourly_kwh=chp_gen_hourly_kwh,
                                                                      chp_size=chp_size, class_dict=class_dict))

        # For Emissions from CHP
        chp_fuel_use_annual = sum(cogen.calc_hourly_fuel_use(chp_gen_hourly_btuh=chp_gen_hourly_btuh, chp_size=chp_size,
                                                             class_dict=class_dict,
                                                             load_following_type=load_following_type))

        # For Emissions from boiler use
        ab_fuel_use_annual = sum(boiler.calc_hourly_fuel_use(class_dict=class_dict,
                                                             ab_output_rate_list=ab_output_rate_list))

        subgrid_coefficient_avg = identify_subgrid_coefficients(class_dict=class_dict)

        chp_fuel_emissions = (class_dict['emissions'].ng_co2 * chp_fuel_use_annual).to('lbs')
        boiler_emissions = (class_dict['emissions'].ng_co2 * ab_fuel_use_annual).to('lbs')

        grid_emissions_avg = (subgrid_coefficient_avg * electricity_bought_annual).to('lbs')
        total_emissions_avg = grid_emissions_avg + chp_fuel_emissions + boiler_emissions

        return total_emissions_avg


if __name__ == "__main__":
    print(dir(ureg.sys.mks))
