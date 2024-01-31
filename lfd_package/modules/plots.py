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
    """
    Uses thermal demand curve to graphically display the Maximum Rectangle CHP size.

    """
    args_list = [demand_class, chp_size]
    if any(elem is None for elem in args_list) is False:
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
    """
    Uses thermal demand curve to graphically display the Maximum Rectangle CHP size.

    """
    args_list = [demand_class, chp_size]
    if any(elem is None for elem in args_list) is False:
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
    """
    Orders the hourly electrical demand from the largest values to the smallest values with percent days on the
    x-axis. From these values, plots the electrical demand curve. Demand values from the EnergyDemand class are used.
    Plot is saved in the /plots folder for future use.

    Parameters
    ----------
    demand_class: EnergyDemand class
        contains initialized EnergyDemand class from command_line.py

    """
    if demand_class is not None:
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
    """
    Orders the hourly thermal demand from the largest values to the smallest values with percent days on the
    x-axis. From these values, plots the thermal demand curve. Demand values from the EnergyDemand class are used.
    Plot is saved in the /plots folder for future use.

    Parameters
    ----------
    demand_class: EnergyDemand class
        contains initialized EnergyDemand class from command_line.py

    """
    if demand_class is not None:
        hl_demand = demand_class.hl.to(ureg.kW)
        y2 = sizing.create_demand_curve_array(hl_demand)[1].magnitude
        x2 = sizing.create_demand_curve_array(hl_demand)[0]

        # Set up plot
        plt.plot(x2, y2)
        plt.title('Thermal Demand Curve')
        plt.ylabel('Demand (kW)')
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
    """
    Plots the daily sums of the CHP electricity generated and electricity bought from the grid for
    ELF operation mode. Plot is saved to the /plots folder for future use.

    Parameters
    ----------
    elf_electric_gen_list: list
        contains hourly CHP electricity generated in units of kWh.
    elf_electricity_bought_list: list
        contains hourly electricity bought form the grid in units of kWh.
    demand_class: EnergyDemand class
        contains initialized EnergyDemand class from command_line.py

    """
    args_list = [elf_electric_gen_list, elf_electricity_bought_list, demand_class]
    if any(elem is None for elem in args_list) is False:
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
        fig.suptitle('ELF Electrical Demand and Generation, Daily Sums')
        ax1.plot(daily_kwh_dem_array)
        ax1.set_ylabel('Demand (kWh)')
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
    """
    Plots the daily sums of CHP thermal generation, boiler thermal output, and TES heat flows (kW) for ELF operation
    mode. Includes negative and positive heat flow values, with negative discharging convention. Plot is saved to
    the /plots folder for future use.

    Parameters
    ----------
    elf_chp_gen_btuh: list
        contains hourly CHP heat generation in units of Btu/hr.
    elf_tes_heat_flow_list: list
        contains hourly TES heat flow values in units of Btu/hr.
    elf_boiler_dispatch_hourly: list
        contains hourly boiler heat dispatch in units of Btu/hr
    demand_class: EnergyDemand class
        contains initialized EnergyDemand class from command_line.py
    """
    args_list = [elf_chp_gen_btuh, elf_tes_heat_flow_list, elf_boiler_dispatch_hourly, demand_class]
    if any(elem is None for elem in args_list) is False:
        data1 = []
        data2 = []
        data3 = []
        for index, item in enumerate(elf_chp_gen_btuh):
            data1.append(item.to(ureg.kW))
            # For TES, append only negative values (discharging)
            if elf_tes_heat_flow_list[index].magnitude <= 0:
                data2.append(-1 * elf_tes_heat_flow_list[index].to(ureg.kW))
            else:
                data2.append(0 * ureg.kW)
            data3.append(elf_boiler_dispatch_hourly[index].to(ureg.kW))
        hl_demand = demand_class.hl.to(ureg.kW)

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
        fig.suptitle('ELF Thermal Demand and Generation, Daily Sums')
        ax1.plot(daily_btu_dem_array)
        ax1.set_ylabel('Demand (kWh)')
        ax2.plot(daily_btu_chp_array)
        ax2.set_ylabel('CHP (kWh)')
        ax3.plot(daily_btu_tes_array)
        ax3.set_ylabel('TES Discharge (kWh)')
        ax4.plot(daily_btu_ab_array)
        ax4.set_ylabel('Aux Boiler (kWh)')
        ax4.set_xlabel('Time (days)')

        file_path = pathlib.Path(__file__).parent.parent.resolve() / "plots/{}_{}".format(demand_class.city,
                                                                                          demand_class.state) / \
                    "{}_{}_elf_plot_thermal.png".format(demand_class.city, demand_class.state)
        if file_path.is_file():
            pathlib.Path.unlink(file_path)
        plt.savefig(file_path, dpi=900)

        plt.show()


