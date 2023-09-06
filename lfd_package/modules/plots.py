"""
Module Description:
    This module will create plots of data passed to the program
    as well as relevant data calculated by the program
"""

import matplotlib.pyplot as plt
import numpy as np
import pathlib
from lfd_package.modules import sizing_calcs as sizing
from lfd_package.modules.__init__ import ureg


def plot_max_rectangle_electric(demand_class=None, chp_size=None):
    el_demand = demand_class.el.to(ureg.kW)
    y1 = sizing.create_demand_curve_array(el_demand)[1].magnitude
    x1 = sizing.create_demand_curve_array(el_demand)[0]

    y2_value = chp_size.magnitude
    y2_index = min(range(len(y1)), key=lambda i: abs(y1[i] - y2_value))
    x2_value = x1[y2_index]

    # Set up plot
    plt.plot(x1, y1, label='Electrical Demand Curve')
    plt.vlines(x=x2_value, colors='purple', ymin=0, ymax=y2_value, linestyles='--')
    plt.plot((0, x2_value), (y2_value, y2_value), color='purple', label='Max Rectangle CHP Size', linestyle='--')
    plt.ylabel('Demand (kW)')
    annual_sum = sum(el_demand)
    if annual_sum.magnitude <= 1:
        plt.yticks(np.arange(0, 10, 1))
    else:
        plt.yticks(np.arange(0, y1.max(), y1.max()/10))
    plt.xlabel('Percent Hours')
    plt.legend()

    file_path = pathlib.Path(__file__).parent.parent.resolve() / "plots/{}_{}".format(demand_class.city,
                                                                                      demand_class.state) / \
                "{}_{}_MR_size_thermal.png".format(demand_class.city, demand_class.state)
    if file_path.is_file():
        pathlib.Path.unlink(file_path)
    plt.savefig(file_path, dpi=900)

    plt.show()


def plot_max_rectangle_thermal(demand_class=None, chp_size=None):
    th_demand = demand_class.hl.to(ureg.kW)
    y1 = sizing.create_demand_curve_array(th_demand)[1].magnitude
    x1 = sizing.create_demand_curve_array(th_demand)[0]

    y2_value = sizing.electrical_output_to_thermal_output(chp_size).magnitude
    y2_index = min(range(len(y1)), key=lambda i: abs(y1[i] - y2_value))
    x2_value = x1[y2_index]

    # Set up plot
    plt.plot(x1, y1, label='Thermal Demand Curve')
    plt.vlines(x=x2_value, colors='purple', ymin=0, ymax=y2_value, linestyles='--')
    plt.plot((0, x2_value), (y2_value, y2_value), color='purple', label='Max Rectangle CHP Size', linestyle='--')
    plt.ylabel('Demand (kW)')
    annual_sum = sum(th_demand)
    if annual_sum.magnitude <= 1:
        plt.yticks(np.arange(0, 10, 1))
    else:
        plt.yticks(np.arange(0, y1.max(), y1.max() / 10))
    plt.xlabel('Percent Hours')
    plt.legend()

    file_path = pathlib.Path(__file__).parent.parent.resolve() / "plots/{}_{}".format(demand_class.city,
                                                                                      demand_class.state) / \
                "{}_{}_MR_size_electrical.png".format(demand_class.city, demand_class.state)
    if file_path.is_file():
        pathlib.Path.unlink(file_path)
    plt.savefig(file_path, dpi=900)

    plt.show()


