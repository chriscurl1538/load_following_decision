"""
Module Description:
    Contains functions needed to calculate the thermal energy stored and thermal
    energy dispatched by the thermal energy storage (TES) system

TODO: Consider how to make TES calculations optional for with/without comparison
"""

from lfd_package.modules import chp as cogen
from lfd_package.modules.__init__ import ureg, Q_
import numpy as np


def calc_excess_and_deficit_heat(chp=None, demand=None, tes=None, load_following_type=None):
    """
    Calculates excess heat generated by the CHP unit each hour (positive values) and
    the difference between the heat generated by the mCHP unit and the heat needed
    to meet demand (negative values).

    Parameters
    ---------
    chp: CHP Class
        contains initialized CHP class data using CLI inputs (see command_line.py)
    demand: EnergyDemand Class
        contains initialized EnergyDemand class data using CLI inputs (see command_line.py)
    tes: TES Class
        contains initialized TES class data using CLI inputs (see command_line.py)
    load_following_type: string
        specifies whether calculation is for electrical load following (ELF) state
        or thermal load following (TLF) state.

    Returns
    -------
    excess_heat: list
        Excess heat generated by CHP each hour (positive) and additional heat needed
        (negative).
    """
    if chp is not None and demand is not None:
        heat_demand = demand.hl
        if load_following_type is "ELF":
            chp_heat_gen_hourly = cogen.elf_calc_hourly_heat_generated(chp=chp, demand=demand)
        elif load_following_type is "TLF":
            chp_heat_gen_hourly = cogen.tlf_calc_hourly_heat_generated(chp=chp, demand=demand, tes=tes)
        else:
            raise Exception("Error passing load_following_type to thermal_storage.py function, "
                            "calc_excess_and_deficit_heat")

        excess_heat = []

        for index, heat in enumerate(chp_heat_gen_hourly):
            dem = heat_demand[index]
            if dem < heat:
                heat_diff = abs(heat - dem)
                excess_heat.append(heat_diff)
            elif heat <= dem:
                heat_diff = -1 * abs(dem - heat)
                excess_heat.append(heat_diff)
            else:
                raise Exception('Error in thermal_storage module function: calc_excess_heat')
        return excess_heat


def tes_heat_stored(chp=None, demand=None, tes=None):
    """
    Adds or subtracts heat from storage based on excess heat generated by
    CHP or demand gaps not met by CHP.

    Parameters
    ---------
    chp: CHP Class
        contains initialized CHP class data using CLI inputs (see command_line.py)
    demand: EnergyDemand Class
        contains initialized EnergyDemand class data using CLI inputs (see command_line.py)
    tes: TES Class
        contains initialized TES class data using CLI inputs (see command_line.py)

    Returns
    -------
    charge_or_discharge: list
        Change in heat content of storage. Values are positive for heat added and
        negative for heat discharged
    status: list
        Hourly status of TES storage. Values are heat stored in Btu. Calculated by
        summing charge_or_discharge from index 0 to the current hour
    """
    if chp is not None and demand is not None and tes is not None:
        excess_and_deficit = calc_excess_and_deficit_heat(chp=chp, demand=demand)

        charge_or_discharge = []
        soc = []
        current_status = Q_(0, ureg.Btu)

        for index, i in enumerate(excess_and_deficit):
            new_status = i + current_status  # Summation should fix exception raised in aux_boiler module
            if i == 0:
                stored_heat = tes.start
                charge_or_discharge.append(stored_heat)
                soc.append(current_status/tes.cap)
            elif 0 < i and new_status <= tes.cap:
                stored_heat = i
                charge_or_discharge.append(stored_heat)
                current_status = new_status
                soc.append(current_status/tes.cap)
            elif 0 < i and tes.cap < new_status:
                diff = new_status - tes.cap
                stored_heat = i - diff
                charge_or_discharge.append(stored_heat)
                current_status = tes.cap
                soc.append(current_status/tes.cap)
            elif i < 0 <= new_status:
                stored_heat = i
                charge_or_discharge.append(stored_heat)
                current_status = new_status
                soc.append(current_status/tes.cap)
            elif i < 0 and new_status < 0:
                diff = new_status
                stored_heat = abs(i - diff)
                charge_or_discharge.append(stored_heat)
                current_status = Q_(0, ureg.Btu)
                soc.append(current_status/tes.cap)
            else:
                raise Exception("Error in tes_heat_stored function")

        return charge_or_discharge, soc
