"""
Module Description:
    This module will create plots of data passed to the program
    as well as relevant data calculated by the program

TODO: Change plots to bar graphs for debugging
"""

import matplotlib.pyplot as plt, numpy as np
from lfd_package.modules import thermal_storage as storage
from lfd_package.modules import aux_boiler as boiler, chp as cogen, chp_tes_sizing as sizing


def plot_electrical_demand_curve(demand=None):
    y1 = sizing.create_demand_curve_array(demand.el)[1]
    x1 = sizing.create_demand_curve_array(demand.el)[0]

    # Set up plot
    plt.plot(x1, y1)
    plt.title('Electrical Demand Curve')
    plt.ylabel('Demand (kWh)')
    plt.yticks(np.arange(0, y1.max(), y1.max()/10))
    plt.xlabel('Percent Days')

    plt.show()


def plot_thermal_demand_curve(demand=None):
    y2 = sizing.create_demand_curve_array(demand.hl)[1]
    x2 = sizing.create_demand_curve_array(demand.hl)[0]

    # Set up plot
    plt.plot(x2, y2)
    plt.title('Thermal Demand Curve')
    plt.ylabel('Demand (Btu)')
    plt.yticks(np.arange(0, y2.max(), y2.max()/10))
    plt.xlabel('Percent Days')

    plt.show()


"""
ELF Plots
"""


def elf_plot_electric(chp=None, demand=None):
    data1 = cogen.elf_calc_electricity_bought_and_generated(chp=chp, demand=demand)[1]
    data2 = cogen.elf_calc_electricity_bought_and_generated(chp=chp, demand=demand)[0]

    # Convert to base units before creating numpy array for plotting
    y0 = np.array([dem.to_base_units().magnitude for dem in demand.el])
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
    fig.suptitle('ELF Annual Electrical Demand and Generation, Daily [kWh]')
    ax1.plot(daily_kwh_dem_array)
    ax1.set_ylabel('Demand')
    ax2.plot(daily_kwh_chp_array)
    ax2.set_ylabel('CHP')
    ax3.plot(daily_kwh_buy_array)
    ax3.set_ylabel('Electricity Bought')
    ax3.set_xlabel('Time (days)')

    plt.show()


def elf_plot_thermal(chp=None, demand=None, tes=None, ab=None):
    data1 = cogen.elf_calc_hourly_heat_generated(chp=chp, demand=demand)
    data2 = storage.calc_tes_heat_flow_and_soc(chp=chp, demand=demand, tes=tes, load_following_type="ELF")[0]
    data3 = boiler.calc_aux_boiler_output_rate(chp=chp, demand=demand, tes=tes, ab=ab, load_following_type="ELF")

    # Convert to base units before creating numpy array for plotting
    y0 = np.array([dem.to_base_units().magnitude for dem in demand.hl])
    y1 = np.array([gen.to_base_units().magnitude for gen in data1])
    y2 = np.array([gen.to_base_units().magnitude for gen in data2])
    y3 = np.array([gen.to_base_units().magnitude for gen in data3])

    # Calculate daily sums
    daily_btu_dem = []
    daily_btu_chp = []
    daily_btu_tes = []
    daily_btu_ab = []

    for i in range(24, len(y0) + 1, 24):
        daily_btu_dem.append(y0[(i - 24):i].sum())
        daily_btu_chp.append(y1[(i - 24):i].sum())
        daily_btu_tes.append(y2[(i - 24):i].sum())
        daily_btu_ab.append(y3[(i - 24):i].sum())

    daily_btu_dem_array = np.array(daily_btu_dem)
    daily_btu_chp_array = np.array(daily_btu_chp)
    daily_btu_tes_array = np.array(daily_btu_tes)
    daily_btu_ab_array = np.array(daily_btu_ab)

    # Set up plot
    fig, (ax1, ax2, ax3, ax4) = plt.subplots(1, 4, sharex='all', sharey='all')
    fig.suptitle('ELF Annual Thermal Demand and Generation, Daily [Btu]')
    ax1.plot(daily_btu_dem_array)
    ax1.set_ylabel('Demand')
    ax2.plot(daily_btu_chp_array)
    ax2.set_ylabel('CHP')
    ax3.plot(daily_btu_tes_array)
    ax3.set_ylabel('TES Discharge')
    ax4.plot(daily_btu_ab_array)
    ax4.set_ylabel('Aux Boiler')
    ax4.set_xlabel('Time (days)')

    plt.show()


