"""
Expected command line inputs:
    part_load_eff
    heat_power_ratio
    thermal_load_profile
    electrical_load_profile
    fuel_HHV
"""

import sys
import argparse
import ruamel_yaml
# Use yaml files for large number of inputs


# Command Line Example
parser = argparse.ArgumentParser(
    description='This is a simple command-line program.'
)
parser.add_argument('-n', '--name', required=True,
                    help='name of the user')

args = parser.parse_args(sys.argv[1:])

print("Hi there {}, nice to meet you".format(args.name))
