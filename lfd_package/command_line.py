"""
Module Description:
    Command line interface - imports .yaml file and uses equipment operating parameters
    from the file to initialize the class variables.
TODO: Reduce calculation times by eliminating redundant function calls. Make new branch for this
TODO: Update all docstrings
"""

from lfd_package.modules import aux_boiler as boiler, classes, chp as cogen, \
    sizing_calcs as sizing, plots, emissions
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
    chp = classes.CHP(fuel_input_rate=data['fuel_input_rate'],
                      turn_down_ratio=data['chp_turn_down'], part_load_electrical=part_load_electrical_array,
                      part_load_thermal=part_load_thermal_array, chp_electric_eff=data['Electrical'][100],
                      chp_thermal_eff=data['Thermal'][100], percent_availability=data['percent_availability'],
                      cost=data['chp_installed_cost'])
    ab = classes.AuxBoiler(capacity=data['ab_capacity'], efficiency=data['ab_eff'],
                           turn_down_ratio=data['ab_turn_down'])
    demand = classes.EnergyDemand(file_name=data['demand_filename'], net_metering_status=data['net_metering_status'],
                                  grid_efficiency=data['grid_efficiency'],
                                  electric_cost=data['electric_utility_cost'],
                                  fuel_cost=data['fuel_cost'], city=data['city'], state=data['state'])
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

    """
    Energy Analysis
    """

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

    # Electrical Energy Savings
    elf_electric_energy_savings = sum(cogen.elf_calc_electricity_bought_and_generated(chp=chp, demand=demand, ab=ab)[1])
    tlf_electric_energy_savings = sum(cogen.tlf_calc_electricity_bought_and_generated(chp=chp, demand=demand, ab=ab)[1])

    """
    Economic Analysis
    """

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

    """
    Emissions Analysis
    """

    emissions_elf = emissions.compare_emissions(chp=chp, demand=demand, load_following_type='ELF', ab=ab, tes=tes)
    emissions_tlf = emissions.compare_emissions(chp=chp, demand=demand, load_following_type='TLF', ab=ab, tes=tes)

    """
    Table: Display system property inputs
    """

    head_equipment = ["", "mCHP", "TES", "Aux Boiler"]

    system_properties = [
        ["Thermal Efficiency (Full Load)", "{} %".format(chp.th_nominal_eff * 100), "N/A", "{} %".format(ab.eff * 100)],
        ["Electrical Efficiency (Full Load)", "{} %".format(chp.el_nominal_eff * 100), "N/A", "N/A"],
        ["Minimum Load Operation", "{} %".format(round(chp.min_pl * 100, 2)), "N/A", "{} %".format(round(ab.min_pl * 100, 2))],
        ["ELF Equipment Sizes", round(chp_size_elf.to(ureg.kW), 2), tes_size_elf.to(ureg.megaBtu), ab.cap],
        ["TLF Equipment Sizes", round(chp_size_tlf.to(ureg.kW), 2), tes_size_tlf.to(ureg.megaBtu), ab.cap]
    ]

    table_system_properties = tabulate(system_properties, headers=head_equipment, tablefmt="fancy_grid")
    print(table_system_properties)

    """
    Table: Display key input data
    """

    head_units = ["", "Value"]

    input_data = [
        ["Location", "{}, {}".format(demand.city, demand.state)],
        ["Fuel Cost [$/MMBtu]", round(demand.fuel_cost, 2)],
        ["Electricity Rate [$/kWh]", round(demand.el_cost, 2)],
        ["CHP Installed Cost, ELF [$]", round(capex_chp_elf.to(ureg.dimensionless), 2)],
        ["CHP Installed Cost, TLF [$]", round(capex_chp_tlf, 2)],
        ["TES Installed Cost, ELF [$]", round(capex_tes_elf, 2)],
        ["TES Installed Cost, TLF [$]", round(capex_tes_tlf, 2)]
    ]

    table_input_data = tabulate(input_data, headers=head_units, tablefmt="fancy_grid")
    print(table_input_data)

    """
    Table: Display economic calculations
    """

    head_comparison = ["", "ELF", "TLF"]

    costs = [
        ["Annual Electrical Demand [kWh]", round(demand.annual_el, 2), "N/A"],
        ["Annual Thermal Demand [MMBtu]", round(demand.annual_hl.to(ureg.megaBtu), 2), "N/A"],
        ["Thermal Energy Savings [MMBtu]", round(elf_thermal_energy_savings.to(ureg.megaBtu), 2),
         round(tlf_thermal_energy_savings.to(ureg.megaBtu), 2)],
        ["Thermal Cost Savings [$]", round(elf_thermal_cost_savings, 2),
         round(tlf_thermal_cost_savings, 2)],
        ["Electrical Energy Savings [kWh]", round(elf_electric_energy_savings, 2),
         round(tlf_electric_energy_savings, 2)],
        ["Electrical Cost Savings [$]", round(elf_electric_cost_savings, 2),
         round(tlf_electric_cost_savings, 2)],
        ["Total Cost Savings [$]", round(elf_total_cost_savings, 2),
         round(tlf_total_cost_savings, 2)],
        ["Simple Payback [Yrs]", round(elf_simple_payback, 2),
         round(tlf_simple_payback, 2)]
    ]

    table_costs = tabulate(costs, headers=head_comparison, tablefmt="fancy_grid")
    print(table_costs)

    """
    Table: Display Emissions Analysis
    """

    head_location = ["City, State", "Climate Zone"]

    emissions_data_co2 = [
        ["Seattle, WA", "4C - Marine"],
        ["Miami, FL", "1A - Warm, Humid"],
        ["Duluth, MN", "7 - Cold, Humid"],
        ["Pheonix, AZ", "2B - Warm, Dry"],
        ["Helena, MT", "6B - Cold, Dry"]
    ]

    table_location = tabulate(emissions_data_co2, headers=head_location, tablefmt="fancy_grid")
    print(table_location)

    head_emissions_co2 = ["City, State", "CHP (ELF): Annual Delta CO2 (tons)", "CHP (TLF): Annual Delta CO2 (tons)"]

    emissions_data_co2 = [
        ["{}, {}".format(demand.city, demand.state), round(emissions_elf.to('tons'), 2), round(emissions_tlf.to('tons'), 2)]
    ]

    table_emissions_co2 = tabulate(emissions_data_co2, headers=head_emissions_co2, tablefmt="fancy_grid")
    print(table_emissions_co2)

    """
    Plots
    """

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

    """
    head_emissions_nox = ["City, State", "Climate Zone", "CHP (ELF): Annual Delta NOx (tons)",
                          "CHP (TLF): Annual Delta NOx (tons)"]

    emissions_data_nox = [
        ["Seattle, WA", "4C - Marine", round(seattle_elf['nox'].to('tons'), 2), round(seattle_tlf['nox'].to('tons'), 2)],
        ["Miami, FL", "1A - Warm, Humid", round(miami_elf['nox'].to('tons'), 2), round(miami_tlf['nox'].to('tons'), 2)],
        ["Duluth, MN", "7 - Cold, Humid", round(duluth_elf['nox'].to('tons'), 2), round(duluth_tlf['nox'].to('tons'), 2)],
        ["Pheonix, AZ", "2B - Warm, Dry", round(pheonix_elf['nox'].to('tons'), 2), round(pheonix_tlf['nox'].to('tons'), 2)],
        ["Helena, MT", "6B - Cold, Dry", round(helena_elf['nox'].to('tons'), 2), round(helena_tlf['nox'].to('tons'), 2)]
    ]

    table_emissions_nox = tabulate(emissions_data_nox, headers=head_emissions_nox, tablefmt="fancy_grid")
    print(table_emissions_nox)

    head_emissions_so2 = ["City, State", "Climate Zone", "CHP (ELF): Annual Delta SO2 (tons)",
                          "CHP (TLF): Annual Delta SO2 (tons)"]

    emissions_data_so2 = [
        ["Seattle, WA", "4C - Marine", round(seattle_elf['so2'].to('tons'), 2), round(seattle_tlf['so2'].to('tons'), 2)],
        ["Miami, FL", "1A - Warm, Humid", round(miami_elf['so2'].to('tons'), 2), round(miami_tlf['so2'].to('tons'), 2)],
        ["Duluth, MN", "7 - Cold, Humid", round(duluth_elf['so2'].to('tons'), 2), round(duluth_tlf['so2'].to('tons'), 2)],
        ["Pheonix, AZ", "2B - Warm, Dry", round(pheonix_elf['so2'].to('tons'), 2), round(pheonix_tlf['so2'].to('tons'), 2)],
        ["Helena, MT", "6B - Cold, Dry", round(helena_elf['so2'].to('tons'), 2), round(helena_tlf['so2'].to('tons'), 2)]
    ]

    table_emissions_so2 = tabulate(emissions_data_so2, headers=head_emissions_so2, tablefmt="fancy_grid")
    print(table_emissions_so2)

    head_emissions_pm = ["City, State", "Climate Zone", "CHP (ELF): Annual Delta PM2.5 (tons)",
                          "CHP (TLF): Annual Delta PM2.5 (tons)"]

    emissions_data_pm = [
        ["Seattle, WA", "4C - Marine", round(seattle_elf['pm'].to('tons'), 2), round(seattle_tlf['pm'].to('tons'), 2)],
        ["Miami, FL", "1A - Warm, Humid", round(miami_elf['pm'].to('tons'), 2), round(miami_tlf['pm'].to('tons'), 2)],
        ["Duluth, MN", "7 - Cold, Humid", round(duluth_elf['pm'].to('tons'), 2),
         round(duluth_tlf['pm'].to('tons'), 2)],
        ["Pheonix, AZ", "2B - Warm, Dry", round(pheonix_elf['pm'].to('tons'), 2),
         round(pheonix_tlf['pm'].to('tons'), 2)],
        ["Helena, MT", "6B - Cold, Dry", round(helena_elf['pm'].to('tons'), 2), round(helena_tlf['pm'].to('tons'), 2)]
    ]

    table_emissions_pm = tabulate(emissions_data_pm, headers=head_emissions_pm, tablefmt="fancy_grid")
    print(table_emissions_pm)

    head_emissions_voc = ["City, State", "Climate Zone", "CHP (ELF): Annual Delta VOC (tons)",
                         "CHP (TLF): Annual Delta VOC (tons)"]

    emissions_data_voc = [
        ["Seattle, WA", "4C - Marine", round(seattle_elf['voc'].to('tons'), 2), round(seattle_tlf['voc'].to('tons'), 2)],
        ["Miami, FL", "1A - Warm, Humid", round(miami_elf['voc'].to('tons'), 2), round(miami_tlf['voc'].to('tons'), 2)],
        ["Duluth, MN", "7 - Cold, Humid", round(duluth_elf['voc'].to('tons'), 2),
         round(duluth_tlf['voc'].to('tons'), 2)],
        ["Pheonix, AZ", "2B - Warm, Dry", round(pheonix_elf['voc'].to('tons'), 2),
         round(pheonix_tlf['voc'].to('tons'), 2)],
        ["Helena, MT", "6B - Cold, Dry", round(helena_elf['voc'].to('tons'), 2), round(helena_tlf['voc'].to('tons'), 2)]
    ]

    table_emissions_voc = tabulate(emissions_data_voc, headers=head_emissions_voc, tablefmt="fancy_grid")
    print(table_emissions_voc)

    head_emissions_nh3 = ["City, State", "Climate Zone", "CHP (ELF): Annual Delta NH3 (tons)",
                          "CHP (TLF): Annual Delta NH3 (tons)"]

    emissions_data_nh3 = [
        ["Seattle, WA", "4C - Marine", round(seattle_elf['nh3'].to('tons'), 2),
         round(seattle_tlf['nh3'].to('tons'), 2)],
        ["Miami, FL", "1A - Warm, Humid", round(miami_elf['nh3'].to('tons'), 2), round(miami_tlf['nh3'].to('tons'), 2)],
        ["Duluth, MN", "7 - Cold, Humid", round(duluth_elf['nh3'].to('tons'), 2),
         round(duluth_tlf['nh3'].to('tons'), 2)],
        ["Pheonix, AZ", "2B - Warm, Dry", round(pheonix_elf['nh3'].to('tons'), 2),
         round(pheonix_tlf['nh3'].to('tons'), 2)],
        ["Helena, MT", "6B - Cold, Dry", round(helena_elf['nh3'].to('tons'), 2), round(helena_tlf['nh3'].to('tons'), 2)]
    ]

    table_emissions_nh3 = tabulate(emissions_data_nh3, headers=head_emissions_nh3, tablefmt="fancy_grid")
    print(table_emissions_nh3)
    """
