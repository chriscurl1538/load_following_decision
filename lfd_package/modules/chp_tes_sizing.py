"""
Module description:
    These functions calculate the desired size of the CHP and TES systems
"""

import numpy as np
from sympy import symbols, solve
from lfd_package.modules.__init__ import ureg


def create_demand_curve_array(array=None):
    """
    TODO: Docstring updated 9/24/2022
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
        total_days = len(array) / 24
        reverse_sort_array = np.sort(array.magnitude, axis=0)
        sorted_demand_array = reverse_sort_array[::-1]
        percent_days = []
        for i, k in enumerate(array):
            percent = (i+1 / 24) / total_days
            percent_days.append(percent)
        percent_days_array = np.array(percent_days)
        return percent_days_array, sorted_demand_array


def electrical_output_to_fuel_consumption(electrical_output=None):
    """
    TODO: Docstring updated 9/24/2022
    Calculates approximate CHP fuel consumption for a given electrical output.
    The constants are from a linear fit of CHP data (<100kW) created in Excel.
    The data used for the fit are derived from the CHP TAP's eCatalog. The
    R^2 value of the fit is 0.9641. Link to eCatalog: https://chp.ecatalog.ornl.gov

    Used in the calc_min_pes_size function

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
        a = 3.309
        b = 20.525
        fuel_consumption_kw = (a * electrical_output.magnitude + b) * ureg.kW
        return fuel_consumption_kw


def electrical_output_to_thermal_output(electrical_output=None):
    """
    TODO: Docstring updated 9/24/2022
    Calculates approximate CHP thermal output for a given electrical output.
    The constants are from a second order polynomial fit of CHP data (<100kW)
    created in Excel. The data for the fit are derived from the CHP TAP's
    eCatalog. The R^2 value of the fit is 0.6016. Link to eCatalog:
    https://chp.ecatalog.ornl.gov

    Used in the calc_min_pes_size function.
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
        a = -0.0216
        b = 3.6225
        c = 5.0367
        thermal_output_kw = (a * electrical_output.magnitude**2 + b * electrical_output.magnitude + c) * ureg.kW
        return thermal_output_kw


def thermal_output_to_electrical_output(thermal_output=None):
    """
    TODO: There is more than one solution!
    TODO: Docstring updated 9/24/2022
    Calculates the approximate CHP electrical output for a given thermal output.
    The constants are from a second order polynomial fit of CHP data (<100kW)
    in excel. The data is derived from the CHP TAP eCatalog. The R^2 value of
    the fit is 0.0.6016. eCatalog link: https://chp.ecatalog.ornl.gov

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
        assert thermal_output.units == ureg.kW  # TODO: Might cause error
        a = -0.0216
        b = 3.6225
        c = 5.0367

        y = symbols('y')
        expr = a * y**2 + b * y + c - thermal_output.magnitude
        electrical_output_kw = solve(expr) * ureg.kW

        # if len(electrical_output_kw) == 1:
        #     return electrical_output_kw[0]
        # else:
        #     raise Exception('Error: More than one solution in sizing module, function
        #     thermal_output_to_electrical_output')
        return electrical_output_kw[0]


def size_chp(load_following_type=None, demand=None, ab=None):
    """
    TODO: Docstring updated 9/24/2022
    Sizes the CHP system using either the max_rect_chp_size function or the
    calc_min_pes_size function as needed depending on operating strategy (load
    following type) and/or presence of net metering.

    TODO: Where is this used?

    Parameters
    ----------
    load_following_type: string
        Reads as either "ELF" or "TLF" depending on whether the operating
        strategy is electrical load following or thermal load following,
        respectively.
    demand: EnergyDemand class
        Initialized class data (see command_line.py module)
    ab: AuxBoiler class
        Initialized class data (see command_line.py module)

    Returns
    -------
    chp_size: Quantity (float)
        Recommended size of CHP system in units of kW
    """
    if load_following_type is not None and demand is not None and ab is not None:
        if demand.net_metering_status is True:
            chp_size = calc_min_pes_chp_size(demand=demand, ab=ab)
        elif load_following_type == "ELF" and demand.net_metering_status is False:
            chp_size = calc_max_rect_chp_size(array=demand.el)
        elif load_following_type == "TLF" and demand.net_metering_status is False:
            chp_size = calc_min_pes_chp_size(demand=demand, ab=ab)
        else:
            raise Exception("Error in size_chp function in module chp_tes_sizing.py")
        return chp_size


def calc_max_rect_chp_size(array=None):
    """
    TODO: Docstring updated 9/24/2022
    Calculates the recommended CHP size in kW based on the Maximum Rectangle (MR)
    sizing method.

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
        max_value = np.amax(prod_array)
        return max_value


def calc_min_pes_chp_size(demand=None, ab=None):
    """
    TODO: Docstring updated 9/24/2022
    Recommends a CHP system size using the minimum Primary Energy Savings
    (PES) method.

    Used in the size_chp function

    Parameters
    ----------
    demand: EnergyDemand class
        Initialized class data (see command_line.py module)
    ab: AuxBoiler class
        Initialized class data (see command_line.py module)

    Returns
    -------
    min_pes_size: Quantity (float)
        Recommended size of CHP system in units of kW electrical
    """
    # TODO: Account for no net metering + TLF operation
    if demand is not None and ab is not None:
        chp_size_list = list(range(10, 105, 5)) * ureg.kW   # TODO: Check that units are attached to items in list

        grid_eff = demand.grid_efficiency
        size_list = []
        pes_list = []

        for size in chp_size_list:
            max_fuel_consumption = electrical_output_to_fuel_consumption(size)
            max_thermal_output = electrical_output_to_thermal_output(size)
            electrical_eff = size/max_fuel_consumption
            thermal_eff = max_thermal_output/max_fuel_consumption

            nominal_electrical_eff = electrical_eff / grid_eff
            nominal_thermal_eff = thermal_eff / ab.eff
            pes = 1 - (1/(nominal_thermal_eff + nominal_electrical_eff))

            size_list.append(size)
            pes_list.append(pes)

        min_pes_value = min(pes_list)
        min_pes_index = pes_list.index(min_pes_value)
        min_pes_size = size_list[min_pes_index]
        return min_pes_size


# def size_tes():
#     return None
