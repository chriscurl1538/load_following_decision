"""
Module Description:
    This module will create plots of data passed to the program
    as well as relevant data calculated by the program

Plots to be included:
    Electrical Demand (done)
    Thermal Demand (done)
    mCHP Electricity Generated (done)
    mCHP Heat Generated (done)
    TES Storage/Dispatch History
    Aux Boiler Heat Generated
"""

import matplotlib.pyplot as plt
import numpy as np
import classes
import chp as cogen
from __init__ import ureg


def plot_electrical_demand():
    demand = classes.EnergyDemand()

    y = demand.el
    plt.plot(y)
    plt.title('Annual Electrical Demand, Hourly')
    plt.ylabel('Electrical Demand [kWh]')
    plt.yticks(np.arange(y.min(), y.max(), 5))
    plt.xlabel('Time (hours)')

    # plot
    plt.show()


def plot_thermal_demand():
    demand = classes.EnergyDemand()

    y = demand.hl
    plt.plot(y)
    plt.title('Annual Heating Demand, Hourly')
    plt.ylabel('Heating Demand [Btu]')
    plt.yticks(np.arange(y.min(), y.max(), 20000))
    plt.xlabel('Time (hours)')

    # plot
    plt.show()


def plot_chp_electricity_generated():
    data = cogen.calc_hourly_generated_electricity()

    # Convert to base units before creating numpy array for plotting
    y = np.array([gen.to_base_units().magnitude for gen in data])

    plt.plot(y)
    plt.title('CHP Electricity Generation, Hourly')
    plt.ylabel('Electricity [{}]'.format(data[0].units))
    plt.yticks(np.arange(y.min(), y.max(), 5))
    plt.xlabel('Time (hours)')

    # plot
    plt.show()


def plot_chp_heat_generated():
    data = cogen.calc_hourly_heat_generated()

    # Convert to base units before creating numpy array for plotting
    y = np.array([heat.to_base_units().magnitude for heat in data])

    plt.plot(y)
    plt.title('CHP Heat Generated, Hourly')
    plt.ylabel('Heat [{}}]'.format(data[0].units))
    plt.yticks(np.arange(y.min(), y.max(), 5))
    plt.xlabel('Time (hours)')

    # plot
    plt.show()


def plot_tes_history():
    return None


if __name__ == "__main__":
    plot_chp_heat_generated()
