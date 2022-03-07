"""
Module Description:
    This module will create plots of data passed to the program
    as well as relevant data calculated by the program
"""

# TODO: plot electrical and thermal demand of building

import matplotlib.pyplot as plt
import numpy as np
import classes


def plot_electrical_demand():
    demand = classes.EnergyDemand()
    plt.style.use('_mpl-gallery')

    # make data
    x = range(8760)
    y = demand.el

    # plot
    fig, ax = plt.subplots()

    ax.plot(x, y, linewidth=2.0)

    ax.set(xlim=(0, 8), xticks=np.arange(1, 8),
           ylim=(0, 8), yticks=np.arange(1, 8))

    plt.show()


if __name__ == "__main__":
    plot_electrical_demand()
