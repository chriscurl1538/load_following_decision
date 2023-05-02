"""
Module description:
    Calculate CO2e emissions for grid and CHP system. Compare the two.
"""

from lfd_package.modules.__init__ import ureg, Q_
from lfd_package.modules import chp as cogen, aux_boiler as boiler


def identify_subgrid_coefficients(demand=None):
    """
    Assumes city,state is one of 5 accepted locations

    Returns
    -------

    """
    city = demand.city
    state = demand.state

    if city.lower() == 'seattle' and state.lower() == 'wa':
        subgrid_coefficient_marginal = demand.nw_emissions_co2
        subgrid_coefficient_average = demand.nwpp_emissions_co2
    elif city.lower() == 'helena' and state.lower() == 'mt':
        subgrid_coefficient_marginal = demand.nw_emissions_co2
        subgrid_coefficient_average = demand.nwpp_emissions_co2
    elif city.lower() == 'miami' and state.lower() == 'fl':
        subgrid_coefficient_marginal = demand.fl_emissions_co2
        subgrid_coefficient_average = demand.frcc_emissions_co2
    elif city.lower() == 'duluth' and state.lower() == 'mn':
        subgrid_coefficient_marginal = demand.midwest_emissions_co2
        subgrid_coefficient_average = demand.mrow_emissions_co2
    elif city.lower() == 'pheonix' and state.lower() == 'az':
        subgrid_coefficient_marginal = demand.sw_emissions_co2
        subgrid_coefficient_average = demand.aznm_emissions_co2
    elif city.lower() == 'fairbanks' and state.lower() == 'ak':
        subgrid_coefficient_marginal = demand.akgd_emissions_co2    # TODO: Change to marginal
        subgrid_coefficient_average = demand.akgd_emissions_co2
    elif city.lower() == 'chicago' and state.lower() == 'il':
        subgrid_coefficient_marginal = demand.rfcw_emissions_co2    # TODO: Change to marginal
        subgrid_coefficient_average = demand.rfcw_emissions_co2
    else:
        raise Exception("City and State must be one of the 5 accepted locations")
    return subgrid_coefficient_marginal, subgrid_coefficient_average


def calc_baseline_grid_emissions(demand=None):
    """
    Calc grid emissions for electrical demand pre-CHP retrofit

    Returns
    -------

    """
    subgrid_coefficient_marginal, subgrid_coefficient_average = identify_subgrid_coefficients(demand=demand)
    electric_demand_annual = demand.annual_el
    assert electric_demand_annual.units == ureg.kWh

    electric_emissions_annual_marg = (electric_demand_annual * subgrid_coefficient_marginal).to('lbs')
    electric_emissions_annual_avg = (electric_demand_annual * subgrid_coefficient_average).to('lbs')

    return electric_emissions_annual_marg, electric_emissions_annual_avg


def calc_baseline_fuel_emissions(demand=None):
    """
    Calc NG emissions for heating demand pre-CHP retrofit

    Returns
    -------

    """
    heating_demand_annual = demand.annual_hl
    assert heating_demand_annual.units == ureg.Btu

    fuel_emissions_annual = (heating_demand_annual * demand.ng_co2).to('lbs')
    assert fuel_emissions_annual.units == ureg.lbs

    return fuel_emissions_annual


def calc_chp_emissions(chp=None, demand=None, load_following_type=None, ab=None, tes=None):
    """
    Calc CHP emissions using CHP efficiency data.
    Accounts for bought electricity as well.

    Returns
    -------

    """
    if any(elem is None for elem in [chp, demand, load_following_type, ab, tes]) is False:

        # Emissions from electricity bought
        if load_following_type == "ELF":
            electricity_bought_annual = sum(cogen.elf_calc_electricity_bought_and_generated(chp=chp, demand=demand,
                                                                                            ab=ab)[0])
        elif load_following_type == "TLF":
            electricity_bought_annual = sum(cogen.tlf_calc_electricity_bought_and_generated(chp=chp, demand=demand,
                                                                                            ab=ab, tes=tes)[0])
        elif load_following_type == "PP":
            electricity_bought_annual = sum(cogen.pp_calc_electricity_bought_and_generated(chp=chp, demand=demand,
                                                                                           ab=ab)[0])
        else:
            raise Exception("Error in calc_chp_emissions function")

        # For Emissions from CHP
        chp_fuel_use_annual = cogen.calc_annual_fuel_use_and_costs(chp=chp, demand=demand, tes=tes,
                                                                   load_following_type=load_following_type, ab=ab)[0]

        # For Emissions from boiler use
        ab_fuel_use_annual = boiler.calc_annual_fuel_use_and_cost(chp=chp, demand=demand, tes=tes,
                                                                  load_following_type=load_following_type, ab=ab)[0]

        subgrid_coefficient_marg, subgrid_coefficient_avg = identify_subgrid_coefficients(demand=demand)

        grid_emissions_marg = (subgrid_coefficient_marg * electricity_bought_annual).to('lbs')   # TODO: Incorrect calc
        chp_fuel_emissions = (demand.ng_co2 * chp_fuel_use_annual).to('lbs')
        boiler_emissions = (demand.ng_co2 * ab_fuel_use_annual).to('lbs')
        total_emissions_marg = grid_emissions_marg + chp_fuel_emissions + boiler_emissions

        grid_emissions_avg = (subgrid_coefficient_avg * electricity_bought_annual).to('lbs')
        total_emissions_avg = grid_emissions_avg + chp_fuel_emissions + boiler_emissions

        return total_emissions_marg, total_emissions_avg


if __name__ == "__main__":
    print(dir(ureg.sys.mks))
