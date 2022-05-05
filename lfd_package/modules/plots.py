"""
Module Description:
    This module will create plots of data passed to the program
    as well as relevant data calculated by the program

TODO: Replace TES plot with TES SOC plot. Also add TES
TODO: charge/discharge plot with positive discharging convention
TODO: Make sets of subplots for each equipment
"""

import matplotlib.pyplot as plt, numpy as np
from lfd_package.modules import thermal_storage as storage
from lfd_package.modules import aux_boiler as boiler, chp as cogen


def plot_electric(chp=None, demand=None):
    data1 = cogen.calc_hourly_generated_electricity(chp=chp, demand=demand)
    data2 = cogen.calc_hourly_electricity_bought(chp=chp, demand=demand)

    # Convert to base units before creating numpy array for plotting
    y0 = demand.el.magnitude
    y1 = np.array([gen.to_base_units().magnitude for gen in data1])
    y2 = np.array([gen.to_base_units().magnitude for gen in data2])

    # Calculate daily sums
    daily_kwh_dem = []
    daily_kwh_chp = []
    daily_kwh_buy = []

    for i in range(24, len(y0) + 1, 24):
        daily_kwh_dem.append(y0[(i - 24):i].sum())
        daily_kwh_chp.append(y1[(i - 24):i].sum())
        daily_kwh_buy.append(y2[(i - 24):i].sum())

    daily_kwh_dem_array = np.array(daily_kwh_dem)
    daily_kwh_chp_array = np.array(daily_kwh_chp)
    daily_kwh_buy_array = np.array(daily_kwh_buy)

    # Set up plot
    fig, (ax1, ax2, ax3) = plt.subplots(1, 3, sharex='all', sharey='all')
    fig.suptitle('Annual Electrical Demand and Generation, Daily [kWh]')
    ax1.plot(daily_kwh_dem_array)
    ax1.set_ylabel('Demand')
    ax2.plot(daily_kwh_chp_array)
    ax2.set_ylabel('CHP')
    ax3.plot(daily_kwh_buy_array)
    ax3.set_ylabel('Electricity Bought')
    ax3.set_xlabel('Time (days)')

    plt.show()


def plot_thermal(chp=None, demand=None, tes=None, ab=None):
    data1 = cogen.calc_hourly_heat_generated(chp=chp, demand=demand)
    data2 = storage.tes_heat_stored(chp=chp, demand=demand, tes=tes)[0]
    data3 = boiler.calc_aux_boiler_output(chp=chp, demand=demand, tes=tes, ab=ab)

    # Convert to base units before creating numpy array for plotting
    y0 = demand.hl.magnitude
    y1 = np.array([gen.to_base_units().magnitude for gen in data1])
    y2 = np.array([gen.to_base_units().magnitude for gen in data2])
    y3 = np.array([gen.to_base_units().magnitude for gen in data3])

    # Calculate daily sums
    daily_kwh_dem = []
    daily_kwh_chp = []
    daily_kwh_tes = []
    daily_kwh_ab = []

    for i in range(24, len(y0) + 1, 24):
        daily_kwh_dem.append(y0[(i - 24):i].sum())
        daily_kwh_chp.append(y1[(i - 24):i].sum())
        daily_kwh_tes.append(y2[(i - 24):i].sum())
        daily_kwh_ab.append(y2[(i - 24):i].sum())

    daily_kwh_dem_array = np.array(daily_kwh_dem)
    daily_kwh_chp_array = np.array(daily_kwh_chp)
    daily_kwh_tes_array = np.array(daily_kwh_tes)
    daily_kwh_ab_array = np.array(daily_kwh_ab)

    # Set up plot
    fig, (ax1, ax2, ax3, ax4) = plt.subplots(1, 4, sharex='all', sharey='all')
    fig.suptitle('Annual Thermal Demand and Generation, Daily [kWh]')
    ax1.plot(daily_kwh_dem_array)
    ax1.set_ylabel('Demand')
    ax2.plot(daily_kwh_chp_array)
    ax2.set_ylabel('CHP')
    ax3.plot(daily_kwh_tes_array)
    ax3.set_ylabel('TES Discharge')
    ax4.plot(daily_kwh_ab_array)
    ax4.set_ylabel('Aux Boiler')
    ax4.set_xlabel('Time (days)')

    plt.show()


def plot_tes_soc(chp=None, demand=None, tes=None):
    data = storage.tes_heat_stored(chp=chp, demand=demand, tes=tes)[1]

    # Convert to base units before creating numpy array for plotting
    y = np.array([status.to_base_units().magnitude for status in data])

    # Calculate daily avg for discharge plot
    daily_btu = []

    for i in range(24, len(y) + 1, 24):
        daily_btu.append(np.average(y[(i - 24):i]))

    daily_btu_array = np.array(daily_btu)

    # Set up plots
    plt.plot(daily_btu_array)
    plt.title('TES SOC, Daily Avg')
    plt.ylabel('SOC')
    plt.yticks(np.arange(0, 1, 0.1))
    plt.xlabel('Time (days)')

    # plot
    plt.show()


