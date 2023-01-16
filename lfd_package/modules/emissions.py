"""
Module description:
    Calculate CO2e emissions for grid and CHP system. Compare the two.
"""

from lfd_package.modules.__init__ import ureg, Q_
from lfd_package.modules import chp as cogen, aux_boiler as boiler


def identify_subgrid(demand=None, state=None, city=None):
    """
    Assumes city,state is one of 5 accepted locations

    Returns
    -------

    """
    if state is None and city is None:
        state = input("Enter state location (use two-letter abbreviation): ")
        city = input("Enter city location: ")

    if city.lower() == 'seattle' and state.lower() == 'wa':
        subgrid = demand.nwpp_co2e
    elif city.lower() == 'helena' and state.lower() == 'mt':
        subgrid = demand.nwpp_co2e
    elif city.lower() == 'miami' and state.lower() == 'fl':
        subgrid = demand.frcc_co2e
    elif city.lower() == 'duluth' and state.lower() == 'mn':
        subgrid = demand.mrow_co2e
    elif city.lower() == 'pheonix' and state.lower() == 'az':
        subgrid = demand.aznm_co2e
    else:
        return Exception("City and State must be one of the 5 accepted locations")
    return subgrid


def calc_grid_emissions(demand=None, city=None, state=None):
    """
    Calc grid emissions for electrical demand pre-CHP retrofit

    Returns
    -------

    """
    subgrid = identify_subgrid(demand=demand, city=city, state=state)
    electric_demand_annual = demand.annual_el

    electric_emissions_annual = (electric_demand_annual * subgrid).to('lbs')
    assert electric_emissions_annual.units == ureg.lbs

    return electric_emissions_annual


def calc_fuel_emissions(demand=None):
    """
    Calc NG emissions for heating demand pre-CHP retrofit

    Returns
    -------

    """
    heating_demand_annual = demand.annual_hl

    fuel_emissions_annual = (heating_demand_annual * demand.ng_co2e).to('lbs')
    assert fuel_emissions_annual.units == ureg.lbs

    return fuel_emissions_annual


def calc_chp_emissions(chp=None, demand=None, load_following_type=None, ab=None, tes=None, city=None, state=None):
    """
    Calc CHP emissions using CHP efficiency data.
    Accounts for bought electricity as well.

    Returns
    -------

    """
    if any(elem is None for elem in [chp, demand, load_following_type, ab, tes, city, state]) is False:
        if load_following_type == "ELF":
            electricity_bought_annual = sum(cogen.elf_calc_electricity_bought_and_generated(chp=chp, demand=demand,
                                                                                        ab=ab)[0])
        elif load_following_type == "TLF":
            electricity_bought_annual = sum(cogen.tlf_calc_electricity_bought_and_generated(chp=chp, demand=demand,
                                                                                        ab=ab)[0])
        else:
            return Exception("Error in calc_chp_emissions function")

        # Emissions from electricity bought
        subgrid = identify_subgrid(demand=demand, city=city, state=state)
        grid_emissions = (subgrid * electricity_bought_annual).to('lbs')

        # Emissions from CHP
        chp_fuel_use_annual = cogen.calc_annual_fuel_use_and_costs(chp=chp, demand=demand,
                                                                   load_following_type=load_following_type, ab=ab)[0]
        chp_emissions = (demand.ng_co2e * chp_fuel_use_annual).to('lbs')

        # Emissions from boiler use
        ab_fuel_use_annual = boiler.calc_annual_fuel_use_and_cost(chp=chp, demand=demand, tes=tes,
                                                                  load_following_type=load_following_type, ab=ab)[0]
        boiler_emissions = (demand.ng_co2e * ab_fuel_use_annual).to('lbs')

        # Total
        co2e_emissions = grid_emissions + chp_emissions + boiler_emissions
        assert co2e_emissions.units == ureg.lbs

        return co2e_emissions


def compare_emissions(chp=None, demand=None, load_following_type=None, ab=None, tes=None, state=None, city=None):
    """
    Calculates increase/decrease in CO2e emissions compared to pre-CHP conditions.
    Emissions increase if output is negative, decrease if output is positive.

    Parameters
    ----------
    chp
    demand
    load_following_type
    ab
    tes
    city
    state

    Returns
    -------

    """
    if any(elem is None for elem in [chp, demand, load_following_type, ab, tes, city, state]) is False:
        pre_chp_fuel_emissions = calc_fuel_emissions(demand=demand)
        pre_chp_grid_emissions = calc_grid_emissions(demand=demand, state=state, city=city)
        pre_chp_total_emissions = pre_chp_fuel_emissions + pre_chp_grid_emissions

        chp_total_emissions = calc_chp_emissions(chp=chp, demand=demand, load_following_type=load_following_type, ab=ab,
                                                 tes=tes, city=city, state=state)

        difference = pre_chp_total_emissions - chp_total_emissions
        assert difference.units == ureg.lbs

        return difference
