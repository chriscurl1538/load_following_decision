"""
Module Description:
    Contains functions needed to calculate the economics of thermal load following
    mCHP energy dispatch option

Assumptions:
    Fuel = Natural gas
    Prime Mover = Internal combustion engine
    Building = Mid-rise Apartment
    Other Equipment = Auxiliary Boiler, Thermal energy storage (TES) system
    Net metering is not allowed
"""

from load_following_decision_package import classes
import numpy as np


def is_aux_boiler_needed():
    return None


# def calc_aux_boiler_output():
#     """
#     Using CHP turn down ratio and heat to power ratio, this function determines when the
#     heat demand exceeds the heat produced by the electric load following CHP system.
#
#     Returns
#     -------
#
#     """
#     chp = classes.CHP()
#     chp_cap = chp.cap
#     try:
#         chp_min = chp_cap / chp.td
#     except ZeroDivisionError:
#         chp_min = 0
#     chp_heat_min = chp_min * chp.hp
#     chp_heat_max = chp_cap * chp.hp
#
#     demand = classes.EnergyDemand()
#     heat_demand_hourly = demand.hl
#
#     ab = classes.AuxBoiler()
#     ab_min = ab.cap / ab.td
#
#     boiler_needed = []
#     boiler_heat = []
#
#     for i in range(heat_demand_hourly.shape[0]):
#         # Verifies input dtype
#         heat_demand = float(heat_demand_hourly[i])
#
#         # Verifies acceptable input value range
#         assert heat_demand >= 0
#
#         if chp_heat_min <= heat_demand <= chp_heat_max:
#             heat = 0
#             boiler_heat.append(heat)
#             boiler_needed.append(False)
#         elif ab_min < heat_demand < chp_heat_min:
#             heat = abs(heat_demand - ab_min)
#             boiler_heat.append(heat)
#             boiler_needed.append(True)
#         elif chp_heat_max < heat_demand:
#             heat = abs(heat_demand - chp_heat_max)
#             boiler_heat.append(heat)
#             boiler_needed.append(True)
#         else:
#             raise Exception(
#                 "Error in ELF calc_aux_boiler_output function: Heat demand is less than minimum allowed aux "
#                 "boiler output")
#
#     return boiler_needed, boiler_heat


def calculate_ab_fuel_use():
    return None


def calculate_chp_fuel_use():
    return None


def is_electric_utility_needed():
    return None