def elf_plot_tes_soc(elf_tes_soc=None, demand_class=None):
    """
    Plots the average TES SOC values for the ELF operating mode. Plot is saved to the /plots folder for future use.

    Parameters
    ----------
    elf_tes_soc: list
        contains hourly TES SOC values for the ELF operating mode
    demand_class: EnergyDemand class
        contains initialized EnergyDemand class from command_line.py

    """
    args_list = [elf_tes_soc, demand_class]
    if any(elem is None for elem in args_list) is False:
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


def tlf_plot_electric(tlf_electric_gen_list=None, tlf_electricity_bought_list=None, tlf_electricity_sold_list=None,
                      demand_class=None):
    """
    Plots the daily sums of the CHP electricity generated, electricity bought, and electricity sold to the grid for
    TLF operation mode. Plot is saved to the /plots folder for future use.

    Parameters
    ----------
    tlf_electric_gen_list: list
        contains hourly CHP electricity generated in units of kWh.
    tlf_electricity_bought_list: list
        contains hourly electricity bought form the grid in units of kWh.
    tlf_electricity_sold_list: list
        contains hourly electricity sold to the grid in units of kWh.
    demand_class: EnergyDemand class
        contains initialized EnergyDemand class from command_line.py

    """
    args_list = [tlf_electric_gen_list, tlf_electricity_bought_list, tlf_electricity_sold_list, demand_class]
    if any(elem is None for elem in args_list) is False:
        data0 = demand_class.el.to(ureg.kW)
        data1 = tlf_electric_gen_list
        data2 = tlf_electricity_bought_list
        data3 = tlf_electricity_sold_list

        # Convert to base units before creating numpy array for plotting
        y0 = np.array(data0.magnitude)
        y1 = np.array([gen.magnitude for gen in data1])
        y2 = np.array([buy.magnitude for buy in data2])
        y3 = np.array([sell.magnitude for sell in data3])

        # Calculate daily sums
        daily_kwh_dem = []
        daily_kwh_chp = []
        daily_kwh_buy = []
        daily_kwh_sell = []

        for i in range(24, len(y0) + 1, 24):
            daily_kwh_dem.append(y0[(i - 24):i].sum())
            daily_kwh_chp.append(y1[(i - 24):i].sum())
            daily_kwh_buy.append(y2[(i - 24):i].sum())
            daily_kwh_sell.append(y3[(i - 24):i].sum())

        daily_kwh_dem_array = np.array(daily_kwh_dem)
        daily_kwh_chp_array = np.array(daily_kwh_chp)
        daily_kwh_buy_array = np.array(daily_kwh_buy)
        daily_kwh_sell_array = np.array(daily_kwh_sell)

        # Set up plot
        fig, (ax1, ax2, ax3, ax4) = plt.subplots(1, 4, sharex='all', sharey='all')
        fig.suptitle('TLF Electrical Demand, Generation, and Exports, Daily Sums')
        ax1.plot(daily_kwh_dem_array)
        ax1.set_ylabel('Demand (kWh)')
        ax2.plot(daily_kwh_chp_array)
        ax2.set_ylabel('CHP (kWh)')
        ax3.plot(daily_kwh_buy_array)
        ax3.set_ylabel('Electricity Bought (kWh)')
        ax4.plot(daily_kwh_sell_array)
        ax4.set_ylabel('Electricity Sold (kWh)')
        ax3.set_xlabel('Time (days)')

        file_path = pathlib.Path(__file__).parent.parent.resolve() / "plots/{}_{}".format(demand_class.city,
                                                                                          demand_class.state) / \
                    "{}_{}_tlf_plot_electric.png".format(demand_class.city, demand_class.state)
        if file_path.is_file():
            pathlib.Path.unlink(file_path)
        plt.savefig(file_path, dpi=900)

        plt.show()


