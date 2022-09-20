"""
Module description:
    These functions calculate the desired size of the CHP and TES systems
TODO: Incorporate net metering status operation condition
"""

import numpy as np
from scipy.optimize import curve_fit
from lfd_package.modules.__init__ import ureg


def create_demand_curve_array(array=None):
    if array is not None:
        assert array.ndim == 1
        total_days = len(array) / 24
        reverse_sort_array = np.sort(array.magnitude, axis=0)
        sorted_demand_array = reverse_sort_array[::-1]
        percent_days = []
        for i, k in enumerate(array):
            percent = (i / 24) / total_days
            percent_days.append(percent)
        percent_days_array = np.array(percent_days)
        return percent_days_array, sorted_demand_array


def create_efficiency_equation_coefficients(chp=None):
    if chp is not None:
        # Function to calculate the exponential with constants a and b
        def exponential(x, a, b):
            return a * np.exp(b * x)

        # Assign the data to be fitted
        part_loads = chp.el_pl[:, 0]
        thermal_efficiencies = chp.th_pl[0, :]
        electrical_efficiencies = chp.el_pl[0, :]

        # Fit the exponential data
        pars_th, cov_th = curve_fit(f=exponential, xdata=part_loads, ydata=thermal_efficiencies, p0=[0, 0],
                                    bounds=(-np.inf, np.inf))
        pars_el, cov_el = curve_fit(f=exponential, xdata=part_loads, ydata=electrical_efficiencies, p0=[0, 0],
                                    bounds=(-np.inf, np.inf))

        # TODO: Graph values and standard deviations
        # # Get the standard deviations of the parameters (square roots of the # diagonal of the covariance)
        # stdevs_th = np.sqrt(np.diag(cov_th))
        # stdevs_el = np.sqrt(np.diag(cov_el))
        #
        # # Calculate the residuals
        # res_th = thermal_efficiencies - exponential(part_loads, *pars_th)
        # res_el = electrical_efficiencies - exponential(part_loads, *pars_el)

        return pars_el, pars_th


def size_chp(load_following_type=None, demand=None, ab=None):
    if load_following_type is not None and demand is not None:
        net_metering_status = demand.net_metering_status
        if net_metering_status is True:
            chp_size = calc_min_pes_size(demand=demand, ab=ab) * ureg.kW
        elif load_following_type == "ELF" and net_metering_status is False:
            chp_size = max_rect_chp_size(demand.el) * ureg.kW
        elif load_following_type == "TLF" and net_metering_status is False:
            chp_size = calc_min_pes_size(demand=demand, ab=ab) * ureg.kW
        else:
            raise Exception("Error in size_chp function in module chp_tes_sizing.py")
        return chp_size


def max_rect_chp_size(array=None):
    if array is not None:
        assert array.ndim == 1
        percent_days_array, sorted_demand_array = create_demand_curve_array(array=array)
        prod_array = np.multiply(percent_days_array, sorted_demand_array)
        max_value = np.amax(prod_array)
        return max_value


def calc_min_pes_size(demand=None, ab=None):
    # TODO: Create an array of sizes with associated nominal efficiencies, put it here

    eff_array = np.array([24, 0.284, 0.562],  # https://chp.ecatalog.ornl.gov/package/76-PR23-ZC97330
             [34, 0.284, 0.582],  # https://chp.ecatalog.ornl.gov/package/97-SP9-ZC97330
             [54, 0.305, 0.560],  # https://chp.ecatalog.ornl.gov/package/99-PR18-ZC97330
             [59, 0.259, 0.532],  # https://chp.ecatalog.ornl.gov/package/114-PR7-ZC97330
             [73, 0.259, 0.542])  # https://chp.ecatalog.ornl.gov/package/11-SP8-ZC97330

    grid_eff = demand.grid_efficiency
    size_list = []
    pes_list = []
    if demand is not None and ab is not None:
        for row in eff_array:
            size = row[0]
            nominal_electrical_eff = row[1] / grid_eff
            nominal_thermal_eff = row[2] / ab.eff
            pes = 1 - (1/(nominal_thermal_eff + nominal_electrical_eff))

            size_list.append(size)
            pes_list.append(pes)
    min_pes_value = min(pes_list)
    min_pes_index = pes_list.index(min_pes_value)
    min_pes_size = size_list[min_pes_index]

    return min_pes_size


def size_tes():
    return None