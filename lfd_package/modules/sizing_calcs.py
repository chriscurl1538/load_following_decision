"""
Module description:
    These functions calculate the desired size of the CHP and TES systems
"""

import numpy as np
from lfd_package.modules.__init__ import ureg, Q_
from lfd_package.modules import thermal_storage as storage, chp as cogen


def create_demand_curve_array(array=None):
    """
    Creates two 1D numpy arrays containing percent total days (days / days in 1 year)
    and associated energy demand data (thermal or electrical), respectively.

    Used in the max_rect_chp_size function for CHP sizing using the Max Rectangle (MR) method.

    Parameters
    ----------
    array: numpy.ndarray (Quantity)
        One dimensional numpy array containing energy demand data (thermal or electrical).
        Items in the array are Quantity values.

    Returns
    -------
    percent_days_array: numpy.ndarray
        1D array of percent total days (day in year / total days in 1 year) values.
    sorted_demand_array: numpy.ndarray (Quantity)
        1D array of energy demand data associated with the percent-days data. Contains
        Quantity values.
    """
    if array is not None:
        assert array.ndim == 1
        reverse_sort_array = np.sort(array, axis=0)
        sorted_demand_array = reverse_sort_array[::-1]
        percent_days = []
        for i, k in enumerate(array):
            percent = ((i+1) / len(array))*100
            percent_days.append(percent)
        percent_days_array = np.array(percent_days)
        return percent_days_array, sorted_demand_array


def electrical_output_to_fuel_consumption(electrical_output=None):
    """
    Calculates approximate CHP fuel consumption for a given electrical output.
    The constants are from a linear fit of CHP data (<100kW) created in Excel.
    The data used for the fit are derived from the CHP TAP's eCatalog.
    Link to eCatalog: https://chp.ecatalog.ornl.gov

    Used in the calc_pes_chp_size() function

    Parameters
    ----------
    electrical_output: Quantity (float)
        Electrical output of CHP in units of kW

    Returns
    -------
    fuel_consumption_kw: Quantity (float)
        Approximate fuel consumption of CHP in units of kW thermal
    """
    if electrical_output is not None:
        assert electrical_output.units == ureg.kW

        if electrical_output.magnitude == 0:
            return Q_(0, ureg.kW)
        else:
            a = 3.6376
            assert electrical_output.units == ureg.kW
            fuel_consumption_kw = (a * electrical_output.magnitude) * ureg.kW
            return fuel_consumption_kw


def electrical_output_to_thermal_output(electrical_output=None):
    """
    Calculates approximate CHP thermal output for a given electrical output.
    The constants are from a linear fit of CHP data (<100kW)
    created in Excel. The data for the fit are derived from the CHP TAP's
    eCatalog.
    Link to eCatalog: https://chp.ecatalog.ornl.gov

    Used in the calc_pes_chp_size function.
    Used in the calc_avg_efficiency, elf_calc_hourly_heat_generated, and
    tlf_calc_hourly_heat_generated functions in the chp.py module

    Parameters
    ----------
    electrical_output: Quantity (float)
        Electrical output of CHP in units of kW

    Returns
    -------
    thermal_output_kw: Quantity (float)
        Approximate thermal output of CHP in units of kW
    """
    if electrical_output is not None:
        assert electrical_output.units == ureg.kW

        if electrical_output.magnitude == 0:
            return Q_(0, ureg.kW)
        else:
            a = 1.8721
            thermal_output_kw = (a * electrical_output.magnitude) * ureg.kW
            return thermal_output_kw


def thermal_output_to_electrical_output(thermal_output=None):
    """
    Calculates the approximate CHP electrical output for a given thermal output.
    The constants are from a linear fit of CHP data (<100kW)
    in Excel. The data is derived from the CHP TAP eCatalog.
    eCatalog link: https://chp.ecatalog.ornl.gov

    Used in the tlf_calc_electricity_bought_and_generated function in the
    chp.py module

    Parameters
    ----------
    thermal_output: Quantity (float)
        Thermal output of CHP in units of kW (thermal)

    Returns
    -------
    electrical_output_kw: Quantity (float)
        Approximate electrical output of CHP in units of kW
    """
    if thermal_output is not None:
        assert thermal_output.units == ureg.kW

        if thermal_output.magnitude == 0:
            return Q_(0, ureg.kW)
        else:
            a = 0.5188
            electrical_output_kw = (thermal_output.magnitude * a) * ureg.kW
            if electrical_output_kw.magnitude <= 0:
                return Q_(0, ureg.kW)
            else:
                return electrical_output_kw


