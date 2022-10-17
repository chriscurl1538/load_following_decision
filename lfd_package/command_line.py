"""
Module Description:
    Command line interface - imports .yaml file and uses equipment operating parameters
    from the file to initialize the class variables.
TODO: Create counter for each function to calculate how many times each is called. Can we reduce the calculation times?
"""

from lfd_package.modules import aux_boiler as boiler, classes, chp as cogen, chp_tes_sizing as sizing, plots
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

    part_load_electrical_list = []
    part_load_thermal_list = []
    for i in range(50, 125, 25):
        part_load_electrical_list.append([i, data['Electrical'][i]])
        part_load_thermal_list.append([i, data['Thermal'][i]])
    part_load_electrical_array = np.array(part_load_electrical_list)
    part_load_thermal_array = np.array(part_load_thermal_list)

    # Class initialization using CLI arguments
    chp = classes.CHP(fuel_type=data['fuel_type'], fuel_input_rate=data['fuel_input_rate'],
                      turn_down_ratio=data['chp_turn_down'], part_load_electrical=part_load_electrical_array,
                      part_load_thermal=part_load_thermal_array, chp_electric_eff=data['Electrical'][100],
                      chp_thermal_eff=data['Thermal'][100], percent_availability=data['percent_availability'],
                      cost=data['chp_installed_cost'])
    ab = classes.AuxBoiler(capacity=data['ab_capacity'], efficiency=data['ab_eff'],
                           turn_down_ratio=data['ab_turn_down'])
    demand = classes.EnergyDemand(file_name=data['demand_filename'], net_metering_status=data['net_metering_status'],
                                  grid_efficiency=data['grid_efficiency'],
                                  electric_cost=data['electric_utility_cost'],
                                  fuel_cost=data['fuel_cost'])
    tes = classes.TES(start=data['tes_init'], discharge=data['tes_discharge_rate'],
                      cost=data['tes_installed_cost'])

    return [demand, chp, tes, ab]


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
    demand = class_list[0]
    chp = class_list[1]
    tes = class_list[2]
    ab = class_list[3]

    # Retrieve equipment sizes
    tes_size_elf = sizing.size_tes(demand=demand, chp=chp, load_following_type='ELF', ab=ab)
    tes_size_tlf = sizing.size_tes(demand=demand, chp=chp, load_following_type='TLF', ab=ab)
    chp_size_tlf = sizing.size_chp(load_following_type='TLF', demand=demand, ab=ab)
    chp_size_elf = sizing.size_chp(load_following_type='ELF', demand=demand, ab=ab)

    # Thermal Energy Savings (current energy consumption - proposed energy consumption)
    thermal_consumption_control = demand.annual_hl / ab.eff
    elf_thermal_consumption_chp = cogen.calc_annual_fuel_use_and_costs(chp=chp, demand=demand, ab=ab,
                                                                       load_following_type="ELF")[0]
    elf_thermal_consumption_ab = boiler.calc_annual_fuel_use_and_cost(chp=chp, demand=demand, tes=tes, ab=ab,
                                                                      load_following_type="ELF")[0]
    elf_thermal_consumption_total = elf_thermal_consumption_chp + elf_thermal_consumption_ab
    elf_thermal_energy_savings = thermal_consumption_control - elf_thermal_consumption_total

    tlf_thermal_consumption_chp = cogen.calc_annual_fuel_use_and_costs(chp=chp, demand=demand, ab=ab,
                                                                       load_following_type="TLF")[0]
    tlf_thermal_consumption_ab = boiler.calc_annual_fuel_use_and_cost(chp=chp, demand=demand, tes=tes, ab=ab,
                                                                      load_following_type="TLF")[0]
    tlf_thermal_consumption_total = tlf_thermal_consumption_chp + tlf_thermal_consumption_ab
    tlf_thermal_energy_savings = thermal_consumption_control - tlf_thermal_consumption_total

    # Thermal Cost Savings (current energy costs - proposed energy costs)
    thermal_cost_control = thermal_consumption_control.to(ureg.megaBtu) * demand.fuel_cost
    elf_thermal_cost_chp = cogen.calc_annual_fuel_use_and_costs(chp=chp, demand=demand, ab=ab,
                                                                load_following_type="ELF")[1]
    elf_thermal_cost_ab = boiler.calc_annual_fuel_use_and_cost(chp=chp, demand=demand, tes=tes, ab=ab,
                                                               load_following_type="ELF")[1]
    elf_thermal_cost_total = elf_thermal_cost_chp + elf_thermal_cost_ab
    elf_thermal_cost_savings = thermal_cost_control - elf_thermal_cost_total

    tlf_thermal_cost_chp = cogen.calc_annual_fuel_use_and_costs(chp=chp, demand=demand, ab=ab, load_following_type="TLF")[1]
    tlf_thermal_cost_ab = boiler.calc_annual_fuel_use_and_cost(chp=chp, demand=demand, tes=tes, ab=ab,
                                                               load_following_type="TLF")[1]
    tlf_thermal_cost_total = tlf_thermal_cost_chp + tlf_thermal_cost_ab
    tlf_thermal_cost_savings = thermal_cost_control - tlf_thermal_cost_total

    # Electrical Energy Savings
    elf_electric_energy_savings = sum(cogen.elf_calc_electricity_bought_and_generated(chp=chp, demand=demand, ab=ab)[1])
    tlf_electric_energy_savings = sum(cogen.tlf_calc_electricity_bought_and_generated(chp=chp, demand=demand, ab=ab)[1])

    # ELF Electrical Cost Savings
    electric_cost_old = demand.el_cost * demand.annual_el
    elf_electric_cost_new = cogen.calc_annual_electric_cost(chp=chp, demand=demand, ab=ab, load_following_type="ELF")
    elf_electric_cost_savings = electric_cost_old - elf_electric_cost_new

    tlf_electric_cost_new = cogen.calc_annual_electric_cost(chp=chp, demand=demand, ab=ab, load_following_type="TLF")
    tlf_electric_cost_savings = electric_cost_old - tlf_electric_cost_new

    # Total Cost Savings
    elf_total_cost_savings = elf_electric_cost_savings + elf_thermal_cost_savings
    tlf_total_cost_savings = tlf_electric_cost_savings + tlf_thermal_cost_savings

    # Implementation Cost (material cost + installation cost)
    capex_chp_elf = chp.incremental_cost * sizing.size_chp(load_following_type='ELF', demand=demand, ab=ab)
    capex_chp_tlf = chp.incremental_cost * sizing.size_chp(load_following_type='TLF', demand=demand, ab=ab)
    tes_cap_elf_kwh = tes_size_elf.to(ureg.kWh)
    tes_cap_tlf_kwh = tes_size_tlf.to(ureg.kWh)
    capex_tes_elf = tes.incremental_cost * tes_cap_elf_kwh
    capex_tes_tlf = tes.incremental_cost * tes_cap_tlf_kwh
    implementation_cost_elf = capex_chp_elf + capex_tes_elf
    implementation_cost_tlf = capex_chp_tlf + capex_tes_tlf

    # Simple Payback Period (implementation cost / annual cost savings)
    elf_simple_payback = (implementation_cost_elf / elf_total_cost_savings) * ureg.year
    tlf_simple_payback = (implementation_cost_tlf / tlf_total_cost_savings) * ureg.year

    # Table: Display economic calculations
    head_comparison = ["", "ELF", "TLF"]

    costs = [
        ["Annual Electrical Demand [kWh]", round(demand.annual_el, 2), "N/A"],
        ["Annual Thermal Demand [Btu]", round(demand.annual_hl, 2), "N/A"],
        ["Thermal Energy Savings [Btu]", round(float(elf_thermal_energy_savings.magnitude), 2), round(float(tlf_thermal_energy_savings.magnitude), 2)],
        ["Thermal Cost Savings [$]", round(elf_thermal_cost_savings.magnitude, 2),
         round(float(tlf_thermal_cost_savings.magnitude), 2)],
        ["Electrical Energy Savings [kWh]", round(float(elf_electric_energy_savings.magnitude), 2),
         round(float(tlf_electric_energy_savings.magnitude), 2)],
        ["Electrical Cost Savings [$]", round(float(elf_electric_cost_savings.magnitude), 2),
         round(float(tlf_electric_cost_savings.magnitude), 2)],
        ["Total Cost Savings [$]", round(float(elf_total_cost_savings.magnitude), 2),
         round(float(tlf_total_cost_savings.magnitude), 2)],
        ["Simple Payback [Yrs]", round(float(elf_simple_payback.magnitude), 2), round(float(tlf_simple_payback.magnitude), 2)]
    ]

    table_costs = tabulate(costs, headers=head_comparison, tablefmt="fancy_grid")
    print(table_costs)

    # Table: Display system property inputs
    head_equipment = ["", "mCHP", "TES", "Aux Boiler"]

    system_properties = [
        ["Thermal Efficiency (Full Load)", "{} %".format(chp.th_nominal_eff * 100), "N/A", "{} %".format(ab.eff * 100)],
        ["Electrical Efficiency (Full Load)", "{} %".format(chp.el_nominal_eff * 100), "N/A", "N/A"],
        ["Minimum Load Operation", round(chp.min_pl, 2), "N/A", round(ab.min_pl, 2)],
        ["ELF Equipment Sizes", round(chp_size_elf, 2), tes_size_elf, ab.cap],
        ["TLF Equipment Sizes", round(chp_size_tlf, 2), tes_size_tlf, ab.cap]
    ]

    table_system_properties = tabulate(system_properties, headers=head_equipment, tablefmt="fancy_grid")
    print(table_system_properties)

    # Table: Display key input data
    head_units = ["", "Value"]

    input_data = [
        ["Fuel Cost [$/MMBtu]", round(demand.fuel_cost, 2)],
        ["Electricity Rate [$/kWh]", round(demand.el_cost, 2)],
        ["CHP Installed Cost, ELF [$]", round(capex_chp_elf.magnitude, 2)],
        ["CHP Installed Cost, TLF [$]", round(capex_chp_tlf.magnitude, 2)],
        ["TES Installed Cost, ELF [$]", round(capex_tes_elf.magnitude, 2)],
        ["TES Installed Cost, TLF [$]", round(capex_tes_tlf.magnitude, 2)]
    ]

    table_input_data = tabulate(input_data, headers=head_units, tablefmt="fancy_grid")
    print(table_input_data)

    # Plots
    plots.plot_electrical_demand_curve(demand=demand)
    plots.plot_thermal_demand_curve(demand=demand)

    plots.elf_plot_electric(chp=chp, demand=demand, ab=ab)
    plots.elf_plot_thermal(chp=chp, demand=demand, tes=tes, ab=ab)
    plots.elf_plot_tes_soc(chp=chp, demand=demand, tes=tes, ab=ab)

    plots.tlf_plot_electric(chp=chp, demand=demand, ab=ab)
    plots.tlf_plot_thermal(chp=chp, demand=demand, tes=tes, ab=ab)
    plots.tlf_plot_tes_soc(chp=chp, demand=demand, tes=tes, ab=ab)


if __name__ == "__main__":
    main()
