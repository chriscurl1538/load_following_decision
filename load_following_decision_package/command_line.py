"""
Module Description:
    Command line interface - imports .yaml file and uses equipment operating parameters
    from the file to initialize the class variables.
"""

import argparse
import classes
import numpy as np
import yaml
try:
    from yaml import CLoader as Loader
except ImportError:
    from yaml import Loader


def run(args):
    """

    Parameters
    ----------
    args
        inputs from command line using argparse

    Returns
    -------

    """
    yaml_filename = args.input   # these match the "dest": dest="input"

    with open(yaml_filename) as f:
        data = yaml.load(f, Loader=Loader)
    f.close()

    part_load_list = []
    for i in range(30, 100, 10):
        part_load_list.append([i, data[i]])
    part_load_array = np.array(part_load_list)

    classes.CHP(capacity=data['chp_cap'], heat_power=data['chp_heat_power'], turn_down_ratio=data['chp_turn_down'],
                part_load=part_load_array)
    classes.AuxBoiler(capacity=data['ab_capacity'], efficiency=data['ab_eff'], turn_down_ratio=data['ab_turn_down'])
    classes.EnergyDemand(file_name=data['demand_filename'], net_metering=data['net_metering'],
                         electric_cost=data['electric_utility_cost'], fuel_cost=data['fuel_cost'])


def main():
    # TODO: Add argument that prints program output to a file
    parser = argparse.ArgumentParser(description="Import equipment operating parameter data")
    parser.add_argument("--in", help="filename for .yaml file with equipment data", dest="input", type=str,
                        required=True)
    parser.set_defaults(func=run)
    args = parser.parse_args()
    args.func(args)

    # TODO: Add other modules to main() function here


if __name__ == "__main__":
    main()