def size_chp(load_following_type=None, class_dict=None):
    """
    Sizes the CHP system using either the calc_max_rect_chp_size() function or the
    calc_pes_chp_size() function as needed depending on operating strategy (load
    following type).

    Used in chp.py module

    Parameters
    ----------
    class_dict: dict
        contains initialized class data using CLI inputs (see command_line.py)
    load_following_type: string
        Reads as either "ELF" or "TLF" depending on whether the operating
        strategy is electrical load following or thermal load following,
        respectively.

    Returns
    -------
    chp_size: Quantity (float)
        Recommended size of CHP system in units of kW
    """
    args_list = [load_following_type, class_dict]
    if any(elem is None for elem in args_list) is False:
        if load_following_type == "PP" or load_following_type == "Peak":
            chp_size = calc_pes_chp_size(class_dict=class_dict)
        elif load_following_type == "ELF":
            chp_size = calc_max_rect_chp_size(array=class_dict['demand'].el)
        elif load_following_type == "TLF":
            thermal_size = (calc_max_rect_chp_size(array=class_dict['demand'].hl)).to(ureg.kW)
            chp_size = thermal_output_to_electrical_output(thermal_output=thermal_size)
        else:
            raise Exception("Error in size_chp function in module sizing_calcs.py")

        # Convert units
        if chp_size.units != ureg.kW:
            chp_size.to(ureg.kW)

        return chp_size


def calc_max_rect_chp_size(array=None):
    """
    Calculates the recommended CHP size in kW based on the Maximum Rectangle (MR)
    sizing method. The input array is either electrical or thermal demand.

    Used in the size_chp function

    Parameters
    ----------
    array: numpy.ndarray
        One 1D numpy array containing either electrical or thermal energy demand data.
        Items in this array are Quantity values with units of either kW or Btu/hr.

    Returns
    -------
    max_value: Quantity (float)
        The recommended size (either thermal or electrical) of the CHP system. Units
        will be either kW or Btu/hr.
    """
    if array is not None:
        assert array.ndim == 1
        percent_days_array, sorted_demand_array = create_demand_curve_array(array=array)
        prod_array = np.multiply(percent_days_array, sorted_demand_array)
        max_index = np.argmax(prod_array)
        max_value = sorted_demand_array[max_index]
        return max_value


def calc_pes_chp_size(class_dict=None):
    """
    Recommends a CHP system size using the minimum Primary Energy Savings
    (PES) method. A high PES value indicates that the associated CHP size
    saves the maximum energy compared to the baseline case. A low PES value
    indicates that the associated CHP size is the most profitable (but saves
    the least energy compared to the baseline case). This function returns the
    maximum PES value.

    Used in the size_chp function

    Parameters
    ----------
    class_dict: dict
        contains initialized class data using CLI inputs (see command_line.py)

    Returns
    -------
    max_pes_size: Quantity (float)
        Recommended size of CHP system in units of kW electrical
    """
    args_list = [class_dict]
    if any(elem is None for elem in args_list) is False:
        chp_size_list = list(range(10, 105, 5)) * ureg.kW

        grid_eff = class_dict['demand'].grid_efficiency
        size_list = []
        pes_list = []

        for size in chp_size_list:
            chp_gen_kwh_list = cogen.pp_calc_electricity_gen_sold(chp_size=size, class_dict=class_dict)[0]
            chp_gen_btuh_list = cogen.pp_calc_hourly_heat_generated(chp_gen_hourly_kwh=chp_gen_kwh_list,
                                                                    class_dict=class_dict)
            fuel_consumption_list = cogen.calc_hourly_fuel_use(chp_gen_hourly_btuh=chp_gen_btuh_list, chp_size=size,
                                                               load_following_type='PP', class_dict=class_dict)

            fuel_consumption = sum(fuel_consumption_list)
            thermal_output = sum(chp_gen_btuh_list) * Q_(1, ureg.hours)
            electrical_output = sum(chp_gen_kwh_list)
            electrical_eff = electrical_output/fuel_consumption
            thermal_eff = thermal_output/fuel_consumption

            nominal_electrical_eff = (electrical_eff / grid_eff).to('')
            nominal_thermal_eff = thermal_eff / class_dict['ab'].eff
            pes = 1 - (1/(nominal_thermal_eff + nominal_electrical_eff))

            size_list.append(size)
            pes_list.append(pes)

        max_pes_value = max(pes_list)
        max_pes_index = pes_list.index(max_pes_value)
        max_pes_size = size_list[max_pes_index]

        return max_pes_size