def plot_electrical_demand_curve(demand_class=None):
    el_demand = demand_class.el.to(ureg.kW)
    y1 = sizing.create_demand_curve_array(el_demand)[1].magnitude
    x1 = sizing.create_demand_curve_array(el_demand)[0]

    # Set up plot
    plt.plot(x1, y1)
    plt.title('Electrical Demand Curve')
    plt.ylabel('Demand (kW)')
    annual_sum = sum(el_demand)
    if annual_sum.magnitude <= 1:
        plt.yticks(np.arange(0, 10, 1))
    else:
        plt.yticks(np.arange(0, y1.max(), y1.max()/10))
    plt.xlabel('Percent Hours')

    file_path = pathlib.Path(__file__).parent.parent.resolve() / "plots/{}_{}".format(demand_class.city,
                                                                                      demand_class.state) / \
                "{}_{}_electrical_demand.png".format(demand_class.city, demand_class.state)
    if file_path.is_file():
        pathlib.Path.unlink(file_path)
    plt.savefig(file_path, dpi=900)

    plt.show()


def plot_thermal_demand_curve(demand_class=None):
    hl_demand = demand_class.hl.to(ureg.Btu / ureg.hours)
    y2 = sizing.create_demand_curve_array(hl_demand)[1].magnitude
    x2 = sizing.create_demand_curve_array(hl_demand)[0]

    # Set up plot
    plt.plot(x2, y2)
    plt.title('Thermal Demand Curve')
    plt.ylabel('Demand (Btu/hr)')
    annual_sum = sum(hl_demand)
    if annual_sum.magnitude <= 1:
        plt.yticks(np.arange(0, 10, 1))
    else:
        plt.yticks(np.arange(0, y2.max(), y2.max()/10))
    plt.xlabel('Percent Hours')

    file_path = pathlib.Path(__file__).parent.parent.resolve() / "plots/{}_{}".format(demand_class.city,
                                                                                      demand_class.state) / \
                "{}_{}_thermal_demand.png".format(demand_class.city, demand_class.state)
    if file_path.is_file():
        pathlib.Path.unlink(file_path)
    plt.savefig(file_path, dpi=900)

    plt.show()


"""
ELF Plots
"""


def elf_plot_electric(elf_electric_gen_list=None, elf_electricity_bought_list=None, demand_class=None):
    data0 = demand_class.el.to(ureg.kW)
    data1 = elf_electric_gen_list
    data2 = elf_electricity_bought_list

    # Convert to base units before creating numpy array for plotting
    y0 = np.array(data0.magnitude)
    y1 = np.array([gen.magnitude for gen in data1])
    y2 = np.array([gen.magnitude for gen in data2])

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
    fig.suptitle('ELF Electrical Demand and Generation, Daily Avg [kW]')
    ax1.plot(daily_kwh_dem_array)
    ax1.set_ylabel('Demand')
    ax2.plot(daily_kwh_chp_array)
    ax2.set_ylabel('CHP')
    ax3.plot(daily_kwh_buy_array)
    ax3.set_ylabel('Electricity Bought')
    ax3.set_xlabel('Time (days)')

    file_path = pathlib.Path(__file__).parent.parent.resolve() / "plots/{}_{}".format(demand_class.city,
                                                                                      demand_class.state) / \
                "{}_{}_elf_plot_electric.png".format(demand_class.city, demand_class.state)
    if file_path.is_file():
        pathlib.Path.unlink(file_path)
    plt.savefig(file_path, dpi=900)

    plt.show()


def elf_plot_thermal(elf_chp_gen_btuh=None, elf_tes_heat_flow_list=None, elf_boiler_dispatch_hourly=None, demand_class=None):
    data1 = elf_chp_gen_btuh
    data2 = elf_tes_heat_flow_list
    data3 = elf_boiler_dispatch_hourly
    hl_demand = demand_class.hl.to(ureg.Btu / ureg.hours)

    # Convert to base units before creating numpy array for plotting
    y0 = np.array([dem.magnitude for dem in hl_demand])
    y1 = np.array([gen.magnitude for gen in data1])
    y2 = np.array([gen.magnitude for gen in data2])
    y3 = np.array([gen.magnitude for gen in data3])

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
    fig.suptitle('ELF Thermal Demand and Generation, Daily Avg [Btu/hr]')
    ax1.plot(daily_btu_dem_array)
    ax1.set_ylabel('Demand')
    ax2.plot(daily_btu_chp_array)
    ax2.set_ylabel('CHP')
    ax3.plot(daily_btu_tes_array)
    ax3.set_ylabel('TES Discharge')
    ax4.plot(daily_btu_ab_array)
    ax4.set_ylabel('Aux Boiler')
    ax4.set_xlabel('Time (days)')

    file_path = pathlib.Path(__file__).parent.parent.resolve() / "plots/{}_{}".format(demand_class.city,
                                                                                      demand_class.state) / \
                "{}_{}_elf_plot_thermal.png".format(demand_class.city, demand_class.state)
    if file_path.is_file():
        pathlib.Path.unlink(file_path)
    plt.savefig(file_path, dpi=900)

    plt.show()


