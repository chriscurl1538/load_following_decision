"""
Module Description:
    Contains functions needed to calculate the heat generated and fuel used
    by the auxiliary boiler
"""

import chp as cogen
import thermal_storage as storage
from __init__ import ureg


def calc_aux_boiler_output(chp=None, demand=None, tes=None, ab=None):
    """
    Using CHP heat output and TES heat discharge, this function determines when the
    heat demand exceeds the heat produced by the electric load following CHP system. Heat
    demand not met by CHP and TES is then assigned to the aux boiler (added to boiler_heat list).
    Items in the list are then verified to be within boiler operating parameters.

    Parameters
    ---------
    chp: CHP Class
        contains initialized CHP class data using CLI inputs (see command_line.py)
    demand: EnergyDemand Class
        contains initialized EnergyDemand class data using CLI inputs (see command_line.py)
    tes: TES Class
        contains initialized TES class data using CLI inputs (see command_line.py)
    ab: AuxBoiler Class
        contains initialized AuxBoiler class data using CLI inputs (see command_line.py)

    Returns
    -------
    ab_heat_hourly: list
        Hourly heat output of the auxiliary boiler
    """
    if chp is not None and demand is not None and tes is not None and ab is not None:
        data_res = 1 * ureg.hour
        ab_cap_btu = ab.cap * data_res
        ab_min_btu = ab.min * data_res

        el_demand_hourly = demand.el
        heat_demand_hourly = demand.hl

        ab_heat_hourly = []

        # Pull chp heat and tes heat data
        chp_heat_hourly = cogen.calc_hourly_heat_generated(chp=chp, demand=demand)
        tes_status_hourly = storage.tes_heat_stored(chp=chp, demand=demand, tes=tes)

        # Generate list of tes hourly heat discharge
        tes_heat_hourly = []

        for index, status in enumerate(tes_status_hourly):
            assert status >= 0
            if index == 0:
                tes_heat = 0 * ureg.Btu
                tes_heat_hourly.append(tes_heat)
            elif status < tes_status_hourly[index - 1]:
                tes_heat = abs(tes_status_hourly[index - 1] - status)
                tes_heat_hourly.append(tes_heat)
            elif status >= tes_status_hourly[index - 1]:
                tes_heat = 0 * ureg.Btu
                tes_heat_hourly.append(tes_heat)
            else:
                raise Exception('Error in aux_boiler.py function calc_aux_boiler_output()')

        for i in range(heat_demand_hourly.shape[0]):
            # Verifies acceptable input value range
            assert el_demand_hourly[i] >= 0
            assert heat_demand_hourly[i] >= 0

            chp_heat = chp_heat_hourly[i]
            tes_heat = tes_heat_hourly[i]
            sum_heat = chp_heat + tes_heat

            if sum_heat > heat_demand_hourly[i]:
                raise Exception('chp heat output and tes heat output exceeds building heating demand. Check chp and tes'
                                ' heat output calculations for errors')
            elif sum_heat == heat_demand_hourly[i]:
                ab_heat = 0
                ab_heat_hourly.append(ab_heat)
            elif sum_heat < heat_demand_hourly[i]:
                ab_heat = abs(heat_demand_hourly[i] - sum_heat)
                ab_heat_hourly.append(ab_heat)
            else:
                raise Exception('Error in aux_boiler.py function calc_aux_boiler_output()')

        # Check that hourly heat demand is within aux boiler operating parameters
        for index, i in enumerate(ab_heat_hourly):
            if ab_min_btu < i < ab_cap_btu:
                pass
            elif 0 < i <= ab_min_btu:
                ab_heat_hourly[index] = ab_min_btu
            elif ab_cap_btu < i:
                ab_heat_hourly[index] = ab_cap_btu
                raise Exception('ALERT: Boiler size is insufficient to meet heating demand! Output is short by '
                                '{} at hour number ()'.format(abs(i - ab_cap_btu)), index)

        return ab_heat_hourly


def calc_annual_fuel_use(chp=None, demand=None, tes=None, ab=None):
    """
    Calculates the annual fuel use of the auxiliary boiler

    Parameters
    ----------
    chp: CHP Class
        contains initialized CHP class data using CLI inputs (see command_line.py)
    demand: EnergyDemand Class
        contains initialized EnergyDemand class data using CLI inputs (see command_line.py)
    tes: TES Class
        contains initialized TES class data using CLI inputs (see command_line.py)
    ab: AuxBoiler Class
        contains initialized AuxBoiler class data using CLI inputs (see command_line.py)

    Returns
    -------
    annual_fuel_use: float
        annual fuel use of the auxiliary boiler
    """
    annual_heat_output = sum(calc_aux_boiler_output(chp=chp, demand=demand, tes=tes, ab=ab))
    annual_fuel_use = annual_heat_output / ab.eff
    return annual_fuel_use


def calc_annual_fuel_cost(chp=None, demand=None, tes=None, ab=None):
    """
    Calculates the annual fuel cost using the annual fuel use of the boiler

    Parameters
    ----------
    chp: CHP Class
        contains initialized CHP class data using CLI inputs (see command_line.py)
    demand: EnergyDemand Class
        contains initialized EnergyDemand class data using CLI inputs (see command_line.py)
    tes: TES Class
        contains initialized TES class data using CLI inputs (see command_line.py)
    ab: AuxBoiler Class
        contains initialized AuxBoiler class data using CLI inputs (see command_line.py)

    Returns
    -------
    annual_fuel_cost: float
        annual fuel cost, calculated from the annual fuel use of the boiler
    """
    annual_fuel_use_btu = calc_annual_fuel_use(chp=chp, demand=demand, tes=tes, ab=ab)
    annual_fuel_use_mmbtu = annual_fuel_use_btu.to(ureg.megaBtu)
    annual_fuel_cost = demand.fuel_cost * annual_fuel_use_mmbtu
    return annual_fuel_cost