def tlf_plot_thermal(tlf_chp_gen_btuh=None, tlf_tes_heat_flow_list=None, tlf_boiler_dispatch_hourly=None,
                     demand_class=None):
    """
    Plots the daily sums of CHP thermal generation, boiler thermal output, and TES heat flows (kW) for TLF operation
    mode. Includes negative and positive heat flow values, with negative discharging convention. Plot is saved to
    the /plots folder for future use.

    Parameters
    ----------
    tlf_chp_gen_btuh: list
        contains hourly CHP heat generation in units of Btu/hr.
    tlf_tes_heat_flow_list: list
        contains hourly TES heat flow values in units of Btu/hr.
    tlf_boiler_dispatch_hourly: list
        contains hourly boiler heat dispatch in units of Btu/hr
    demand_class: EnergyDemand class
        contains initialized EnergyDemand class from command_line.py

    """
    args_list = [tlf_chp_gen_btuh, tlf_tes_heat_flow_list, tlf_boiler_dispatch_hourly, demand_class]
    if any(elem is None for elem in args_list) is False:
        data1 = []
        data2 = []
        data3 = []
        for index, item in enumerate(tlf_chp_gen_btuh):
            data1.append(item.to(ureg.kW))
            # For TES, append only negative values (discharging)
            if tlf_tes_heat_flow_list[index].magnitude <= 0:
                data2.append(-1 * tlf_tes_heat_flow_list[index].to(ureg.kW))
            else:
                data2.append(0 * ureg.kW)
            data3.append(tlf_boiler_dispatch_hourly[index].to(ureg.kW))
        hl_demand = demand_class.hl.to(ureg.kW)

        # Check units
        assert data1[100].units == ureg.kW
        assert data2[100].units == ureg.kW
        assert data3[100].units == ureg.kW

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
        fig.suptitle('TLF Thermal Demand and Generation, Daily Sums')
        ax1.plot(daily_btu_dem_array)
        ax1.set_ylabel('Demand (kWh)')
        ax2.plot(daily_btu_chp_array)
        ax2.set_ylabel('CHP (kWh)')
        ax3.plot(daily_btu_tes_array)
        ax3.set_ylabel('TES Discharge (kWh)')
        ax4.plot(daily_btu_ab_array)
        ax4.set_ylabel('Aux Boiler (kWh)')
        ax4.set_xlabel('Time (days)')

        file_path = pathlib.Path(__file__).parent.parent.resolve() / "plots/{}_{}".format(demand_class.city,
                                                                                          demand_class.state) / \
                    "{}_{}_tlf_plot_thermal.png".format(demand_class.city, demand_class.state)
        if file_path.is_file():
            pathlib.Path.unlink(file_path)
        plt.savefig(file_path, dpi=900)

        plt.show()


