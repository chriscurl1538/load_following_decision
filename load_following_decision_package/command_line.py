"""
Module Description:
    Command line interface - imports .yaml file and uses equipment operating parameters
    from the file to initialize the class variables.
"""

import chp as cogen
import classes

import pathlib
import argparse
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
    chp: CHP class
        Initialized class using input data from .yaml file
    ab: AuxBoiler class
        Initialized class using input data from .yaml file
    demand: EnergyDemand class
        Initialized class using input data from .yaml file
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

    # Class initialization using CLI arguments
    chp = classes.CHP(capacity=data['chp_cap'], heat_power=data['chp_heat_power'], turn_down_ratio=data['chp_turn_down']
                      , thermal_output_to_fuel_input=data['thermal_output_to_fuel_input'], part_load=part_load_array)
    ab = classes.AuxBoiler(capacity=data['ab_capacity'], efficiency=data['ab_eff'], turn_down_ratio=data['ab_turn_down']
                           )
    demand = classes.EnergyDemand(file_name=data['demand_filename'], electric_cost=data['electric_utility_cost'],
                                  fuel_cost=data['fuel_cost'])
    tes = classes.TES(capacity=data['tes_cap'])

    return chp, ab, demand, tes


def main():
    # Command Line Interface
    parser = argparse.ArgumentParser(description="Import equipment operating parameter data")
    parser.add_argument("--in", help="filename for .yaml file with equipment data", dest="input", type=str,
                        required=True)
    parser.set_defaults(func=run)
    args = parser.parse_args()
    args.func(args)

    # Retrieve initialized class from run() function
    chp, ab, demand, tes = run(args)

    # Electrical and Thermal Demand
    electric_demand = demand.annual_el
    thermal_demand = demand.annual_hl

    # Electricity bought using CHP
    bought_hourly = cogen.calc_electricity_bought()
    util_electric_demand = sum(bought_hourly)
    electric_energy_savings = sum(cogen.calc_generated_electricity())
    electric_cost_savings = cogen.calc_annual_electric_cost()

    # Table: Display economic calculations
    head_comparison = ["", "Control", "ELF"]

    elf_costs = [
        ["Annual Electrical Demand [kWh]", electric_demand, ""],
        ["Annual Thermal Demand [Btu]", thermal_demand, ""],
        ["Thermal Energy Savings [Btu]", "", ""],
        ["Thermal Cost Savings [$]", "", ""],
        ["Electrical Energy Savings [kWh]", 0, electric_energy_savings],
        ["Electrical Cost Savings [$]", "", electric_cost_savings],
        ["Total Cost Savings [$]", "", ""],
        ["Simple Payback [Yrs]", "", ""]
    ]

    table_elf_costs = tabulate(elf_costs, headers=head_comparison, tablefmt="fancy_grid")
    print(table_elf_costs)

    # Table: Display system property inputs
    head_equipment = ["", "mCHP", "TES", "Aux Boiler"]

    system_properties = [
        ["Efficiency", "", "", ""],
        ["Turn-Down Ratio", chp.td, "", ab.td],
        ["Size", '{} kW'.format(chp.cap), "", '{} MMBtu/hr'.format(ab.cap)],
        ["Heat to Power Ratio", chp.hp, "N/A", "N/A"],
        ["Heat out to Fuel in", chp.out_in, "N/A", "N/A"]
    ]

    fuel_consumption = [
        ["Fuel Consumption [Btu]", "", "N/A", ""]
    ]

    table_system_properties = tabulate(system_properties, headers=head_equipment, tablefmt="fancy_grid")
    print(table_system_properties)

    table_fuel_consumption = tabulate(fuel_consumption, headers=head_equipment, tablefmt="fancy_grid")
    print(table_fuel_consumption)

    # Table: Display key input data
    head_units = ["", "Value"]

    input_data = [
        ["Fuel Cost [$]", demand.fuel_cost],
        ["Electricity Rate [$/kWh]", demand.el_cost]
    ]

    table_input_data = tabulate(input_data, headers=head_units, tablefmt="fancy_grid")
    print(table_input_data)


if __name__ == "__main__":
    main()
