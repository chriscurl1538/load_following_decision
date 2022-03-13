"""
Module Description:
    Contains functions needed to calculate the heat generated and fuel used
    by the auxiliary boiler

Functions:
    Boiler needed (bool)
    Heat generated
    Fuel used
"""

# import classes
#
#
# def calc_aux_boiler_output():
#     """
#     Using CHP turn down ratio and heat to power ratio, this function determines when the
#     heat demand exceeds the heat produced by the electric load following CHP system. Heat
#     demand not met by CHP is then assigned to the aux boiler (added to boiler_heat list).
#     Items in the list are then verified to be within boiler operating parameters.
#
#     Returns
#     -------
#     boiler_heat: list
#         Hourly heat output of the auxiliary boiler
#     """
#     chp = classes.CHP()
#     chp_cap = chp.cap
#     chp_hp = chp.hp
#     try:
#         chp_min = chp_cap / chp.td
#     except ZeroDivisionError:
#         chp_min = 0
#
#     demand = classes.EnergyDemand()
#     el_demand_hourly = demand.el
#     heat_demand_hourly = demand.hl
#
#     ab = classes.AuxBoiler()
#     ab_cap = ab.cap
#     ab_min = ab.cap / ab.td
#
#     boiler_heat = []
#
#     for i in range(el_demand_hourly.shape[0]):
#         # Verifies input dtype
#         el_demand = float(el_demand_hourly[i])
#         heat_demand = float(heat_demand_hourly[i])
#
#         # Verifies acceptable input value range
#         assert el_demand >= 0
#         assert heat_demand >= 0
#
#         if chp_min <= el_demand <= chp_cap:
#             chp_heat = el_demand * chp_hp   # Compare heat generated to heat demand
#             if chp_heat < heat_demand:
#                 ab_heat = abs(heat_demand - chp_heat)
#                 boiler_heat.append(ab_heat)
#             else:
#                 ab_heat = 0
#                 boiler_heat.append(ab_heat)
#         elif el_demand < chp_min:
#             heat = heat_demand
#             boiler_heat.append(heat)
#         elif chp_cap < el_demand:
#             chp_heat = chp_cap * chp_hp
#             heat = abs(heat_demand - chp_heat)
#             boiler_heat.append(heat)
#         else:
#             raise Exception("Error in ELF calc_aux_boiler_output function: Heat demand is less than minimum allowed aux"
#                             "boiler output")
#
#     # Check that hourly heat demand is within aux boiler operating parameters
#     for i in boiler_heat:
#         if ab_min < i < ab_cap:
#             pass
#         elif i < ab_min:
#             i = 0
#         elif ab_cap < i:
#             i = ab_cap
#
#     return boiler_heat