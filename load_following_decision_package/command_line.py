"""
Module Description:
    desc
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
    yaml_filename = args.input   # these match the "dest": dest="input"

    with open(yaml_filename) as f:
        data = yaml.load(f, Loader=Loader)

        classes.CHP(capacity=data["chp_cap"], heat_power=data["chp_heat_power"], turn_down_ratio=data["chp_turn_down"],
                    part_load=np.array(data["part_loads"], dtype=float))
        classes.AuxBoiler(capacity=data["ab_capacity"], efficiency=data["ab_eff"], turn_down_ratio=data["ab_turn_down"])
        classes.EnergyDemand(file_name=data["demand_filename"], net_metering=data["net_metering"],
                             electric_cost=data["electric_utility_cost"], fuel_cost=data["fuel_cost"])
    f.close()


def main():
    parser = argparse.ArgumentParser(description="Import equipment operating parameter data")
    parser.add_argument("--in", help="filename for .yaml file with equipment data", dest="input", type=str, required=True)
    parser.add_argument("--out", help="fastq output filename", dest="output", type=str, required=True)
    parser.set_defaults(func=run)
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