def size_tes(chp_size=None, class_dict=None):
    """
    Sizes TES by maximizing the system efficiency. Uses uncovered heat demand values and excess chp heat
    generation values (calculated from electricity generation using electrical_output_to_thermal_output()).
    Chooses the smallest of these two values for each day and creates a list of those
    minimums. Then chooses the max value in that list as the recommended size.

    Parameters
    ----------
    chp_gen_hourly_btuh: list
        contains hourly chp heat generated in Btu/hr.
    chp_size: Quantity
        contains size of CHP unit in kW.
    load_following_type: str
        specifies whether calculation is for electrical load following (ELF) state
        or thermal load following (TLF) state.
    class_dict: dict
        contains initialized class data using CLI inputs (see command_line.py)

    Returns
    -------
    tes_size_btu: Quantity
        Recommended thermal storage size in units of Btu.
    """
    # Create empty lists
    uncovered_heat_demand_hourly = []
    daily_uncovered_heat_btu_list = []
    excess_chp_heat_gen_hourly = []
    daily_excess_chp_heat_btu_list = []
    list_comparison_min_values = []

    # For unit management in pint
    hour_unit = Q_(1, ureg.hour)

    # Pull needed data (assumes CHP runs at constant max generation for sizing purposes)
    hourly_excess_and_deficit_list = \
        [(electrical_output_to_thermal_output(chp_size)).to(ureg.Btu / ureg.hour) - dem for dem in
         class_dict['demand'].hl]

    assert isinstance(hourly_excess_and_deficit_list, list)
    assert hourly_excess_and_deficit_list[0].units == ureg.Btu / ureg.hour

    # Separate data into excess generation list and uncovered demand list
    for index, element in enumerate(hourly_excess_and_deficit_list):
        if element.magnitude <= 0:
            uncovered_heat_demand_hourly.append(Q_(abs(element.magnitude), element.units))
            excess_chp_heat_gen_hourly.append(Q_(0, ureg.Btu / ureg.hour))
        elif 0 < element.magnitude:
            uncovered_heat_demand_hourly.append(Q_(0, ureg.Btu / ureg.hour))
            excess_chp_heat_gen_hourly.append(Q_(abs(element.magnitude), element.units))
        else:
            raise Exception('Error in sizing_calcs.py function, size_tes()')

    # Turn hourly lists into daily sums
    assert len(uncovered_heat_demand_hourly) == len(excess_chp_heat_gen_hourly)
    for index in range(24, len(uncovered_heat_demand_hourly) + 1, 24):
        daily_uncovered_heat_btu_hour = sum(uncovered_heat_demand_hourly[(index - 24):index])
        daily_uncovered_heat_btu = (daily_uncovered_heat_btu_hour * hour_unit).to(ureg.Btu)
        daily_uncovered_heat_btu_list.append(daily_uncovered_heat_btu)

        daily_excess_heat_btu_hour = sum(excess_chp_heat_gen_hourly[(index - 24):index])
        daily_excess_heat_btu = (daily_excess_heat_btu_hour * hour_unit).to(ureg.Btu)
        daily_excess_chp_heat_btu_list.append(daily_excess_heat_btu)

    # Compare the two lists and pick the min for each day
    assert len(daily_excess_chp_heat_btu_list) == len(daily_uncovered_heat_btu_list)
    for index in range(len(daily_excess_chp_heat_btu_list)):
        if daily_excess_chp_heat_btu_list[index] <= daily_uncovered_heat_btu_list[index]:
            list_comparison_min_values.append(daily_excess_chp_heat_btu_list[index])
        elif daily_uncovered_heat_btu_list[index] < daily_excess_chp_heat_btu_list[index]:
            list_comparison_min_values.append(daily_uncovered_heat_btu_list[index])
        else:
            raise Exception('Error in sizing_calcs.py function, size_tes()')

    assert len(list_comparison_min_values) == len(daily_excess_chp_heat_btu_list)

    # Search the resulting list of min values for the maximum, aka the TES size
    tes_size_btu = max(list_comparison_min_values)
    assert list_comparison_min_values[0].units == ureg.Btu
    assert tes_size_btu.units == ureg.Btu

    if 0 <= tes_size_btu.magnitude:
        return tes_size_btu
    else:
        raise Exception('TES size is negative - error in size_tes() function')
