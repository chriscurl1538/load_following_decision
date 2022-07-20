"""
Module Description:
    Command line interface - imports .yaml file and uses equipment operating parameters
    from the file to initialize the class variables.
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
    Takes in information from the command line and assigns input data
    to the package's classes.

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
    tes: TES class
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
    tes = classes.TES(capacity=data['tes_cap'], start=data['tes_init'], discharge=data['tes_discharge_rate'],
                      cost=data['tes_installed_cost'])

    return [chp, ab, demand, tes]


def main():
    """
    Generates tables with cost and savings calculations and plots of equipment
    energy use / energy generation

    Returns
    -------
    Tables of economic information in the terminal
    Plots including:
        Electrical demand inputs
        Thermal demand inputs
        CHP Electricity Generation
        CHP Heat Generation
        TES Heat Storage status
        Aux Boiler Heat output
    """
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
    elf_thermal_consumption_chp = cogen.calc_annual_fuel_use_and_costs(chp=chp, demand=demand,
                                                                       load_following_type="ELF")[0]
    elf_thermal_consumption_ab = boiler.calc_annual_fuel_use_and_cost(chp=chp, demand=demand, tes=tes, ab=ab,
                                                                      load_following_type="ELF")[0]
    elf_thermal_consumption_total = elf_thermal_consumption_chp + elf_thermal_consumption_ab
    elf_thermal_energy_savings = thermal_consumption_control - elf_thermal_consumption_total

    tlf_thermal_consumption_chp = cogen.calc_annual_fuel_use_and_costs(chp=chp, demand=demand,
                                                                       load_following_type="TLF")[0]
    tlf_thermal_consumption_ab = boiler.calc_annual_fuel_use_and_cost(chp=chp, demand=demand, tes=tes, ab=ab,
                                                                      load_following_type="TLF")[0]
    tlf_thermal_consumption_total = tlf_thermal_consumption_chp + tlf_thermal_consumption_ab
    tlf_thermal_energy_savings = thermal_consumption_control - tlf_thermal_consumption_total

    # Thermal Cost Savings (current energy costs - proposed energy costs)
    thermal_cost_control = thermal_consumption_control.to(ureg.megaBtu) * demand.fuel_cost
    elf_thermal_cost_chp = cogen.calc_annual_fuel_use_and_costs(chp=chp, demand=demand, load_following_type="ELF")[1]
    elf_thermal_cost_ab = boiler.calc_annual_fuel_use_and_cost(chp=chp, demand=demand, tes=tes, ab=ab,
                                                               load_following_type="ELF")[1]
    elf_thermal_cost_total = elf_thermal_cost_chp + elf_thermal_cost_ab
    elf_thermal_cost_savings = thermal_cost_control - elf_thermal_cost_total

    tlf_thermal_cost_chp = cogen.calc_annual_fuel_use_and_costs(chp=chp, demand=demand, load_following_type="TLF")[1]
    tlf_thermal_cost_ab = boiler.calc_annual_fuel_use_and_cost(chp=chp, demand=demand, tes=tes, ab=ab,
                                                               load_following_type="TLF")[1]
    tlf_thermal_cost_total = tlf_thermal_cost_chp + tlf_thermal_cost_ab
    tlf_thermal_cost_savings = thermal_cost_control - tlf_thermal_cost_total

    # Electrical Energy Savings
    elf_electric_energy_savings = sum(cogen.elf_calc_electricity_bought_and_generated(chp=chp, demand=demand)[1])
    tlf_electric_energy_savings = sum(cogen.tlf_calc_electricity_bought_and_generated(chp=chp, demand=demand)[1])

    # ELF Electrical Cost Savings
    electric_cost_old = demand.el_cost * demand.annual_el
    elf_electric_cost_new = cogen.calc_annual_electric_cost(chp=chp, demand=demand, load_following_type="ELF")
    elf_electric_cost_savings = electric_cost_old - elf_electric_cost_new

    tlf_electric_cost_new = cogen.calc_annual_electric_cost(chp=chp, demand=demand, load_following_type="TLF")
    tlf_electric_cost_savings = electric_cost_old - tlf_electric_cost_new

    # Total Cost Savings
    elf_total_cost_savings = elf_electric_cost_savings + elf_thermal_cost_savings
    tlf_total_cost_savings = tlf_electric_cost_savings + tlf_thermal_cost_savings

    # Implementation Cost (material cost + installation cost)
    capex_chp = chp.cost * chp.cap
    tes_cap_kwh = tes.cap.to(ureg.kWh)
    capex_tes = tes.cost * tes_cap_kwh
    implementation_cost = capex_chp + capex_tes

    # Simple Payback Period (implementation cost / annual cost savings)
    elf_simple_payback = (implementation_cost / elf_total_cost_savings) * ureg.year
    tlf_simple_payback = (implementation_cost / tlf_total_cost_savings) * ureg.year

    # Table: Display economic calculations
    head_comparison = ["", "ELF", "TLF"]

    costs = [
        ["Annual Electrical Demand [kWh]", round(electric_demand, 2), "N/A"],
        ["Annual Thermal Demand [Btu]", round(thermal_demand, 2), "N/A"],
        ["Thermal Energy Savings [Btu]", round(elf_thermal_energy_savings, 2), round(tlf_thermal_energy_savings, 2)],
        ["Thermal Cost Savings [$]", round(elf_thermal_cost_savings.magnitude, 2),
         round(tlf_thermal_cost_savings.magnitude, 2)],
        ["Electrical Energy Savings [kWh]", round(elf_electric_energy_savings, 2),
         round(tlf_electric_energy_savings, 2)],
        ["Electrical Cost Savings [$]", round(elf_electric_cost_savings.magnitude, 2),
         round(tlf_electric_cost_savings.magnitude, 2)],
        ["Total Cost Savings [$]", round(elf_total_cost_savings.magnitude, 2),
         round(tlf_total_cost_savings.magnitude, 2)],
        ["Simple Payback [Yrs]", round(elf_simple_payback, 2), round(tlf_simple_payback, 2)]
    ]

    table_costs = tabulate(costs, headers=head_comparison, tablefmt="fancy_grid")
    print(table_costs)

    # Table: Display system property inputs
    head_equipment = ["", "mCHP", "TES", "Aux Boiler"]
    hpr_rec = demand.hl_mchp_size_rec.to(ureg.kWh) / (demand.el_mchp_size_rec * 1 * ureg.hours)

    system_properties = [
        ["Efficiency (Full Load)", "{} %".format(chp.pl[-1, 1] * 100), "N/A", "{} %".format(ab.eff * 100)],
        ["Turn-Down Ratio", chp.td, "N/A", ab.td],
        ["Size Actual", chp.cap, tes.cap, ab.cap],
        ["Size Recommended", round(demand.el_mchp_size_rec, 2), "", ""],
        ["Heat to Power Ratio Actual", chp.hp, "N/A", "N/A"],
        ["Heat to Power Ratio Recommended", round(hpr_rec, 2), "N/A", "N/A"]
    ]

    table_system_properties = tabulate(system_properties, headers=head_equipment, tablefmt="fancy_grid")
    print(table_system_properties)

    # Table: Display key input data
    head_units = ["", "Value"]

    input_data = [
        ["Fuel Cost [$/MMBtu]", round(demand.fuel_cost, 2)],
        ["Electricity Rate [$/kWh]", round(demand.el_cost, 2)],
        ["CHP Installed Cost [$]", round(capex_chp.magnitude, 2)],
        ["TES Installed Cost [$]", round(capex_tes.magnitude, 2)]
    ]

    table_input_data = tabulate(input_data, headers=head_units, tablefmt="fancy_grid")
    print(table_input_data)

    # Plots
    plots.plot_electrical_demand_curve(demand=demand)
    plots.plot_thermal_demand_curve(demand=demand)

    plots.elf_plot_electric(chp=chp, demand=demand)
    plots.elf_plot_thermal(chp=chp, demand=demand, tes=tes, ab=ab)
    plots.elf_plot_tes_soc(chp=chp, demand=demand, tes=tes)

    plots.tlf_plot_electric(chp=chp, demand=demand)
    plots.tlf_plot_thermal(chp=chp, demand=demand, tes=tes, ab=ab)
    plots.tlf_plot_tes_soc(chp=chp, demand=demand, tes=tes)


if __name__ == "__main__":
    main()
