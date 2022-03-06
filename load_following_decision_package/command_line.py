"""
Module Description:
    Command line interface - imports .yaml file and uses equipment operating parameters
    from the file to initialize the class variables.
"""

import electric_load_following as elf

import pathlib

import argparse
import classes
import numpy as np
from tabulate import tabulate
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
    cwd = pathlib.Path(__file__).parent.resolve() / 'input_files'

    with open(cwd / yaml_filename) as f:
        data = yaml.load(f, Loader=Loader)
    f.close()

    part_load_list = []
    for i in range(30, 100, 10):
        part_load_list.append([i, data[i]])
    part_load_array = np.array(part_load_list)

    # TODO: This does not store the data in classes as anticipated

    chp = classes.CHP(capacity=data['chp_cap'], heat_power=data['chp_heat_power'], turn_down_ratio=data['chp_turn_down']
                      , thermal_output_to_fuel_input=['thermal_output_to_fuel_input'], part_load=part_load_array)
    ab = classes.AuxBoiler(capacity=data['ab_capacity'], efficiency=data['ab_eff'], turn_down_ratio=data['ab_turn_down']
                           )
    demand = classes.EnergyDemand(file_name=data['demand_filename'], electric_cost=data['electric_utility_cost'],
                                  fuel_cost=data['fuel_cost'])


def main():
    # TODO: Add argument that prints program output to a file
    parser = argparse.ArgumentParser(description="Import equipment operating parameter data")
    parser.add_argument("--in", help="filename for .yaml file with equipment data", dest="input", type=str,
                        required=True)
    parser.set_defaults(func=run)
    args = parser.parse_args()
    args.func(args)

    # TODO: Add other modules to main() function here

    # Headers to be used in tables
    head_equipment = ["", "mCHP", "TES", "Aux Boiler"]
    head_units = ["", "Value", "Units"]
    head_comparison = ["", "Control", "ELF"]

    # Create list of economic calculations
    demand = classes.EnergyDemand()
    chp = classes.CHP()
    ab = classes.AuxBoiler()

    electric_demand = demand.annual_el
    thermal_demand = demand.annual_hl

    util_electric_demand_list = elf.calc_utility_electricity_needed()
    util_electric_demand = sum(util_electric_demand_list)

    # Display economic calculations
    elf_costs = [
        ["Annual Electrical Demand", electric_demand, util_electric_demand],
        ["Annual Thermal Demand", thermal_demand, ""],
        ["Thermal Energy Savings", "", ""],
        ["Thermal Cost Savings", "", ""],
        ["Electrical Energy Savings", "", ""],
        ["Electrical Cost Savings", "", ""],
        ["Total Cost Savings", "", ""],
        ["Simple Payback", "", ""]
    ]

    table_elf_costs = tabulate(elf_costs, headers=head_comparison, tablefmt="grid")
    print(table_elf_costs)

    # Display system property inputs
    system_properties = [
        ["Efficiency", "", "", ""],
        ["Turn-Down Ratio", chp.td, "", ab.td],
        ["Size", chp.cap, "", ab.cap],
        ["Heat to Power Ratio", chp.hp, "N/A", "N/A"],
        ["Heat out to Fuel in", chp.out_in, "N/A", "N/A"]
    ]

    table_system_properties = tabulate(system_properties, headers=head_equipment, tablefmt="fancy_grid")
    print(table_system_properties)

    # Display key input data
    input_data = [
        ["Fuel Cost", demand.fuel_cost, ""],
        ["Electricity Rate", demand.el_cost, ""]
    ]

    table_input_data = tabulate(input_data, headers=head_units, tablefmt="fancy_grid")
    print(table_input_data)

    # Fuel Consumption
    fuel_consumption = [
        ["Fuel Consumption", "", "", ""]
    ]

    table_fuel_consumption = tabulate(fuel_consumption, headers=head_equipment, tablefmt="fancy_grid")
    print(table_fuel_consumption)


if __name__ == "__main__":
    main()
