"""
Module Description:
    Command line interface - imports .yaml file and uses equipment operating parameters
    from the file to initialize the class variables.

Documentation action items:
    TODO: Update README.md with PyPI installation instructions (line 79)
    TODO: Generate distribution archives and upload to PyPI
    (see https://packaging.python.org/en/latest/tutorials/packaging-projects/)
    TODO: Add instructions for using the testing suite to /docs/how_to_guide.md
    TODO: Add desired output to /docs/example_output.md
"""

from lfd_package.modules import aux_boiler as boiler, classes, chp as cogen, plots
import pathlib, argparse, yaml, numpy as np
from tabulate import tabulate
from lfd_package.modules.__init__ import ureg


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
    chp = classes.CHP(capacity=data['chp_cap'], heat_power=data['chp_heat_power'],
                      turn_down_ratio=data['chp_turn_down'],
                      part_load=part_load_array, cost=data['chp_installed_cost'])
    ab = classes.AuxBoiler(capacity=data['ab_capacity'], efficiency=data['ab_eff'],
                           turn_down_ratio=data['ab_turn_down'])
    demand = classes.EnergyDemand(file_name=data['demand_filename'], electric_cost=data['electric_utility_cost'],
                                  fuel_cost=data['fuel_cost'])
    tes = classes.TES(capacity=data['tes_cap'], cost=data['tes_installed_cost'])

    return [chp, ab, demand, tes]


def main():
    # Command Line Interface
    parser = argparse.ArgumentParser(description="Import equipment operating parameter data")
    parser.add_argument("--in", help="filename for .yaml file with equipment data", dest="input", type=str,
                        required=True)
    parser.set_defaults(func=run)
    args = parser.parse_args()
    args.func(args)

    # Retrieve initialized class from run() function
    class_list = run(args)
    chp = class_list[0]
    ab = class_list[1]
    demand = class_list[2]
    tes = class_list[3]

    # Annual Demand Values
    electric_demand = demand.annual_el
    thermal_demand = demand.annual_hl

    # Thermal Energy Savings (current energy consumption - proposed energy consumption)
    thermal_consumption_control = thermal_demand / ab.eff
    thermal_consumption_chp = cogen.calculate_annual_fuel_use(chp=chp, demand=demand)
    thermal_consumption_ab = boiler.calc_annual_fuel_use(chp=chp, demand=demand, tes=tes, ab=ab)
    thermal_consumption_elf = thermal_consumption_chp + thermal_consumption_ab
    thermal_energy_savings = thermal_consumption_control - thermal_consumption_elf

    # Thermal Cost Savings (current energy costs - proposed energy costs)
    thermal_cost_control = thermal_consumption_control.to(ureg.megaBtu) * demand.fuel_cost
    thermal_cost_chp = cogen.calc_annual_fuel_cost(chp=chp, demand=demand)
    thermal_cost_ab = boiler.calc_annual_fuel_cost(chp=chp, demand=demand, tes=tes, ab=ab)
    thermal_cost_elf = thermal_cost_chp + thermal_cost_ab
    thermal_cost_savings = thermal_cost_control - thermal_cost_elf

    # Electrical Energy Savings
    electric_energy_savings = sum(cogen.calc_hourly_generated_electricity(chp=chp, demand=demand))

    # Electrical Cost Savings
    electric_cost_old = demand.el_cost * demand.annual_el
    electric_cost_new = cogen.calc_annual_electric_cost(chp=chp, demand=demand)
    electric_cost_savings = abs(electric_cost_old - electric_cost_new)

    # Total Cost Savings
    total_cost_savings = electric_cost_savings + thermal_cost_savings

    # Implementation Cost (material cost + installation cost)
    capex_chp = chp.cost * chp.cap
    tes_cap_kwh = tes.cap.to(ureg.kWh)
    capex_tes = tes.cost * tes_cap_kwh
    implementation_cost = capex_chp + capex_tes

    # Simple Payback Period (implementation cost / annual cost savings)
    simple_payback = implementation_cost / total_cost_savings

    # Table: Display economic calculations
    head_comparison = ["", "ELF"]

    elf_costs = [
        ["Annual Electrical Demand [kWh]", round(electric_demand)],
        ["Annual Thermal Demand [Btu]", round(thermal_demand)],
        ["Thermal Energy Savings [Btu]", round(thermal_energy_savings)],
        ["Thermal Cost Savings [$]", round(thermal_cost_savings)],
        ["Electrical Energy Savings [kWh]", round(electric_energy_savings)],
        ["Electrical Cost Savings [$]", round(electric_cost_savings)],
        ["Total Cost Savings [$]", round(total_cost_savings)],
        ["Simple Payback [Yrs]", round(simple_payback)]
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

    table_system_properties = tabulate(system_properties, headers=head_equipment, tablefmt="fancy_grid")
    print(table_system_properties)

    # Table: Display key input data
    head_units = ["", "Value"]

    input_data = [
        ["Fuel Cost [$/MMBtu]", demand.fuel_cost],
        ["Electricity Rate [$/kWh]", demand.el_cost],
        ["CHP Installed Cost [$]", capex_chp],
        ["TES Installed Cost [$]", capex_tes]
    ]

    table_input_data = tabulate(input_data, headers=head_units, tablefmt="fancy_grid")
    print(table_input_data)

    # Plots
    plots.plot_electrical_demand(demand=demand)
    plots.plot_thermal_demand(demand=demand)
    plots.plot_chp_electricity_generated(chp=chp, demand=demand)
    plots.plot_chp_heat_generated(chp=chp, demand=demand)
    plots.plot_tes_status(chp=chp, demand=demand, tes=tes)
    plots.plot_aux_boiler_output(chp=chp, demand=demand, tes=tes, ab=ab)


if __name__ == "__main__":
    main()
