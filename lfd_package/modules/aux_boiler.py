"""
Module Description:
    Contains functions needed to calculate the heat generated and fuel used
    by the auxiliary boiler
"""
import math

from lfd_package.modules import chp as cogen
from lfd_package.modules import thermal_storage as storage
from lfd_package.modules.__init__ import ureg, Q_


# TODO: Known bug - aux boiler output in plots is always zero
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

        # Pull chp heat and tes heat data
        chp_heat_hourly = cogen.calc_hourly_heat_generated(chp=chp, demand=demand)
        tes_charge_discharge, tes_status_hourly = storage.tes_heat_stored(chp=chp, demand=demand, tes=tes)

        ab_heat_hourly = []
        tes_discharge = []
        chp_heat_no_excess = []

        # Remove waste heat production from CHP heat output data since TES captures excess
        for index, heat in enumerate(chp_heat_hourly):
            if demand.hl[index] < heat:
                no_excess = demand.hl[index]
                chp_heat_no_excess.append(no_excess)
            else:
                no_excess = heat
                chp_heat_no_excess.append(no_excess)

        # Get TES discharge only
        for index, dis in enumerate(tes_charge_discharge):
            if dis < 0:
                tes_discharge.append(dis)
            else:
                zero = Q_(0, ureg.Btu)
                tes_discharge.append(zero)

        # Compare CHP and TES output with demand to determine AB output
        for index, dem in enumerate(demand.hl):
            chp_heat = chp_heat_no_excess[index]
            tes_heat = tes_discharge[index]      # Negative if heat is discharged, zero otherwise
            sum_heat = chp_heat - tes_heat

            if tes_heat.magnitude < 0 and dem <= chp_heat:
                check_closeness = math.isclose((sum_heat.magnitude - dem.magnitude), 0, abs_tol=10**-4)
                if check_closeness is False:
                    raise Exception('chp heat output and tes heat output exceeds building heating demand by {}. '
                                    'Check chp and tes heat output calculations for errors'.format(sum_heat - dem))
                else:
                    ab_heat = Q_(0, ureg.Btu)
                    ab_heat_hourly.append(ab_heat)
            elif dem <= sum_heat:
                ab_heat = Q_(0, ureg.Btu)
                ab_heat_hourly.append(ab_heat)
            elif sum_heat < dem:
                ab_heat = abs(dem - sum_heat)
                ab_heat_hourly.append(ab_heat)
            else:
                raise Exception('Error in aux_boiler.py function calc_aux_boiler_output()')

        # Check that hourly heat demand is within aux boiler operating parameters
        for index, i in enumerate(ab_heat_hourly):
            if 0 < i.magnitude <= ab_min_btu.magnitude:
                ab_heat_hourly[index] = ab_min_btu
            elif ab_cap_btu < i:
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