def elf_plot_tes_soc(elf_tes_soc=None, demand_class=None):
    data = elf_tes_soc

    # Convert to base units before creating numpy array for plotting
    y = np.array([status.magnitude for status in data])

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

    file_path = pathlib.Path(__file__).parent.parent.resolve() / "plots/{}_{}".format(demand_class.city,
                                                                                      demand_class.state) / \
                "{}_{}_elf_plot_soc.png".format(demand_class.city, demand_class.state)
    if file_path.is_file():
        pathlib.Path.unlink(file_path)
    plt.savefig(file_path, dpi=900)

    plt.show()


"""
TLF Plots
"""


def tlf_plot_electric(tlf_electric_gen_list=None, tlf_electricity_bought_list=None, demand_class=None):
    data0 = demand_class.el.to(ureg.kW)
    data1 = tlf_electric_gen_list
    data2 = tlf_electricity_bought_list

    # Convert to base units before creating numpy array for plotting
    y0 = np.array(data0.magnitude)
    y1 = np.array([gen.magnitude for gen in data1])
    y2 = np.array([gen.magnitude for gen in data2])

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
    fig.suptitle('TLF Electrical Demand and Generation, Daily Avg [kW]')
    ax1.plot(daily_kwh_dem_array)
    ax1.set_ylabel('Demand')
    ax2.plot(daily_kwh_chp_array)
    ax2.set_ylabel('CHP')
    ax3.plot(daily_kwh_buy_array)
    ax3.set_ylabel('Electricity Bought')
    ax3.set_xlabel('Time (days)')

    file_path = pathlib.Path(__file__).parent.parent.resolve() / "plots/{}_{}".format(demand_class.city,
                                                                                      demand_class.state) / \
                "{}_{}_tlf_plot_electric.png".format(demand_class.city, demand_class.state)
    if file_path.is_file():
        pathlib.Path.unlink(file_path)
    plt.savefig(file_path, dpi=900)

    plt.show()


# TODO: Make so thermal demand of all zeros produces properly scaled plot
def tlf_plot_thermal(tlf_chp_gen_btuh=None, tlf_tes_heat_flow_list=None, tlf_boiler_dispatch_hourly=None,
                     demand_class=None):
    data1 = tlf_chp_gen_btuh
    data2 = tlf_tes_heat_flow_list
    data3 = tlf_boiler_dispatch_hourly
    hl_demand = demand_class.hl.to(ureg.Btu / ureg.hours)

    # Check units
    assert data1[100].units == ureg.Btu / ureg.hours
    assert data2[100].units == ureg.Btu / ureg.hours
    assert data3[100].units == ureg.Btu / ureg.hours

    # Convert to base units before creating numpy array for plotting
    y0 = np.array([dem.magnitude for dem in hl_demand])
    y1 = np.array([gen.magnitude for gen in data1])
    y2 = np.array([gen.magnitude for gen in data2])
    y3 = np.array([gen.magnitude for gen in data3])

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
    fig.suptitle('TLF Thermal Demand and Generation, Daily Avg [Btu/hr]')
    ax1.plot(daily_btu_dem_array)
    ax1.set_ylabel('Demand')
    ax2.plot(daily_btu_chp_array)
    ax2.set_ylabel('CHP')
    ax3.plot(daily_btu_tes_array)
    ax3.set_ylabel('TES Discharge')
    ax4.plot(daily_btu_ab_array)
    ax4.set_ylabel('Aux Boiler')
    ax4.set_xlabel('Time (days)')

    file_path = pathlib.Path(__file__).parent.parent.resolve() / "plots/{}_{}".format(demand_class.city,
                                                                                      demand_class.state) / \
                "{}_{}_tlf_plot_thermal.png".format(demand_class.city, demand_class.state)
    if file_path.is_file():
        pathlib.Path.unlink(file_path)
    plt.savefig(file_path, dpi=900)

    plt.show()


