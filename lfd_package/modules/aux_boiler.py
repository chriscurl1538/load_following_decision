"""
Module Description:
    Contains functions needed to calculate the heat generated and fuel used
    by the auxiliary boiler
"""

from lfd_package.modules import chp as cogen
from lfd_package.modules import thermal_storage as storage
from lfd_package.modules.__init__ import ureg, Q_


def calc_aux_boiler_output_rate(chp_size=None, tes_size=None, chp_gen_hourly_kwh_dict=None, load_following_type=None,
                                class_dict=None):
    """
    Using CHP heat output and TES heat discharge, this function determines when the
    heat demand exceeds the heat produced by the electric load following CHP system. Heat
    demand not met by CHP and TES is then assigned to the aux boiler (added to ab_heat_hourly list).
    Items in the list are then verified to be within boiler operating parameters.

    Parameters
    ---------
    class_dict: dict
        contains initialized class data using CLI inputs (see command_line.py)
    chp_gen_hourly_kwh_dict: dict
        contains lists of hourly chp electricity generated in kWh. Keys indicate
        operating mode (ELF, TLF, PP, Peak).
    tes_size: Quantity
        contains size of TES in units of Btu.
    chp_size: Quantity
        contains size of CHP in units of kW.
    load_following_type: string
        specifies whether calculation is for electrical load following (ELF) state
        or thermal load following (TLF) state.

    Returns
    -------
    ab_heat_rate_hourly: list (Quantity)
        Hourly heat output of the auxiliary boiler in units of Btu/hr
    """
    args_list = [chp_size, tes_size, chp_gen_hourly_kwh_dict, load_following_type, class_dict]
    if any(elem is None for elem in args_list) is False:
        # Pull chp heat and tes heat data

        # TODO: Optimize - remove functions called in CLI
        if load_following_type == "ELF":
            chp_heat_hourly = cogen.elf_calc_hourly_heat_generated(chp_gen_hourly_kwh=chp_gen_hourly_kwh_dict['ELF'],
                                                                   class_dict=class_dict)
            tes_heat_rate_list = storage.calc_tes_heat_flow_and_soc(chp_gen_hourly_kwh_dict=chp_gen_hourly_kwh_dict,
                                                                    tes_size=tes_size, class_dict=class_dict,
                                                                    load_following_type=load_following_type)[0]
        elif load_following_type == "TLF":
            chp_heat_hourly, tes_heat_rate_list = cogen.tlf_calc_hourly_heat_chp_tes_soc(chp_size=chp_size,
                                                                                         class_dict=class_dict)[0:2]
        elif load_following_type == "PP" or load_following_type == "Peak":
            chp_heat_hourly = cogen.pp_calc_hourly_heat_generated(class_dict=class_dict,
                                                                  chp_gen_hourly_kwh=chp_gen_hourly_kwh_dict[str(load_following_type)])
            tes_heat_rate_list = storage.calc_tes_heat_flow_and_soc(chp_gen_hourly_kwh_dict=chp_gen_hourly_kwh_dict,
                                                                    tes_size=tes_size, class_dict=class_dict,
                                                                    load_following_type=load_following_type)[0]
        else:
            raise Exception("Error in chp.py function, calc_annual_electric_cost")

        ab_heat_rate_hourly = []

        # Compare CHP and TES output with demand to determine AB output
        for index, dem in enumerate(class_dict['demand'].hl):
            chp_heat = chp_heat_hourly[index]
            tes_heat = tes_heat_rate_list[index]  # Negative if heat is discharged, zero otherwise
            chp_tes_heat_sum = chp_heat - tes_heat

            if dem <= chp_tes_heat_sum:
                ab_heat_rate_item = Q_(0, ureg.Btu / ureg.hour)
                ab_heat_rate_hourly.append(ab_heat_rate_item)
            elif chp_tes_heat_sum < dem:
                ab_heat_rate_item = dem - chp_tes_heat_sum
                ab_heat_rate_hourly.append(ab_heat_rate_item)
            else:
                raise Exception('Error in aux_boiler.py function calc_aux_boiler_output_rate()')

        # Check that hourly heat demand is within aux boiler operating parameters
        boiler_size = class_dict['demand'].annual_peak_hl
        for index, rate in enumerate(ab_heat_rate_hourly):
            if boiler_size < rate:
                short = round(abs(rate - boiler_size), 2)
                raise Exception('ALERT: Boiler size is insufficient to meet heating demand! Output is short by '
                                '{} at hour number {}'.format(short, index))
        return ab_heat_rate_hourly


def calc_hourly_fuel_use(ab_output_rate_list=None, class_dict=None):
    """
    Calculates the hourly fuel use of the auxiliary boiler.

    Parameters
    ----------
    ab_output_rate_list: list
        contains hourly heat generation of the auxiliary boiler.
    class_dict: dict
        contains initialized class data using CLI inputs (see command_line.py)

    Returns
    -------
    hourly_fuel_use_btu: list
        hourly fuel use of the auxiliary boiler in units of Btu
    """
    # Fuel use calculation
    hourly_fuel_use_btu = []
    for item in ab_output_rate_list:
        fuel_use = (item * Q_(1, ureg.hour)) / class_dict['ab'].eff
        hourly_fuel_use_btu.append(fuel_use.to(ureg.Btu))

    return hourly_fuel_use_btu
