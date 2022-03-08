"""
Module Description:
    This module will create plots of data passed to the program
    as well as relevant data calculated by the program

Plots to be included:
    Electrical Demand
    Thermal Demand
    mCHP Electricity Generated
    mCHP Heat Generated
    TES Storage/Dispatch History
    Aux Boiler Heat Generated
"""

# TODO: plot electrical and thermal demand of building

import matplotlib.pyplot as plt
import numpy as np
import classes


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


if __name__ == "__main__":
    plot_thermal_demand()
    plot_electrical_demand()