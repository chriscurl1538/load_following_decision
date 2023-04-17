"""
Module Description:
    Contains functions needed to calculate the heat generated and fuel used
    by the auxiliary boiler
"""

import math

from lfd_package.modules import chp as cogen
from lfd_package.modules import thermal_storage as storage
from lfd_package.modules.__init__ import ureg, Q_


# TODO: Aux boiler output is far too high (see plots)
def calc_aux_boiler_output_rate(chp_size=None, chp=None, demand=None, tes=None, ab=None, load_following_type=None):
    """
    Updated 10/16/2022

    Using CHP heat output and TES heat discharge, this function determines when the
    heat demand exceeds the heat produced by the electric load following CHP system. Heat
    demand not met by CHP and TES is then assigned to the aux boiler (added to ab_heat_hourly list).
    Items in the list are then verified to be within boiler operating parameters.

    Parameters
    ---------
    chp: CHP Class
        contains initialized class data using CLI inputs (see command_line.py)
    demand: EnergyDemand Class
        contains initialized class data using CLI inputs (see command_line.py)
    tes: TES Class
        contains initialized class data using CLI inputs (see command_line.py)
    ab: AuxBoiler Class
        contains initialized class data using CLI inputs (see command_line.py)
    load_following_type: string
        specifies whether calculation is for electrical load following (ELF) state
        or thermal load following (TLF) state.

    Returns
    -------
    ab_heat_rate_hourly: list (Quantity)
        Hourly heat output of the auxiliary boiler in units of Btu/hr
    """
    if chp is not None and demand is not None and tes is not None and ab is not None:
        # Pull chp heat and tes heat data

        if load_following_type is "ELF":
            chp_heat_hourly = cogen.elf_calc_hourly_heat_generated(chp=chp, demand=demand, ab=ab)
            tes_heat_rate_list = storage.calc_tes_heat_flow_and_soc(chp_size=chp_size, chp=chp, demand=demand, tes=tes,
                                                                    ab=ab, load_following_type=load_following_type)[0]
        elif load_following_type is "TLF":
            chp_heat_hourly = cogen.tlf_calc_hourly_heat_generated(chp=chp, demand=demand, ab=ab, tes=tes)[0]
            tes_heat_rate_list = cogen.tlf_calc_hourly_heat_generated(chp=chp, demand=demand, ab=ab, tes=tes)[1]
        elif load_following_type is "PP":
            chp_heat_hourly = cogen.pp_calc_hourly_heat_generated(chp=chp, demand=demand, ab=ab)
            tes_heat_rate_list = storage.calc_tes_heat_flow_and_soc(chp_size=chp_size, chp=chp, demand=demand, tes=tes,
                                                                    ab=ab, load_following_type=load_following_type)[0]
        else:
            raise Exception("Error in chp.py function, calc_annual_electric_cost")

        ab_heat_rate_hourly = []
        tes_discharge = []
        chp_heat_rate_minus_excess = []

        # Remove waste heat production from CHP heat output data since TES captures excess
        for index, chp_heat_rate in enumerate(chp_heat_hourly):
            dem_item = demand.hl[index]
            if dem_item < chp_heat_rate:
                desired = dem_item
                chp_heat_rate_minus_excess.append(desired)
            else:
                desired = chp_heat_rate
                chp_heat_rate_minus_excess.append(desired)

        # Get TES discharge only
        for index, rate in enumerate(tes_heat_rate_list):
            if rate < 0:
                tes_discharge.append(rate)
            else:
                zero = Q_(0, ureg.Btu / ureg.hour)
                tes_discharge.append(zero)

        # Compare CHP and TES output with demand to determine AB output
        for index, dem in enumerate(demand.hl):
            dem_item = dem
            chp_heat_rate_item = chp_heat_rate_minus_excess[index]
            tes_heat_discharge_item = tes_discharge[index]  # Negative if heat is discharged, zero otherwise
            sum_heat_rate = chp_heat_rate_item + abs(tes_heat_discharge_item)

            if tes_heat_discharge_item.magnitude < 0 and dem_item <= chp_heat_rate_item:
                check_closeness = math.isclose((sum_heat_rate.magnitude - dem_item.magnitude), 0, abs_tol=10 ** -4)
                if check_closeness is False:
                    raise Exception('chp heat output and tes heat output exceeds building heating demand by {} at '
                                    'index {}. Check chp and tes heat output calculations for '
                                    'errors'.format(sum_heat_rate - dem_item, index))
                else:
                    ab_heat_rate_item = Q_(0, ureg.Btu / ureg.hour)
                    ab_heat_rate_hourly.append(ab_heat_rate_item)
            elif dem_item <= sum_heat_rate:
                ab_heat_rate_item = Q_(0, ureg.Btu / ureg.hour)
                ab_heat_rate_hourly.append(ab_heat_rate_item)
            elif sum_heat_rate < dem_item:
                ab_heat_rate_item = dem_item - sum_heat_rate
                ab_heat_rate_hourly.append(ab_heat_rate_item)
            else:
                raise Exception('Error in aux_boiler.py function calc_aux_boiler_output_rate()')

        # Check that hourly heat demand is within aux boiler operating parameters
        # TODO: We may have to assume that the boiler turndown is non-existent - test this section
        min_output = ab.min_pl * ab.cap
        for index, rate in enumerate(ab_heat_rate_hourly):
            if 0 < rate.magnitude <= min_output.magnitude:
                ab_heat_rate_hourly[index] = min_output
            elif ab.cap < rate:
                short = round(abs(rate - ab.cap), 2)
                raise Exception('ALERT: Boiler size is insufficient to meet heating demand! Output is short by '
                                '{} at hour number {}'.format(short, index))
        return ab_heat_rate_hourly


def calc_annual_fuel_use_and_cost(chp_size=None, chp=None, demand=None, tes=None, ab=None, load_following_type=None):
    """
    Updated 10/16/2022

    Calculates the annual fuel use and cost of fuel for the auxiliary boiler.

    Parameters
    ----------
    chp: CHP Class
        contains initialized class data using CLI inputs (see command_line.py)
    demand: EnergyDemand Class
        contains initialized class data using CLI inputs (see command_line.py)
    tes: TES Class
        contains initialized class data using CLI inputs (see command_line.py)
    ab: AuxBoiler Class
        contains initialized class data using CLI inputs (see command_line.py)
    load_following_type: string
        specifies whether calculation is for electrical load following (ELF) state
        or thermal load following (TLF) state.

    Returns
    -------
    annual_fuel_use_btu: Quantity
        annual fuel use of the auxiliary boiler in units of Btu
    annual_fuel_cost: Quantity (dimensionless)
        annual fuel cost, calculated from the annual fuel use of the boiler
    """
    # Fuel use calculation
    ab_output_rate_list = calc_aux_boiler_output_rate(chp_size=chp_size, chp=chp, demand=demand, tes=tes, ab=ab,
                                                      load_following_type=load_following_type)
    annual_heat_output = sum(ab_output_rate_list) * (1 * ureg.hour)
    annual_fuel_use_btu = annual_heat_output / ab.eff

    # Fuel cost calculation
    annual_fuel_use_mmbtu = annual_fuel_use_btu.to(ureg.megaBtu)
    annual_fuel_cost = demand.fuel_cost * annual_fuel_use_mmbtu

    return annual_fuel_use_btu, annual_fuel_cost
