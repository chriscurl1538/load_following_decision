"""
Module Description:
    This module will create plots of data passed to the program
    as well as relevant data calculated by the program

Plots to be included:
    Aux Boiler Heat Generated
"""

import matplotlib.pyplot as plt, numpy as np
import chp as cogen, thermal_storage as storage, aux_boiler as boiler


def plot_electrical_demand(demand=None):
    data = demand.el

    # Convert to base units before creating numpy array for plotting
    y = np.array([dem.to_base_units().magnitude for dem in data])

    plt.plot(y)
    plt.title('Annual Electrical Demand, Hourly')
    plt.ylabel('Electrical Demand [{}]'.format(data[0].units))
    plt.yticks(np.arange(y.min(), y.max(), 5))
    plt.xlabel('Time (hours)')

    # plot
    plt.show()


def plot_thermal_demand(demand=None):
    data = demand.hl

    # Convert to base units before creating numpy array for plotting
    y = np.array([dem.to_base_units().magnitude for dem in data])

    plt.plot(y)
    plt.title('Annual Heating Demand, Hourly')
    plt.ylabel('Heating Demand [{}]'.format(data[0].units))
    plt.yticks(np.arange(y.min(), y.max(), 20000))
    plt.xlabel('Time (hours)')

    # plot
    plt.show()


def plot_chp_electricity_generated(chp=None, demand=None):
    data = cogen.calc_hourly_generated_electricity(chp=chp, demand=demand)

    # Convert to base units before creating numpy array for plotting
    y = np.array([gen.to_base_units().magnitude for gen in data])

    plt.plot(y)
    plt.title('CHP Electricity Generation, Hourly')
    plt.ylabel('Electricity [{}]'.format(data[0].units))
    plt.yticks(np.arange(y.min(), y.max(), 5))
    plt.xlabel('Time (hours)')

    # plot
    plt.show()


def plot_chp_heat_generated(chp=None, demand=None):
    data = cogen.calc_hourly_heat_generated(chp=chp, demand=demand)

    # Convert to base units before creating numpy array for plotting
    y = np.array([heat.to_base_units().magnitude for heat in data])

    plt.plot(y)
    plt.title('CHP Heat Generated, Hourly')
    plt.ylabel('Heat [{}]'.format(data[0].units))
    plt.yticks(np.arange(y.min(), y.max(), 5))
    plt.xlabel('Time (hours)')

    # plot
    plt.show()


def plot_tes_status(chp=None, demand=None, tes=None):
    data = storage.tes_heat_stored(chp=chp, demand=demand, tes=tes)

    # Convert to base units before creating numpy array for plotting
    y = np.array([status.to_base_units().magnitude for status in data])

    plt.plot(y)
    plt.title('TES Status, Hourly')
    plt.ylabel('Heat [{}]'.format(data[0].units))
    plt.yticks(np.arange(y.min(), y.max(), 5))
    plt.xlabel('Time (hours)')

    # plot
    plt.show()


def plot_aux_boiler_output(chp=None, demand=None, tes=None, ab=None):
    data = boiler.calc_aux_boiler_output(chp=chp, demand=demand, tes=tes, ab=ab)

    # Convert to base units before creating numpy array for plotting
    y = np.array([heat.to_base_units().magnitude for heat in data])

    plt.plot(y)
    plt.title('Boiler Output, Hourly')
    plt.ylabel('Heat [{}]'.format(data[0].units))
    plt.yticks(np.arange(y.min(), y.max(), 5))
    plt.xlabel('Time (hours)')

    # plot
    plt.show()
