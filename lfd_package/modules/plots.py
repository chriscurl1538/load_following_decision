"""
Module Description:
    This module will create plots of data passed to the program
    as well as relevant data calculated by the program
"""

import matplotlib.pyplot as plt, numpy as np
from lfd_package.modules import thermal_storage as storage
from lfd_package.modules import aux_boiler as boiler, chp as cogen


def plot_electrical_demand(demand=None):
    y = demand.el.magnitude

    # Calculate daily sums
    daily_kwh = []

    for i in range(24, len(y) + 1, 24):
        daily_kwh.append(y[(i - 24):i].sum())

    daily_kwh_array = np.array(daily_kwh)

    # set up plots
    plt.plot(daily_kwh_array)
    plt.title('Annual Electrical Demand, Daily')
    plt.ylabel('Electrical Demand [{}]'.format(demand.el[0].units))
    plt.yticks(np.arange(daily_kwh_array.min(), daily_kwh_array.max(), 20))
    plt.xlabel('Time (days)')

    # plot
    plt.show()


def plot_thermal_demand(demand=None):
    y = demand.hl.magnitude

    # Calculate daily sums
    daily_btu = []

    for i in range(24, len(y) + 1, 24):
        daily_btu.append(y[(i - 24):i].sum())

    daily_btu_array = np.array(daily_btu)

    if daily_btu_array.max() - daily_btu_array.min() >= 10:
        ytick_scale = (daily_btu_array.max() - daily_btu_array.min()) / 10
    else:
        ytick_scale = 5

    # set up plots
    plt.plot(daily_btu_array)
    plt.title('Annual Heating Demand, Daily')
    plt.ylabel('Heating Demand [{}]'.format(demand.hl[0].units))
    plt.yticks(np.arange(daily_btu_array.min(), daily_btu_array.max(), ytick_scale))
    plt.xlabel('Time (days)')

    # plot
    plt.show()


def plot_chp_electricity_generated(chp=None, demand=None):
    data = cogen.calc_hourly_generated_electricity(chp=chp, demand=demand)

    # Convert to base units before creating numpy array for plotting
    y = np.array([gen.to_base_units().magnitude for gen in data])

    # Calculate daily sums
    daily_kwh = []

    for i in range(24, len(y) + 1, 24):
        daily_kwh.append(y[(i - 24):i].sum())

    daily_kwh_array = np.array(daily_kwh)

    # Set up plot
    if daily_kwh_array.max() - daily_kwh_array.min() >= 10:
        ytick_scale = (daily_kwh_array.max() - daily_kwh_array.min()) / 10
    else:
        ytick_scale = 5

    plt.plot(daily_kwh_array)
    plt.title('CHP Electricity Generation, Daily')
    plt.ylabel('Electricity [{}]'.format(data[0].units))
    plt.yticks(np.arange(daily_kwh_array.min(), daily_kwh_array.max(), ytick_scale))
    plt.xlabel('Time (days)')

    # plot
    plt.show()


def plot_chp_heat_generated(chp=None, demand=None):
    data = cogen.calc_hourly_heat_generated(chp=chp, demand=demand)

    # Convert to base units before creating numpy array for plotting
    y = np.array([heat.to_base_units().magnitude for heat in data])

    # Calculate daily sums
    daily_btu = []

    for i in range(24, len(y) + 1, 24):
        daily_btu.append(y[(i - 24):i].sum())

    daily_btu_array = np.array(daily_btu)

    # Set up plot
    if daily_btu_array.max() - daily_btu_array.min() >= 10:
        ytick_scale = (daily_btu_array.max() - daily_btu_array.min()) / 10
    else:
        ytick_scale = 5

    plt.plot(daily_btu_array)
    plt.title('CHP Heat Generated, Daily')
    plt.ylabel('Heat [{}]'.format(data[0].units))
    plt.yticks(np.arange(daily_btu_array.min(), daily_btu_array.max(), ytick_scale))
    plt.xlabel('Time (days)')

    # plot
    plt.show()


def plot_tes_status(chp=None, demand=None, tes=None):
    data = storage.tes_heat_stored(chp=chp, demand=demand, tes=tes)[1]

    # Convert to base units before creating numpy array for plotting
    y = np.array([status.to_base_units().magnitude for status in data])

    # Calculate daily avg
    daily_btu = []

    for i in range(24, len(y) + 1, 24):
        daily_btu.append(np.average(y[(i - 24):i]))

    daily_btu_array = np.array(daily_btu)

    # Set up plot
    if daily_btu_array.max() - daily_btu_array.min() >= 10:
        ytick_scale = (daily_btu_array.max() - daily_btu_array.min()) / 10
    else:
        ytick_scale = 5

    plt.plot(daily_btu_array)
    plt.title('TES Status, Daily Avg')
    plt.ylabel('Heat [{}]'.format(data[0].units))
    plt.yticks(np.arange(daily_btu_array.min(), daily_btu_array.max(), ytick_scale))
    plt.xlabel('Time (days)')

    # plot
    plt.show()


def plot_aux_boiler_output(chp=None, demand=None, tes=None, ab=None):
    data = boiler.calc_aux_boiler_output(chp=chp, demand=demand, tes=tes, ab=ab)

    # Convert to base units before creating numpy array for plotting
    y = np.array([heat.to_base_units().magnitude for heat in data])

    # Calculate daily sums
    daily_btu = []

    for i in range(24, len(y) + 1, 24):
        daily_btu.append(y[(i - 24):i].sum())

    daily_btu_array = np.array(daily_btu)

    # Set up plot
    if daily_btu_array.max() - daily_btu_array.min() >= 10:
        ytick_scale = (daily_btu_array.max() - daily_btu_array.min()) / 10
    else:
        ytick_scale = 5

    plt.plot(daily_btu_array)
    plt.title('Boiler Output, Daily')
    plt.ylabel('Heat [{}]'.format(data[0].units))
    plt.yticks(np.arange(daily_btu_array.min(), daily_btu_array.max(), ytick_scale))
    plt.xlabel('Time (days)')

    # plot
    plt.show()