# def plot_demand(demand=None):
#     y1 = demand.el.magnitude
#     y2 = demand.hl.magnitude
#
#     # Calculate daily sums
#     daily_kwh_el = []
#     daily_kwh_hl = []
#
#     for i in range(24, len(y1) + 1, 24):
#         daily_kwh_el.append(y1[(i - 24):i].sum())
#         daily_kwh_hl.append(y2[(i - 24):i].sum())
#
#     daily_kwh_el_array = np.array(daily_kwh_el)
#     daily_kwh_hl_array = np.array(daily_kwh_hl)
#
#     # Set up plot
#     fig, (ax1, ax2) = plt.subplots(2, sharex='all')
#     fig.suptitle('Annual Demand, Daily')
#     ax1.plot(daily_kwh_el_array)
#     ax1.set_ylabel('Electrical [{}]'.format(demand.el[0].units))
#     ax2.plot(daily_kwh_hl_array)
#     ax2.set_ylabel('Thermal [{}]'.format(demand.hl[0].units))
#     ax2.set_xlabel('Time (days)')
#
#     plt.show()
#
#
# def plot_chp(chp=None, demand=None):
#     data1 = cogen.calc_hourly_generated_electricity(chp=chp, demand=demand)
#     data2 = cogen.calc_hourly_heat_generated(chp=chp, demand=demand)
#
#     # Convert to base units before creating numpy array for plotting
#     y1 = np.array([gen.to_base_units().magnitude for gen in data1])
#     y2 = np.array([gen.to_base_units().magnitude for gen in data2])
#
#     # Calculate daily sums
#     daily_kwh_el = []
#     daily_kwh_th = []
#
#     for i in range(24, len(y1) + 1, 24):
#         daily_kwh_el.append(y1[(i - 24):i].sum())
#         daily_kwh_th.append(y2[(i - 24):i].sum())
#
#     daily_kwh_el_array = np.array(daily_kwh_el)
#     daily_kwh_hl_array = np.array(daily_kwh_th)
#
#     # Set up plot
#     fig, (ax1, ax2) = plt.subplots(2, sharex='all')
#     fig.suptitle('CHP Output, Daily')
#     ax1.plot(daily_kwh_el_array)
#     ax1.set_ylabel('Electrical [{}]'.format(data1[0].units))
#     ax2.plot(daily_kwh_hl_array)
#     ax2.set_ylabel('Thermal [{}]'.format(data2[0].units))
#     ax2.set_xlabel('Time (days)')
#
#     plt.show()
#
#
# def plot_tes_discharge(chp=None, demand=None, tes=None):
#     data = storage.tes_heat_stored(chp=chp, demand=demand, tes=tes)[0]
#
#     # Convert to base units before creating numpy array for plotting
#     y = np.array([status.to_base_units().magnitude for status in data])
#
#     # Calculate daily avg for discharge plot
#     daily_btu = []
#
#     for i in range(24, len(y) + 1, 24):
#         daily_btu.append(np.average(y[(i - 24):i]))
#
#     daily_btu_array = np.array(daily_btu)
#     maximum = daily_btu_array.max()
#     minimum = daily_btu_array.min()
#
#     # Set up plots
#     if maximum - minimum >= 10:
#         ytick_scale = (maximum - minimum) / 10
#     else:
#         ytick_scale = 1
#
#     plt.plot(daily_btu_array)
#     plt.title('TES Status, Daily Avg')
#     plt.ylabel('Heat [{}]'.format(data[0].units))
#     plt.yticks(np.arange(minimum, maximum, ytick_scale))
#     plt.xlabel('Time (days)')
#
#     # plot
#     plt.show()


# def plot_aux_boiler_output(chp=None, demand=None, tes=None, ab=None):
#     data = boiler.calc_aux_boiler_output(chp=chp, demand=demand, tes=tes, ab=ab)
#
#     # Convert to base units before creating numpy array for plotting
#     y = np.array([heat.to_base_units().magnitude for heat in data])
#
#     # Calculate daily sums
#     daily_btu = []
#
#     for i in range(24, len(y) + 1, 24):
#         daily_btu.append(y[(i - 24):i].sum())
#
#     daily_btu_array = np.array(daily_btu)
#     maximum = daily_btu_array.max()
#     minimum = daily_btu_array.min()
#
#     # Set up plot
#     if maximum - minimum >= 10:
#         ytick_scale = (maximum - minimum) / 10
#     else:
#         ytick_scale = 1
#
#     plt.plot(daily_btu_array)
#     plt.title('Boiler Output, Daily')
#     plt.ylabel('Heat [{}]'.format(data[0].units))
#     plt.yticks(np.arange(minimum, maximum, ytick_scale))
#     plt.xlabel('Time (days)')
#
#     # plot
#     plt.show()