def tlf_plot_tes_soc(tlf_tes_soc_list=None, demand_class=None):
    data = tlf_tes_soc_list   # TES SOC data

    # Convert to base units before creating numpy array for plotting
    y = np.array([status.magnitude for status in data])

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

    file_path = pathlib.Path(__file__).parent.parent.resolve() / "plots/{}_{}".format(demand_class.city,
                                                                                      demand_class.state) / \
                "{}_{}_tlf_plot_soc.png".format(demand_class.city, demand_class.state)
    if file_path.is_file():
        pathlib.Path.unlink(file_path)
    plt.savefig(file_path, dpi=900)

    plt.show()


"""
PP PES Plots
"""


def pp_plot_electric(pp_electric_gen_list=None, pp_electricity_bought_list=None, pp_electricity_sold_list=None,
                     demand_class=None):
    data0 = demand_class.el.to(ureg.kW)
    data1 = pp_electric_gen_list
    data2 = pp_electricity_bought_list
    data3 = pp_electricity_sold_list

    # Convert to base units before creating numpy array for plotting
    y0 = np.array(data0.magnitude)
    y1 = np.array([gen.magnitude for gen in data1])
    y2 = np.array([buy.magnitude for buy in data2])
    y3 = np.array([sell.magnitude for sell in data3])

    # Calculate daily sums
    daily_kwh_dem = []
    daily_kwh_chp = []
    daily_kwh_buy = []
    daily_kwh_sold = []

    for i in range(24, len(y0) + 1, 24):
        daily_kwh_dem.append(y0[(i - 24):i].sum())
        daily_kwh_chp.append(y1[(i - 24):i].sum())
        daily_kwh_buy.append(y2[(i - 24):i].sum())
        daily_kwh_sold.append(y3[(i - 24):i].sum())

    daily_kwh_dem_array = np.array(daily_kwh_dem)
    daily_kwh_chp_array = np.array(daily_kwh_chp)
    daily_kwh_buy_array = np.array(daily_kwh_buy)
    daily_kwh_sell_array = np.array(daily_kwh_sold)

    # Set up plot
    fig, (ax1, ax2, ax3, ax4) = plt.subplots(1, 4, sharex='all', sharey='all')
    fig.suptitle('PP (PES CHP Size) Electrical Demand, Generation, and Exports, Daily Aveg [kW]')
    ax1.plot(daily_kwh_dem_array)
    ax1.set_ylabel('Demand')
    ax2.plot(daily_kwh_chp_array)
    ax2.set_ylabel('CHP')
    ax3.plot(daily_kwh_buy_array)
    ax3.set_ylabel('Electricity Bought')
    ax4.plot(daily_kwh_sell_array)
    ax4.set_ylabel('Electricity Sold')
    ax4.set_xlabel('Time (days)')

    file_path = pathlib.Path(__file__).parent.parent.resolve() / "plots/{}_{}".format(demand_class.city,
                                                                                      demand_class.state) / \
                "{}_{}_pp_plot_electric.png".format(demand_class.city, demand_class.state)
    if file_path.is_file():
        pathlib.Path.unlink(file_path)
    plt.savefig(file_path, dpi=900)

    plt.show()


