"""
Module description:
    Calculate CO2e emissions for grid and CHP system. Compare the two.
"""

from lfd_package.modules.__init__ import ureg


def identify_subgrid_coefficients(class_dict=None):
    """
    Assumes city,state is one of 5 accepted locations

    Parameters
    ----------
    class_dict: dict
        contains initialized class data using CLI inputs (see command_line.py)

    Returns
    -------
    subgrid_coefficient_average: Quantity
        contains the desired subgrid emission intensity value to use in emission calculations for the given location.
    """
    if class_dict is not None:
        emissions_class = class_dict['emissions']

        dict_key = "{}, {}".format(emissions_class.city, emissions_class.state)
        subgrid_coefficient_average = emissions_class.avg_emissions[dict_key]
        return subgrid_coefficient_average


def calc_baseline_grid_emissions(class_dict=None):
    """
    Calc grid emissions for electrical demand pre-CHP retrofit

    Parameters
    ----------
    class_dict: dict
        contains initialized class data using CLI inputs (see command_line.py)

    Returns
    -------
    electric_emissions_annual_avg: Quantity
        the annual sum of electrical emissions for the Baseline case in units of lbs.
    """
    if class_dict is not None:
        emissions_class = class_dict['emissions']

        subgrid_coefficient_average = identify_subgrid_coefficients(class_dict=class_dict)
        electric_demand_annual = emissions_class.annual_sum_el
        assert electric_demand_annual.units == ureg.kWh

        electric_emissions_annual_avg = (electric_demand_annual * subgrid_coefficient_average).to('lbs')

        return electric_emissions_annual_avg


def calc_baseline_fuel_emissions(class_dict=None):
    """
    Calc NG emissions for heating demand pre-CHP retrofit

    Parameters
    ----------
    class_dict: dict
        contains initialized class data using CLI inputs (see command_line.py)

    Returns
    -------
    fuel_emissions_annual: Quantity
        the annual sum of fuel CO2 emissions for the Baseline case in units of lbs.
    """
    if class_dict is not None:
        emissions_class = class_dict['emissions']

        heating_demand_annual = emissions_class.annual_sum_hl
        assert heating_demand_annual.units == ureg.Btu

        fuel_emissions_annual = (heating_demand_annual * emissions_class.ng_co2).to('lbs')
        assert fuel_emissions_annual.units == ureg.lbs

        return fuel_emissions_annual


def calc_chp_emissions(electricity_bought_annual=None, chp_fuel_use_annual=None, ab_fuel_use_annual=None,
                       class_dict=None):
    """
    Calc CHP emissions using CHP efficiency data.
    Accounts for bought electricity as well.

    Parameters
    ----------
    class_dict: dict
        contains initialized class data using CLI inputs (see command_line.py)
    electricity_bought_annual: Quantity
        the annual sum of electricity bought in units of kWh.
    chp_fuel_use_annual: Quantity
        the annual sum of fuel used by the CHP unit in units of Btu.
    ab_fuel_use_annual: Quantity
        the annual sum of fuel used by the boiler in units of Btu.

    Returns
    -------
    total_emissions_avg: Quantity
        the sum of annual electrical and fuel CO2 emissions for the energy system (CHP+Boiler) in units of lbs.
    """
    args_list = [electricity_bought_annual, chp_fuel_use_annual, ab_fuel_use_annual, class_dict]
    if any(elem is None for elem in args_list) is False:

        subgrid_coefficient_avg = identify_subgrid_coefficients(class_dict=class_dict)

        chp_fuel_emissions = (class_dict['emissions'].ng_co2 * chp_fuel_use_annual).to('lbs')
        boiler_emissions = (class_dict['emissions'].ng_co2 * ab_fuel_use_annual).to('lbs')

        grid_emissions_avg = (subgrid_coefficient_avg * electricity_bought_annual).to('lbs')
        total_emissions_avg = grid_emissions_avg + chp_fuel_emissions + boiler_emissions

        return total_emissions_avg
