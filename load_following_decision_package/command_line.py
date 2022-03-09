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
    for i in range(30, 110, 10):
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

    # Annual Demand Values
    electric_demand = demand.annual_el
    thermal_demand = demand.annual_hl

    # Thermal Energy Savings
    # TODO: Thermal Energy Savings

    # Thermal Cost Savings
    # TODO: Thermal Cost Savings

    # Electrical Energy Savings
    electric_energy_savings = sum(cogen.calc_hourly_generated_electricity())

    # Electrical Cost Savings
    electric_cost_old = demand.el_cost * demand.annual_el
    electric_cost_new = cogen.calc_annual_electric_cost()
    electric_cost_savings = abs(electric_cost_old - electric_cost_new)

    # Total Cost Savings
    # TODO: Total Cost Savings

    # Simple Payback Period
    # TODO: Simple Payback Period

    # Fuel Consumption Annual
    # TODO: Fuel Consumption Annual

    # Table: Display economic calculations
    head_comparison = ["", "Control", "ELF"]

    elf_costs = [
        ["Annual Electrical Demand [kWh]", round(electric_demand, 0), ""],
        ["Annual Thermal Demand [Btu]", round(thermal_demand, 0), ""],
        ["Thermal Energy Savings [Btu]", "", ""],
        ["Thermal Cost Savings [$]", "", ""],
        ["Electrical Energy Savings [kWh]", 0, round(electric_energy_savings, 0)],
        ["Electrical Cost Savings [$]", "", round(electric_cost_savings, 0)],
        ["Total Cost Savings [$]", "", ""],
        ["Simple Payback [Yrs]", "", ""]
    ]

    table_elf_costs = tabulate(elf_costs, headers=head_comparison, tablefmt="fancy_grid")
    print(table_elf_costs)

    # Table: Display system property inputs
    head_equipment = ["", "mCHP", "TES", "Aux Boiler"]

    system_properties = [
        ["Efficiency (Full Load)", chp.pl[-1, 1], "N/A", ab.eff],
        ["Turn-Down Ratio", chp.td, "N/A", ab.td],
        ["Size", chp.cap, tes.cap, ab.cap],
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
        ["Fuel Cost [$/MMBtu]", demand.fuel_cost],
        ["Electricity Rate [$/kWh]", demand.el_cost]
    ]

    table_input_data = tabulate(input_data, headers=head_units, tablefmt="fancy_grid")
    print(table_input_data)


if __name__ == "__main__":
    main()