def pp_plot_thermal(pp_chp_gen_btuh=None, pp_tes_heat_flow_list=None, pp_boiler_dispatch_hourly=None,
                    demand_class=None):
    data1 = pp_chp_gen_btuh
    data2 = pp_tes_heat_flow_list
    data3 = pp_boiler_dispatch_hourly
    hl_demand = demand_class.hl.to(ureg.Btu / ureg.hours)

    # Convert to base units before creating numpy array for plotting
    y0 = np.array([dem.magnitude for dem in hl_demand])
    y1 = np.array([gen.magnitude for gen in data1])
    y2 = np.array([tes.magnitude for tes in data2])
    y3 = np.array([boil.magnitude for boil in data3])

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
    fig.suptitle('PP (PES CHP Size) Thermal Demand and Generation, Daily Avg [Btu/hr]')
    ax1.plot(daily_btu_dem_array)
    ax1.set_ylabel('Demand')
    ax2.plot(daily_btu_chp_array)
    ax2.set_ylabel('CHP')
    ax3.plot(daily_btu_tes_array)
    ax3.set_ylabel('TES Discharge')
    ax4.plot(daily_btu_ab_array)
    ax4.set_ylabel('Aux Boiler')
    ax4.set_xlabel('Time (days)')

    file_path = pathlib.Path(__file__).parent.parent.resolve() / "plots/{}_{}".format(demand_class.city,
                                                                                      demand_class.state) / \
                "{}_{}_pp_plot_thermal.png".format(demand_class.city, demand_class.state)
    if file_path.is_file():
        pathlib.Path.unlink(file_path)
    plt.savefig(file_path, dpi=900)

    plt.show()


def pp_plot_tes_soc(pp_tes_soc=None, demand_class=None):
    data = pp_tes_soc

    # Convert to base units before creating numpy array for plotting
    y = np.array([status.magnitude for status in data])

    # Calculate daily avg for discharge plot
    daily_btu = []

    for i in range(24, len(y) + 1, 24):
        daily_btu.append(np.average(y[(i - 24):i]))

    daily_btu_array = np.array(daily_btu)

    # Set up plots
    plt.plot(daily_btu_array)
    plt.title('PP (PES CHP Size) TES SOC, Daily Avg')
    plt.ylabel('SOC')
    plt.yticks(np.arange(0, 1, 0.1))
    plt.xlabel('Time (days)')

    file_path = pathlib.Path(__file__).parent.parent.resolve() / "plots/{}_{}".format(demand_class.city,
                                                                                      demand_class.state) / \
                "{}_{}_pp_plot_soc.png".format(demand_class.city, demand_class.state)
    if file_path.is_file():
        pathlib.Path.unlink(file_path)
    plt.savefig(file_path, dpi=900)

    plt.show()


"""
PP Peak Plots
"""


def peak_plot_electric(peak_electric_gen_list=None, peak_electricity_bought_list=None, peak_electricity_sold_list=None,
                       demand_class=None):
    data0 = demand_class.el.to(ureg.kW)
    data1 = peak_electric_gen_list
    data2 = peak_electricity_bought_list
    data3 = peak_electricity_sold_list

    # Convert to base units before creating numpy array for plotting
    y0 = np.array(data0.magnitude)
    y1 = np.array([gen.magnitude for gen in data1])
    y2 = np.array([buy.magnitude for buy in data2])
    y3 = np.array([sell.magnitude for sell in data3])

    # Calculate daily sums
    daily_kwh_dem = []
    daily_kwh_chp = []
    daily_kwh_buy = []
    daily_kwh_sold = []

    for i in range(24, len(y0) + 1, 24):
        daily_kwh_dem.append(y0[(i - 24):i].sum())
        daily_kwh_chp.append(y1[(i - 24):i].sum())
        daily_kwh_buy.append(y2[(i - 24):i].sum())
        daily_kwh_sold.append(y3[(i - 24):i].sum())

    daily_kwh_dem_array = np.array(daily_kwh_dem)
    daily_kwh_chp_array = np.array(daily_kwh_chp)
    daily_kwh_buy_array = np.array(daily_kwh_buy)
    daily_kwh_sell_array = np.array(daily_kwh_sold)

    # Set up plot
    fig, (ax1, ax2, ax3, ax4) = plt.subplots(1, 4, sharex='all', sharey='all')
    fig.suptitle('PP (Peak CHP Size) Electrical Demand, Generation, and Exports, Daily Avg [kW]')
    ax1.plot(daily_kwh_dem_array)
    ax1.set_ylabel('Demand')
    ax2.plot(daily_kwh_chp_array)
    ax2.set_ylabel('CHP')
    ax3.plot(daily_kwh_buy_array)
    ax3.set_ylabel('Electricity Bought')
    ax4.plot(daily_kwh_sell_array)
    ax4.set_ylabel('Electricity Sold')
    ax4.set_xlabel('Time (days)')

    file_path = pathlib.Path(__file__).parent.parent.resolve() / "plots/{}_{}".format(demand_class.city,
                                                                                      demand_class.state) / \
                "{}_{}_peak_plot_electric.png".format(demand_class.city, demand_class.state)
    if file_path.is_file():
        pathlib.Path.unlink(file_path)
    plt.savefig(file_path, dpi=900)

    plt.show()


