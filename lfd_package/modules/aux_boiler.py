"""
Module Description:
    Contains functions needed to calculate the heat generated and fuel used
    by the auxiliary boiler
"""

from lfd_package.modules.__init__ import ureg, Q_


def calc_aux_boiler_output_rate(chp_size=None, tes_size=None, chp_gen_hourly_btuh_dict=None, load_following_type=None,
                                class_dict=None, tes_heat_flow_btuh=None):
    """
    Using CHP heat output and TES heat discharge, this function determines when the
    heat demand exceeds the heat produced by the electric load following CHP system. Heat
    demand not met by CHP and TES is then assigned to the aux boiler (added to ab_heat_hourly list).
    Items in the list are then verified to be within boiler operating parameters.

    Parameters
    ---------
    tes_heat_flow_btuh: list
        contains hourly heat flow into and out of the TES system. Negative values indicate dispatched heat.
        Units are in Btu/hr.
    class_dict: dict
        contains initialized class data using CLI inputs (see command_line.py)
    chp_gen_hourly_btuh_dict: dict
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
    args_list = [chp_size, tes_size, chp_gen_hourly_btuh_dict, load_following_type, class_dict, tes_heat_flow_btuh]
    if any(elem is None for elem in args_list) is False:
        # Pull chp heat and tes heat data
        chp_heat_flow_btuh = chp_gen_hourly_btuh_dict[str(load_following_type)]
        dem_heat_flow_btuh = class_dict['demand'].hl
        boiler_size = class_dict['demand'].annual_peak_hl
        ab_heat_rate_hourly = []

        # Compare CHP and TES output with demand to determine AB output
        for index in range(len(dem_heat_flow_btuh)):
            dem_btuh = dem_heat_flow_btuh[index]
            chp_btuh = chp_heat_flow_btuh[index]
            tes_btuh = -1 * tes_heat_flow_btuh[index]  # Negative if heat is dispatched. Dispatch is now turned positive
            chp_tes_sum = chp_btuh + tes_btuh

            if dem_btuh <= chp_tes_sum:
                ab_heat_rate_item = Q_(0, ureg.Btu / ureg.hour)
                ab_heat_rate_hourly.append(ab_heat_rate_item)
            elif chp_tes_sum < dem_btuh:
                ab_heat_rate_item = dem_btuh - chp_tes_sum

                # Check that hourly heat demand is within aux boiler operating parameters
                if boiler_size < ab_heat_rate_item:
                    short = round(abs(ab_heat_rate_item - boiler_size), 2)
                    raise Exception('ALERT: Boiler size is insufficient to meet heating demand! Output is short by '
                                    '{} at hour number {}'.format(short, index))
                else:
                    ab_heat_rate_hourly.append(ab_heat_rate_item)

        assert len(ab_heat_rate_hourly) == 8760
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
    args_list = [ab_output_rate_list, class_dict]
    if any(elem is None for elem in args_list) is False:
        # Fuel use calculation
        hourly_fuel_use_btu = []
        for item in ab_output_rate_list:
            fuel_use = (item * Q_(1, ureg.hour)) / class_dict['ab'].eff
            hourly_fuel_use_btu.append(fuel_use.to(ureg.Btu))

        return hourly_fuel_use_btu