def tlf_plot_tes_soc(tlf_tes_soc_list=None, demand_class=None):
    """
    Plots the average TES SOC values for the TLF operating mode. Plot is saved to the /plots folder for future use.

    Parameters
    ----------
    tlf_tes_soc_list: list
        contains hourly TES SOC values for the TLF operating mode
    demand_class: EnergyDemand class
        contains initialized EnergyDemand class from command_line.py

    """
    args_list = [tlf_tes_soc_list, demand_class]
    if any(elem is None for elem in args_list) is False:
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
PP Peak Plots
"""


def peak_plot_electric(peak_electric_gen_list=None, peak_electricity_bought_list=None, peak_electricity_sold_list=None,
                       demand_class=None):
    """
    Plots the daily sums of the CHP electricity generated, electricity bought, and electricity sold to the grid for
    PP operation mode. Plot is saved to the /plots folder for future use.

    Parameters
    ----------
    peak_electric_gen_list: list
        contains hourly CHP electricity generated in units of kWh.
    peak_electricity_bought_list: list
        contains hourly electricity bought form the grid in units of kWh.
    peak_electricity_sold_list: list
        contains hourly electricity sold to the grid in units of kWh.
    demand_class: EnergyDemand class
        contains initialized EnergyDemand class from command_line.py

    """
    args_list = [peak_electric_gen_list, peak_electricity_bought_list, peak_electricity_sold_list, demand_class]
    if any(elem is None for elem in args_list) is False:
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
        fig.suptitle('PP Electrical Demand, Generation, and Exports, Daily Sums')
        ax1.plot(daily_kwh_dem_array)
        ax1.set_ylabel('Demand (kWh)')
        ax2.plot(daily_kwh_chp_array)
        ax2.set_ylabel('CHP (kWh)')
        ax3.plot(daily_kwh_buy_array)
        ax3.set_ylabel('Electricity Bought (kWh)')
        ax4.plot(daily_kwh_sell_array)
        ax4.set_ylabel('Electricity Sold (kWh)')
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
    """
    Plots the daily sums of CHP thermal generation, boiler thermal output, and TES heat flows (kW) for PP operation
    mode. Includes negative and positive heat flow values, with negative discharging convention. Plot is saved to
    the /plots folder for future use.

    Parameters
    ----------
    peak_chp_gen_btuh: list
        contains hourly CHP heat generation in units of Btu/hr.
    peak_tes_heat_flow_list: list
        contains hourly TES heat flow values in units of Btu/hr.
    peak_boiler_dispatch_hourly: list
        contains hourly boiler heat dispatch in units of Btu/hr
    demand_class: EnergyDemand class
        contains initialized EnergyDemand class from command_line.py

    """
    args_list = [peak_chp_gen_btuh, peak_tes_heat_flow_list, peak_boiler_dispatch_hourly, demand_class]
    if any(elem is None for elem in args_list) is False:
        data1 = []
        data2 = []
        data3 = []
        for index, item in enumerate(peak_chp_gen_btuh):
            data1.append(item.to(ureg.kW))
            # For TES, append only negative values (discharging)
            if peak_tes_heat_flow_list[index].magnitude <= 0:
                data2.append(-1 * peak_tes_heat_flow_list[index].to(ureg.kW))
            else:
                data2.append(0 * ureg.kW)
            data3.append(peak_boiler_dispatch_hourly[index].to(ureg.kW))
        hl_demand = demand_class.hl.to(ureg.kW)

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
        fig.suptitle('PP Thermal Demand and Generation, Daily Sums')
        ax1.plot(daily_btu_dem_array)
        ax1.set_ylabel('Demand (kWh)')
        ax2.plot(daily_btu_chp_array)
        ax2.set_ylabel('CHP (kWh)')
        ax3.plot(daily_btu_tes_array)
        ax3.set_ylabel('TES Discharge (kWh)')
        ax4.plot(daily_btu_ab_array)
        ax4.set_ylabel('Aux Boiler (kWh)')
        ax4.set_xlabel('Time (days)')

        file_path = pathlib.Path(__file__).parent.parent.resolve() / "plots/{}_{}".format(demand_class.city,
                                                                                          demand_class.state) / \
                    "{}_{}_peak_plot_thermal.png".format(demand_class.city, demand_class.state)
        if file_path.is_file():
            pathlib.Path.unlink(file_path)
        plt.savefig(file_path, dpi=900)

        plt.show()


def peak_plot_tes_soc(peak_tes_soc=None, demand_class=None):
    """
    Plots the average TES SOC values for the PP operating mode (uses "peak" CHP size). Plot is saved to the /plots
    folder for future use.

    Parameters
    ----------
    peak_tes_soc: list
        contains hourly TES SOC values for the PP operating mode (uses "peak" CHP size)
    demand_class: EnergyDemand class
        contains initialized EnergyDemand class from command_line.py

    """
    args_list = [peak_tes_soc, demand_class]
    if any(elem is None for elem in args_list) is False:
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
        plt.title('PP TES SOC, Daily Avg')
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
