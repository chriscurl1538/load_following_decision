"""
Module Description:
    Command line interface - imports .yaml file and uses equipment operating parameters
    from the file to initialize the class variables.
TODO: Reduce calculation times by eliminating redundant function calls. Make new branch for this
TODO: Update all docstrings
TODO: Check that units of inputs and outputs are as expected in each function. Pick one set of units and stick with it
"""

from lfd_package.modules import aux_boiler as boiler, classes, chp as cogen, \
    sizing_calcs as sizing, plots, emissions, thermal_storage as storage
import pathlib, argparse, yaml, numpy as np
from tabulate import tabulate
from lfd_package.modules.__init__ import ureg, Q_


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
    chp = classes.CHP(fuel_input_rate=data['fuel_input_rate'],
                      turn_down_ratio=data['chp_turn_down'], part_load_electrical=part_load_electrical_array,
                      part_load_thermal=part_load_thermal_array, chp_electric_eff=data['Electrical'][100],
                      chp_thermal_eff=data['Thermal'][100], percent_availability=data['percent_availability'],
                      cost=data['chp_installed_cost'])
    demand = classes.EnergyDemand(file_name=data['demand_filename'],
                                  grid_efficiency=data['grid_efficiency'],
                                  electric_cost=data['electric_utility_cost'],
                                  fuel_cost=data['fuel_cost'], city=data['city'], state=data['state'])
    ab = classes.AuxBoiler(capacity=data['ab_capacity'], efficiency=data['ab_eff'],
                           turn_down_ratio=data['ab_turn_down'])
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
    chp_size_tlf = sizing.size_chp(load_following_type='TLF', demand=demand, ab=ab)
    chp_size_elf = sizing.size_chp(load_following_type='ELF', demand=demand, ab=ab)
    chp_size_pp = sizing.size_chp(load_following_type='PP', demand=demand, ab=ab)
    tes_size_elf = sizing.size_tes(demand=demand, chp=chp, load_following_type='ELF', ab=ab)
    tes_size_tlf = sizing.size_tes(chp_size=chp_size_tlf, demand=demand, chp=chp, load_following_type='TLF', ab=ab)
    tes_size_pp = sizing.size_tes(demand=demand, chp=chp, load_following_type='PP', ab=ab)

    """
    Energy Analysis
    """

    # Thermal Energy Savings (current energy consumption - proposed energy consumption)
    thermal_consumption_control = demand.annual_hl / ab.eff
    elf_thermal_consumption_chp = cogen.calc_annual_fuel_use_and_costs(chp=chp, demand=demand, ab=ab, tes=tes,
                                                                       load_following_type="ELF")[0]
    elf_thermal_consumption_ab = boiler.calc_annual_fuel_use_and_cost(chp_size=chp_size_elf, chp=chp, demand=demand, tes=tes, ab=ab,
                                                                      load_following_type="ELF")[0]
    elf_thermal_consumption_total = elf_thermal_consumption_chp + elf_thermal_consumption_ab
    elf_thermal_energy_savings = thermal_consumption_control - elf_thermal_consumption_total

    tlf_thermal_consumption_chp = cogen.calc_annual_fuel_use_and_costs(chp=chp, demand=demand, ab=ab, tes=tes,
                                                                       load_following_type="TLF")[0]
    tlf_thermal_consumption_ab = boiler.calc_annual_fuel_use_and_cost(chp_size=chp_size_tlf, chp=chp, demand=demand, tes=tes, ab=ab,
                                                                      load_following_type="TLF")[0]
    tlf_thermal_consumption_total = tlf_thermal_consumption_chp + tlf_thermal_consumption_ab
    tlf_thermal_energy_savings = thermal_consumption_control - tlf_thermal_consumption_total

    pp_thermal_consumption_chp = cogen.calc_annual_fuel_use_and_costs(chp=chp, demand=demand, ab=ab, tes=tes,
                                                                      load_following_type="PP")[0]
    pp_thermal_consumption_ab = boiler.calc_annual_fuel_use_and_cost(chp_size=chp_size_pp, chp=chp, demand=demand, tes=tes, ab=ab,
                                                                     load_following_type="PP")[0]
    pp_thermal_consumption_total = pp_thermal_consumption_chp + pp_thermal_consumption_ab
    pp_thermal_energy_savings = thermal_consumption_control - pp_thermal_consumption_total

    # Thermal Demand Met by Equipment
    # TODO: Fix CHP heat gen summation unit error in table
    elf_chp_thermal_gen = sum(cogen.elf_calc_hourly_heat_generated(chp=chp, demand=demand, ab=ab))
    tlf_chp_thermal_gen = sum(cogen.tlf_calc_hourly_heat_generated(chp=chp, demand=demand, ab=ab, tes=tes)[0])
    pp_chp_thermal_gen = sum(cogen.pp_calc_hourly_heat_generated(chp=chp, demand=demand, ab=ab))

    # TODO: Fix TES heat rate summation unit error in table
    elf_tes_heat_flow_list = storage.calc_tes_heat_flow_and_soc(chp_size=chp_size_elf, load_following_type="ELF",
                                                                  chp=chp, demand=demand, tes=tes, ab=ab)[0]
    elf_tes_thermal_dispatch = -1 * sum(item for item in elf_tes_heat_flow_list if item < 0)
    tlf_tes_heat_flow_list = cogen.tlf_calc_hourly_heat_generated(chp=chp, demand=demand, tes=tes, ab=ab)[1]
    tlf_tes_thermal_dispatch = -1 * sum(item for item in tlf_tes_heat_flow_list if item < 0)
    pp_tes_heat_flow_list = storage.calc_tes_heat_flow_and_soc(chp_size=chp_size_pp, load_following_type="PP",
                                                                  chp=chp, demand=demand, tes=tes, ab=ab)[0]
    pp_tes_thermal_dispatch = -1 * sum(item for item in pp_tes_heat_flow_list if item < 0)

    elf_boiler_dispatch = sum(boiler.calc_aux_boiler_output_rate(chp_size=chp_size_elf, chp=chp, demand=demand, tes=tes,
                                                                 ab=ab, load_following_type="ELF"))
    tlf_boiler_dispatch = sum(boiler.calc_aux_boiler_output_rate(chp_size=chp_size_tlf, chp=chp, demand=demand, tes=tes,
                                                                 ab=ab, load_following_type="TLF"))
    pp_boiler_dispatch = sum(boiler.calc_aux_boiler_output_rate(chp_size=chp_size_pp, chp=chp, demand=demand, tes=tes,
                                                                ab=ab, load_following_type="PP"))

    # Electrical Energy Savings
    elf_electricity_bought_list, elf_electric_gen_list = cogen.elf_calc_electricity_bought_and_generated(chp=chp, demand=demand, ab=ab)
    elf_electric_energy_savings = sum(elf_electric_gen_list)
    elf_electricity_bought = sum(elf_electricity_bought_list)
    tlf_electricity_bought_list, tlf_electric_gen_list = cogen.tlf_calc_electricity_bought_and_generated(chp=chp, demand=demand, ab=ab, tes=tes)
    tlf_electric_energy_savings = sum(tlf_electric_gen_list)
    tlf_electricity_bought = sum(tlf_electricity_bought_list)
    pp_electricity_bought_list, pp_electric_gen_list, pp_electricity_sold_list = cogen.pp_calc_electricity_bought_and_generated(chp=chp, demand=demand, ab=ab)
    pp_electric_energy_savings = sum(pp_electric_gen_list)
    pp_electricity_bought = sum(pp_electricity_bought_list)
    pp_electricity_sold = sum(pp_electricity_sold_list)

    """
    Economic Analysis
    """

    # Thermal Cost Savings (current energy costs - proposed energy costs)
    thermal_cost_control = thermal_consumption_control.to(ureg.megaBtu) * demand.fuel_cost
    elf_thermal_cost_chp = cogen.calc_annual_fuel_use_and_costs(chp=chp, demand=demand, ab=ab, tes=tes,
                                                                load_following_type="ELF")[1]
    elf_thermal_cost_ab = boiler.calc_annual_fuel_use_and_cost(chp_size=chp_size_elf, chp=chp, demand=demand, tes=tes, ab=ab,
                                                               load_following_type="ELF")[1]
    elf_thermal_cost_total = elf_thermal_cost_chp + elf_thermal_cost_ab
    elf_thermal_cost_savings = thermal_cost_control - elf_thermal_cost_total

    tlf_thermal_cost_chp = cogen.calc_annual_fuel_use_and_costs(chp=chp, demand=demand, ab=ab, tes=tes, load_following_type="TLF")[1]
    tlf_thermal_cost_ab = boiler.calc_annual_fuel_use_and_cost(chp_size=chp_size_tlf, chp=chp, demand=demand, tes=tes, ab=ab,
                                                               load_following_type="TLF")[1]
    tlf_thermal_cost_total = tlf_thermal_cost_chp + tlf_thermal_cost_ab
    tlf_thermal_cost_savings = thermal_cost_control - tlf_thermal_cost_total

    pp_thermal_cost_chp = cogen.calc_annual_fuel_use_and_costs(chp=chp, demand=demand, ab=ab, tes=tes, load_following_type="PP")[1]
    pp_thermal_cost_ab = boiler.calc_annual_fuel_use_and_cost(chp_size=chp_size_pp, chp=chp, demand=demand, tes=tes, ab=ab, load_following_type="PP")[1]
    pp_thermal_cost_total = pp_thermal_cost_chp + pp_thermal_cost_ab
    pp_thermal_cost_savings = thermal_cost_control - pp_thermal_cost_total

    # Electrical Cost Savings
    electric_cost_old = (demand.el_cost * demand.annual_el).to('')
    elf_electric_cost_new = cogen.calc_annual_electric_cost(chp=chp, demand=demand, ab=ab, tes=tes, load_following_type="ELF")
    elf_electric_cost_savings = electric_cost_old - elf_electric_cost_new

    tlf_electric_cost_new = cogen.calc_annual_electric_cost(chp=chp, demand=demand, ab=ab, tes=tes, load_following_type="TLF")
    tlf_electric_cost_savings = electric_cost_old - tlf_electric_cost_new

    pp_electric_cost_new = cogen.calc_annual_electric_cost(chp=chp, demand=demand, ab=ab, tes=tes, load_following_type="PP")
    pp_electric_cost_savings = electric_cost_old - pp_electric_cost_new

    # Total Cost Savings
    elf_total_cost_savings = elf_electric_cost_savings + elf_thermal_cost_savings
    tlf_total_cost_savings = tlf_electric_cost_savings + tlf_thermal_cost_savings
    pp_total_cost_savings = pp_electric_cost_savings + pp_thermal_cost_savings  # TODO: Account for sold electricity

    # Implementation Cost (material cost + installation cost)
    capex_chp_elf = chp.incremental_cost * chp_size_elf
    capex_chp_tlf = chp.incremental_cost * chp_size_tlf
    capex_chp_pp = chp.incremental_cost * chp_size_pp
    capex_tes_elf = tes.incremental_cost * tes_size_elf.to(ureg.kWh)
    capex_tes_tlf = tes.incremental_cost * tes_size_tlf.to(ureg.kWh)
    capex_tes_pp = tes.incremental_cost * tes_size_pp.to(ureg.kWh)
    implementation_cost_elf = capex_chp_elf + capex_tes_elf
    implementation_cost_tlf = capex_chp_tlf + capex_tes_tlf
    implementation_cost_pp = capex_chp_pp + capex_tes_pp

    # Simple Payback Period (implementation cost / annual cost savings)
    elf_simple_payback = (implementation_cost_elf / elf_total_cost_savings) * ureg.year
    tlf_simple_payback = (implementation_cost_tlf / tlf_total_cost_savings) * ureg.year
    pp_simple_payback = (implementation_cost_pp / pp_total_cost_savings) * ureg.year

    """
    Table: Display system property inputs
    """

    head_equipment = ["", "mCHP", "TES", "Aux Boiler"]

    system_properties = [
        ["Thermal Efficiency (Full Load)", "{} %".format(chp.th_nominal_eff * 100), "N/A", "{} %".format(ab.eff * 100)],
        ["Electrical Efficiency (Full Load)", "{} %".format(chp.el_nominal_eff * 100), "N/A", "N/A"],
        ["Minimum Load Operation", "{} %".format(round(chp.min_pl * 100, 2)), "N/A", "{} %".format(round(ab.min_pl * 100, 2))],
        ["ELF Equipment Sizes", round(chp_size_elf.to(ureg.kW), 2), round(tes_size_elf.to(ureg.Btu), 2), ab.cap],
        ["TLF Equipment Sizes", round(chp_size_tlf.to(ureg.kW), 2), round(tes_size_tlf.to(ureg.Btu), 2), ab.cap],
        ["PP Equipment Sizes", round(chp_size_pp.to(ureg.kW), 2), round(tes_size_pp.to(ureg.Btu), 2), ab.cap]
    ]

    table_system_properties = tabulate(system_properties, headers=head_equipment, tablefmt="fancy_grid")
    print(table_system_properties)

    """
    Table: Display key input data
    """

    # head_units = ["", "Value"]
    #
    # input_data = [
    #     ["Location", "{}, {}".format(demand.city, demand.state)]
    #     ["Fuel Cost [$/MMBtu]", round(demand.fuel_cost, 2)],
    #     ["Electricity Rate [$/kWh]", round(demand.el_cost, 2)],
    #     ["CHP Installed Cost, ELF [$]", round(capex_chp_elf.to(ureg.dimensionless), 2)],
    #     ["CHP Installed Cost, TLF [$]", round(capex_chp_tlf, 2)],
    #     ["TES Installed Cost, ELF [$]", round(capex_tes_elf, 2)],
    #     ["TES Installed Cost, TLF [$]", round(capex_tes_tlf, 2)]
    # ]
    #
    # table_input_data = tabulate(input_data, headers=head_units, tablefmt="fancy_grid")
    # print(table_input_data)

    """
    Table: Display Energy Generation by Equipment Type
    """

    head_energy = ["", "ELF", "TLF", "PP"]

    energy = [
        ["Annual Electrical Demand [kWh]", round(demand.annual_el, 2), "N/A", "N/A"],
        ["Peak Electrical Demand [kW]", round(demand.peak_el, 2), "N/A", "N/A"],
        ["CHP Electrical Generation", round(elf_electric_energy_savings.to(ureg.kWh), 2),
         round(tlf_electric_energy_savings.to(ureg.kWh), 2), round(pp_electric_energy_savings.to(ureg.kWh), 2)],
        ["Electrical Energy Bought", round(elf_electricity_bought, 2), round(tlf_electricity_bought, 2),
         round(pp_electricity_bought, 2)],
        ["Electrical Energy Sold", 0, 0, round(pp_electricity_sold, 2)],
        ["Annual Thermal Demand [MMBtu]", round(demand.annual_hl.to(ureg.megaBtu), 2), "N/A", "N/A"],
        ["Peak Thermal Demand [Btu/hr]", round(demand.peak_hl, 2), "N/A", "N/A"],
        ["CHP Thermal Generation", round(elf_chp_thermal_gen, 2),
         round(tlf_chp_thermal_gen, 2), round(pp_chp_thermal_gen, 2)],
        ["TES Thermal Dispatched", round(elf_tes_thermal_dispatch, 2),
         round(tlf_tes_thermal_dispatch, 2), round(pp_tes_thermal_dispatch, 2)],
        ["Boiler Thermal Generation", round(elf_boiler_dispatch, 2), round(tlf_boiler_dispatch, 2),
         round(pp_boiler_dispatch, 2)]
    ]

    table_energy = tabulate(energy, headers=head_energy, tablefmt="fancy_grid")
    print(table_energy)

    """
    Table: Display economic calculations
    """

    # head_costs = ["", "ELF", "TLF", "PP"]
    #
    # costs = [
    #     ["Annual Electrical Demand [kWh]", round(demand.annual_el, 2), "N/A", "N/A"],
    #     ["Annual Thermal Demand [MMBtu]", round(demand.annual_hl.to(ureg.megaBtu), 2), "N/A", "N/A"],
    #     ["Thermal Energy Savings [MMBtu]", round(elf_thermal_energy_savings.to(ureg.megaBtu), 2),
    #      round(tlf_thermal_energy_savings.to(ureg.megaBtu), 2), round(pp_thermal_energy_savings.to(ureg.megaBtu), 2)],
    #     ["Thermal Cost Savings [$]", round(elf_thermal_cost_savings, 2), round(tlf_thermal_cost_savings, 2),
    #      round(pp_thermal_cost_savings, 2)],
    #     ["Electrical Energy Savings [kWh]", round(elf_electric_energy_savings, 2),
    #      round(tlf_electric_energy_savings, 2), round(pp_electric_energy_savings, 2)],
    #     ["Electrical Cost Savings [$]", round(elf_electric_cost_savings, 2), round(tlf_electric_cost_savings, 2),
    #      round(pp_electric_cost_savings, 2)],
    #     ["Total Cost Savings [$]", round(elf_total_cost_savings, 2), round(tlf_total_cost_savings, 2),
    #      round(pp_total_cost_savings, 2)],
    #     ["Simple Payback [Yrs]", round(elf_simple_payback, 2), round(tlf_simple_payback, 2), round(pp_simple_payback)]
    # ]
    #
    # table_costs = tabulate(costs, headers=head_costs, tablefmt="fancy_grid")
    # print(table_costs)

    """
    Table: Display Emissions Analysis
    """

    head_emissions_co2 = ["City, State", "Baseline Electrical Load", "Baseline Heating Load", "Baseline Emissions",
                          "CHP (ELF): Total Annual CO2 (tons)", "CHP (TLF): Total Annual CO2 (tons)",
                          "CHP (PP): Total Annual CO2 (tons)"]

    baseline_total_co2 = emissions.calc_baseline_fuel_emissions(demand=demand) + emissions.calc_baseline_grid_emissions(demand=demand)[1]
    tlf_total_co2 = emissions.calc_chp_emissions(chp=chp, demand=demand, load_following_type="TLF", tes=tes, ab=ab)[1]
    elf_total_co2 = emissions.calc_chp_emissions(chp=chp, demand=demand, load_following_type="ELF", tes=tes, ab=ab)[1]
    pp_total_co2 = emissions.calc_chp_emissions(chp=chp, demand=demand, load_following_type="PP", tes=tes, ab=ab)[1]

    emissions_data_co2 = [
        ["{}, {}".format(demand.city, demand.state), round(demand.annual_el.to(ureg.megaWh)),
         round(demand.annual_hl.to(ureg.megaBtu), 2), round(baseline_total_co2.to(ureg.tons)),
         round(elf_total_co2.to('tons')), round(tlf_total_co2.to('tons')), round(pp_total_co2.to('tons'))],
        ["In SI Units...", round(demand.annual_el.to(ureg.megaWh)), round(demand.annual_hl.to(ureg.megaWh)),
         round(baseline_total_co2.to(ureg.metric_ton)), round(elf_total_co2.to(ureg.metric_ton)),
         round(tlf_total_co2.to(ureg.metric_ton)), round(pp_total_co2.to(ureg.metric_ton))]
    ]

    table_emissions_co2 = tabulate(emissions_data_co2, headers=head_emissions_co2, tablefmt="fancy_grid")
    print(table_emissions_co2)

    """
    Plots
    """

    # plots.plot_max_rectangle_example(demand=demand, chp_size=chp_size_elf)
    #
    # plots.plot_electrical_demand_curve(demand=demand)
    # plots.plot_thermal_demand_curve(demand=demand)
    #
    # plots.elf_plot_electric(chp=chp, demand=demand, ab=ab)
    # plots.elf_plot_thermal(chp=chp, demand=demand, tes=tes, ab=ab)
    # plots.elf_plot_tes_soc(chp=chp, demand=demand, tes=tes, ab=ab)
    #
    # plots.tlf_plot_electric(chp=chp, demand=demand, ab=ab, tes=tes)
    # plots.tlf_plot_thermal(chp=chp, demand=demand, tes=tes, ab=ab)
    # plots.tlf_plot_tes_soc(chp=chp, demand=demand, tes=tes, ab=ab)
    #
    # plots.pp_plot_electric(chp=chp, demand=demand, ab=ab)
    # plots.pp_plot_thermal(chp=chp, demand=demand, tes=tes, ab=ab)
    # plots.pp_plot_tes_soc(chp=chp, demand=demand, tes=tes, ab=ab)


if __name__ == "__main__":
    main()
