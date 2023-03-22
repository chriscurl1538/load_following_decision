"""
Module Description:
    Contains functions needed to calculate the thermal energy stored and thermal
    energy dispatched by the thermal energy storage (TES) system
"""

from lfd_package.modules import chp as cogen, sizing_calcs as sizing
from lfd_package.modules.__init__ import ureg, Q_


def calc_excess_and_deficit_chp_heat_gen(chp=None, demand=None, ab=None, load_following_type=None):
    """
    Calculates excess heat generated by the CHP unit each hour (positive values) and
    the difference between the heat generated by the CHP unit and the heat needed
    to meet demand (negative values).

    Function is used in the calc_tes_heat_flow_and_soc function

    Parameters
    ---------
    ab: AuxBoiler Class
        contains initialized class data using CLI inputs (see command_line.py)
    chp: CHP Class
        contains initialized class data using CLI inputs (see command_line.py)
    demand: EnergyDemand Class
        contains initialized class data using CLI inputs (see command_line.py)
    load_following_type: string
        specifies whether calculation is for electrical load following (ELF) state
        or thermal load following (TLF) state.

    Returns
    -------
    excess_heat: list (Quantity)
        Excess heat generated by CHP each hour (positive) and additional heat needed
        (negative). All items have units of Btu/hour.
    """
    if any(elem is None for elem in [chp, demand, ab, load_following_type]) is False:
        heat_demand = demand.hl
        if load_following_type is "PP":
            electrical_output_kw = sizing.size_chp(load_following_type=load_following_type, demand=demand, ab=ab)
            chp_heat_gen_item_kw = sizing.electrical_output_to_thermal_output(electrical_output=electrical_output_kw)
            chp_heat_gen_item_btu_hour = chp_heat_gen_item_kw.to(ureg.Btu / ureg.hour)
            chp_heat_gen_hourly = [chp_heat_gen_item_btu_hour for i in range(len(demand.hl))]
        elif load_following_type is "ELF":
            chp_heat_gen_hourly = cogen.elf_calc_hourly_heat_generated(chp=chp, demand=demand, ab=ab)
        elif load_following_type is "TLF":
            chp_heat_gen_hourly = cogen.tlf_calc_hourly_heat_generated(chp=chp, demand=demand, ab=ab)
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


def calc_tes_heat_flow_and_soc(chp=None, demand=None, tes=None, ab=None, load_following_type=None):
    """
    Adds or subtracts heat from storage based on excess heat generated by
    CHP or demand gaps not met by CHP (according to calc_excess_and_deficit_chp_heat_gen
    function).

    Used in the aux_boiler.py function, calc_aux_boiler_output_rate

    Parameters
    ---------
    ab: AuxBoiler Class
        contains initialized class data using CLI inputs (see command_line.py)
    chp: CHP Class
        contains initialized class data using CLI inputs (see command_line.py)
    demand: EnergyDemand Class
        contains initialized class data using CLI inputs (see command_line.py)
    tes: TES Class
        contains initialized class data using CLI inputs (see command_line.py)
    load_following_type: string
        specifies whether calculation is for electrical load following (ELF) state
        or thermal load following (TLF) state.

    Returns
    -------
    tes_heat_rate_list_btu_hour: list (Quantity)
        Storage heat rate for each hour. Values are positive for heat added and
        negative for heat discharged.Units are Btu/hr
    soc_list: list (Quantity, dimensionless)
        Hourly status of TES storage. Values are 0 for empty and 1 for full. Calculated by
        dividing current_status by the TES capacity.
    """
    if any(elem is None for elem in [chp, demand, ab, load_following_type]) is False:
        tes_size = sizing.size_tes(demand=demand, chp=chp, ab=ab, load_following_type=load_following_type)

        # Exit function if TES is not recommended
        if tes_size.magnitude == 0:
            zero_rate_list = []
            zero_soc_list = []
            list_size = len(demand.hl)
            zero_rate_item = Q_(0, ureg.Btu / ureg.hour)
            zero_soc_item = Q_(0, '')
            for index in range(list_size):
                zero_rate_list.append(zero_rate_item)
                zero_soc_list.append(zero_soc_item)
            return zero_rate_list, zero_soc_list

        excess_and_deficit = calc_excess_and_deficit_chp_heat_gen(chp=chp, demand=demand, ab=ab,
                                                                  load_following_type=load_following_type)
        tes_heat_rate_list_btu_hour = []
        soc_list = []
        current_status = tes.start

        for index, heat_rate in enumerate(excess_and_deficit):
            new_status = (heat_rate * 1 * ureg.hour) + current_status
            if heat_rate == 0:
                stored_heat = Q_(0, ureg.Btu / ureg.hour)
                tes_heat_rate_list_btu_hour.append(stored_heat)
                soc_list.append(current_status/tes_size)
            elif 0 < heat_rate and new_status <= tes_size:
                stored_heat = heat_rate
                tes_heat_rate_list_btu_hour.append(stored_heat)
                current_status = new_status
                soc_list.append(current_status/tes_size)
            elif 0 < heat_rate and tes_size < new_status:
                diff = (new_status - tes_size) / (1 * ureg.hour)
                stored_heat = heat_rate - diff
                tes_heat_rate_list_btu_hour.append(stored_heat)
                current_status = tes_size
                soc_list.append(current_status/tes_size)
            elif (heat_rate * 1 * ureg.hour) < 0 <= new_status:
                stored_heat = heat_rate
                tes_heat_rate_list_btu_hour.append(stored_heat)
                current_status = new_status
                soc_list.append(current_status/tes_size)
            elif heat_rate < 0 and new_status < 0:
                diff = new_status / (1 * ureg.hour)
                stored_heat = abs(heat_rate - diff)
                tes_heat_rate_list_btu_hour.append(stored_heat)
                current_status = Q_(0, ureg.Btu)
                soc_list.append(current_status/tes_size)
            else:
                raise Exception("Error in tes_heat_stored function")

        return tes_heat_rate_list_btu_hour, soc_list