def elf_plot_tes_soc(chp=None, demand=None, tes=None):
    data = storage.calc_tes_heat_flow_and_soc(chp=chp, demand=demand, tes=tes, load_following_type="ELF")[1]

    # Convert to base units before creating numpy array for plotting
    y = np.array([status.to_base_units().magnitude for status in data])

    # Calculate daily avg for discharge plot
    daily_btu = []

    for i in range(24, len(y) + 1, 24):
        daily_btu.append(np.average(y[(i - 24):i]))

    daily_btu_array = np.array(daily_btu)

    # Set up plots
    plt.plot(daily_btu_array)
    plt.title('ELF TES SOC, Daily Avg')
    plt.ylabel('SOC')
    plt.yticks(np.arange(0, 1, 0.1))
    plt.xlabel('Time (days)')

    # plot
    plt.show()


"""
TLF Plots
"""


def tlf_plot_electric(chp=None, demand=None):
    data1 = cogen.tlf_calc_electricity_bought_and_generated(chp=chp, demand=demand)[1]
    data2 = cogen.tlf_calc_electricity_bought_and_generated(chp=chp, demand=demand)[0]

    # Convert to base units before creating numpy array for plotting
    y0 = np.array([dem.to_base_units().magnitude for dem in demand.el])
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
    fig.suptitle('TLF Annual Electrical Demand and Generation, Daily [kWh]')
    ax1.plot(daily_kwh_dem_array)
    ax1.set_ylabel('Demand')
    ax2.plot(daily_kwh_chp_array)
    ax2.set_ylabel('CHP')
    ax3.plot(daily_kwh_buy_array)
    ax3.set_ylabel('Electricity Bought')
    ax3.set_xlabel('Time (days)')

    plt.show()


def tlf_plot_thermal(chp=None, demand=None, tes=None, ab=None):
    data1 = cogen.tlf_calc_hourly_heat_generated(chp=chp, demand=demand)
    data2 = storage.calc_tes_heat_flow_and_soc(chp=chp, demand=demand, tes=tes, load_following_type="TLF")[0]
    data3 = boiler.calc_aux_boiler_output_rate(chp=chp, demand=demand, tes=tes, ab=ab, load_following_type="TLF")

    # Convert to base units before creating numpy array for plotting
    y0 = np.array([dem.to_base_units().magnitude for dem in demand.hl])
    y1 = np.array([gen.to_base_units().magnitude for gen in data1])
    y2 = np.array([gen.to_base_units().magnitude for gen in data2])
    y3 = np.array([gen.to_base_units().magnitude for gen in data3])

    # Calculate daily sums
    daily_btu_dem = []
    daily_btu_chp = []
    daily_btu_tes = []
    daily_btu_ab = []

    for i in range(24, len(y0) + 1, 24):
        daily_btu_dem.append(y0[(i - 24):i].sum())
        daily_btu_chp.append(y1[(i - 24):i].sum())
        daily_btu_tes.append(y2[(i - 24):i].sum())
        daily_btu_ab.append(y3[(i - 24):i].sum())

    daily_btu_dem_array = np.array(daily_btu_dem)
    daily_btu_chp_array = np.array(daily_btu_chp)
    daily_btu_tes_array = np.array(daily_btu_tes)
    daily_btu_ab_array = np.array(daily_btu_ab)

    # Set up plot
    fig, (ax1, ax2, ax3, ax4) = plt.subplots(1, 4, sharex='all', sharey='all')
    fig.suptitle('TLF Annual Thermal Demand and Generation, Daily [Btu]')
    ax1.plot(daily_btu_dem_array)
    ax1.set_ylabel('Demand')
    ax2.plot(daily_btu_chp_array)
    ax2.set_ylabel('CHP')
    ax3.plot(daily_btu_tes_array)
    ax3.set_ylabel('TES Discharge')
    ax4.plot(daily_btu_ab_array)
    ax4.set_ylabel('Aux Boiler')
    ax4.set_xlabel('Time (days)')

    plt.show()


def tlf_plot_tes_soc(chp=None, demand=None, tes=None):
    data = storage.calc_tes_heat_flow_and_soc(chp=chp, demand=demand, tes=tes, load_following_type="TLF")[1]

    # Convert to base units before creating numpy array for plotting
    y = np.array([status.to_base_units().magnitude for status in data])

    # Calculate daily avg for discharge plot
    daily_btu = []

    for i in range(24, len(y) + 1, 24):
        daily_btu.append(np.average(y[(i - 24):i]))

    daily_btu_array = np.array(daily_btu)

    # Set up plots
    plt.plot(daily_btu_array)
    plt.title('TLF TES SOC, Daily Avg')
    plt.ylabel('SOC')
    plt.yticks(np.arange(0, 1, 0.1))
    plt.xlabel('Time (days)')

    # plot
    plt.show()