def peak_plot_thermal(peak_chp_gen_btuh=None, peak_tes_heat_flow_list=None, peak_boiler_dispatch_hourly=None,
                      demand_class=None):
    data1 = peak_chp_gen_btuh
    data2 = peak_tes_heat_flow_list
    data3 = peak_boiler_dispatch_hourly
    hl_demand = demand_class.hl.to(ureg.Btu / ureg.hours)

    # Convert to base units before creating numpy array for plotting
    y0 = np.array([dem.magnitude for dem in hl_demand])
    y1 = np.array([gen.magnitude for gen in data1])
    y2 = np.array([tes.magnitude for tes in data2])
    y3 = np.array([boil.magnitude for boil in data3])

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
    fig.suptitle('PP (Peak CHP Size) Thermal Demand and Generation, Daily Avg [Btu/hr]')
    ax1.plot(daily_btu_dem_array)
    ax1.set_ylabel('Demand')
    ax2.plot(daily_btu_chp_array)
    ax2.set_ylabel('CHP')
    ax3.plot(daily_btu_tes_array)
    ax3.set_ylabel('TES Discharge')
    ax4.plot(daily_btu_ab_array)
    ax4.set_ylabel('Aux Boiler')
    ax4.set_xlabel('Time (days)')

    file_path = pathlib.Path(__file__).parent.parent.resolve() / "plots/{}_{}".format(demand_class.city,
                                                                                      demand_class.state) / \
                "{}_{}_peak_plot_thermal.png".format(demand_class.city, demand_class.state)
    if file_path.is_file():
        pathlib.Path.unlink(file_path)
    plt.savefig(file_path, dpi=900)

    plt.show()


def peak_plot_tes_soc(peak_tes_soc=None, demand_class=None):
    data = peak_tes_soc

    # Convert to base units before creating numpy array for plotting
    y = np.array([status.magnitude for status in data])

    # Calculate daily avg for discharge plot
    daily_btu = []

    for i in range(24, len(y) + 1, 24):
        daily_btu.append(np.average(y[(i - 24):i]))

    daily_btu_array = np.array(daily_btu)

    # Set up plots
    plt.plot(daily_btu_array)
    plt.title('PP (Peak CHP Size) TES SOC, Daily Avg')
    plt.ylabel('SOC')
    plt.yticks(np.arange(0, 1, 0.1))
    plt.xlabel('Time (days)')

    file_path = pathlib.Path(__file__).parent.parent.resolve() / "plots/{}_{}".format(demand_class.city,
                                                                                      demand_class.state) / \
                "{}_{}_peak_plot_soc.png".format(demand_class.city, demand_class.state)
    if file_path.is_file():
        pathlib.Path.unlink(file_path)
    plt.savefig(file_path, dpi=900)

    plt.show()
