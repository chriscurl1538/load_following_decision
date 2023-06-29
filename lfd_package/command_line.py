"""
Module Description:
    Command line interface - imports .yaml file and uses equipment operating parameters
    from the file to initialize the class variables.
TODO: Update all docstrings and documentation
"""

from lfd_package.modules import aux_boiler as boiler, classes, chp as cogen, \
    sizing_calcs as sizing, plots, emissions, thermal_storage as storage, costs
import pathlib, argparse, yaml
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

    # Class initialization using CLI arguments
    demand = classes.EnergyDemand(file_name=data['demand_filename'], city=data['city'], state=data['state'],
                                  grid_efficiency=data['grid_efficiency'],
                                  winter_start_inclusive=data['winter_start_inclusive'],
                                  summer_start_inclusive=data['summer_start_inclusive'])
    emissions_class = classes.Emissions(file_name=data['demand_filename'], city=data['city'], state=data['state'],
                                        grid_efficiency=data['grid_efficiency'],
                                        summer_start_inclusive=data['summer_start_inclusive'],
                                        winter_start_inclusive=data['winter_start_inclusive'])
    costs_class = classes.EnergyCosts(file_name=data['demand_filename'], city=data['city'], state=data['state'],
                                      grid_efficiency=data['grid_efficiency'],
                                      winter_start_inclusive=data['winter_start_inclusive'],
                                      summer_start_inclusive=data['summer_start_inclusive'],
                                      meter_type_el=data['meter_type_el'], meter_type_fuel=data['meter_type_fuel'],
                                      schedule_type_el=data['schedule_type_el'], schedule_type_fuel=data['schedule_type_fuel'],
                                      master_metered_el=data['master_metered_el'], single_metered_el=data['single_metered_el'],
                                      master_metered_fuel=data['master_metered_fuel'], single_metered_fuel=data['single_metered_fuel'])    # TODO: Implement
    chp = classes.CHP(file_name=data['demand_filename'], city=data['city'], state=data['state'],
                      grid_efficiency=data['grid_efficiency'],
                      summer_start_inclusive=data['summer_start_inclusive'],
                      winter_start_inclusive=data['winter_start_inclusive'], turn_down_ratio=data['chp_turn_down'],
                      cost=data['chp_installed_cost'])
    ab = classes.AuxBoiler(file_name=data['demand_filename'], city=data['city'], state=data['state'],
                           grid_efficiency=data['grid_efficiency'], summer_start_inclusive=data['summer_start_inclusive'],
                           winter_start_inclusive=data['winter_start_inclusive'], efficiency=data['ab_eff'])
    tes = classes.TES(file_name=data['demand_filename'], city=data['city'], state=data['state'],
                      grid_efficiency=data['grid_efficiency'],
                      summer_start_inclusive=data['summer_start_inclusive'],
                      winter_start_inclusive=data['winter_start_inclusive'], start=data['tes_init'],
                      cost=data['tes_installed_cost'])

    class_dict = {
        "demand": demand,
        "emissions": emissions_class,
        "costs": costs_class,
        "chp": chp,
        "ab": ab,
        "tes": tes
    }

    return class_dict


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
    class_dict = dict(run(args))

    # Retrieve CHP sizes
    chp_size_tlf = sizing.size_chp(load_following_type='TLF', class_dict=class_dict)
    chp_size_elf = sizing.size_chp(load_following_type='ELF', class_dict=class_dict)
    chp_size_pp = sizing.size_chp(load_following_type='PP', class_dict=class_dict)

    # Initialize dictionaries
    chp_gen_hourly_kwh_dict = {}
    chp_gen_hourly_btuh_dict = {}

    """
    ELF Analysis
    """

    # Electrical Energy Savings
    elf_electric_gen_list = cogen.elf_calc_electricity_generated(chp_size=chp_size_elf, class_dict=class_dict)
    elf_electricity_bought_hourly = cogen.calc_electricity_bought(chp_size=chp_size_elf, class_dict=class_dict,
                                                                  chp_gen_hourly_kwh=elf_electric_gen_list)
    elf_electric_energy_savings = (class_dict['demand'].annual_sum_el - sum(elf_electricity_bought_hourly)).to(ureg.kWh)

    chp_gen_hourly_kwh_dict["ELF"] = elf_electric_gen_list

    # Retrieve TES Size
    tes_size_elf = sizing.size_tes(chp_gen_hourly_kwh_dict=chp_gen_hourly_kwh_dict, chp_size=chp_size_elf,
                                   load_following_type='ELF', class_dict=class_dict)

    # Thermal Energy Savings (current energy consumption - proposed energy consumption)
    thermal_consumption_baseline = class_dict['demand'].annual_sum_hl / class_dict['ab'].eff

    elf_thermal_consumption_chp = cogen.calc_annual_fuel_use(chp_size=chp_size_elf, load_following_type="ELF",
                                                             class_dict=class_dict)
    elf_thermal_consumption_ab = boiler.calc_annual_fuel_use(chp_gen_hourly_kwh_dict=chp_gen_hourly_kwh_dict,
                                                             chp_size=chp_size_elf, tes_size=tes_size_elf,
                                                             load_following_type="ELF", class_dict=class_dict)
    elf_thermal_consumption_total = elf_thermal_consumption_chp + elf_thermal_consumption_ab
    elf_thermal_energy_savings = thermal_consumption_baseline - elf_thermal_consumption_total

    # Thermal Demand Met by Equipment
    elf_chp_gen_btuh = cogen.elf_calc_hourly_heat_generated(chp_gen_hourly_kwh=chp_gen_hourly_kwh_dict["ELF"],
                                                            class_dict=class_dict)
    chp_gen_hourly_btuh_dict["ELF"] = elf_chp_gen_btuh

    # Convert from power to energy
    elf_chp_gen_btu = []
    for item in elf_chp_gen_btuh:
        new_item = (item * Q_(1, ureg.hours)).to(ureg.Btu)
        elf_chp_gen_btu.append(new_item)
    elf_chp_thermal_gen = sum(elf_chp_gen_btu)

    elf_tes_heat_flow_list, elf_tes_soc = \
        storage.calc_tes_heat_flow_and_soc(chp_gen_hourly_kwh_dict=chp_gen_hourly_kwh_dict, tes_size=tes_size_elf,
                                           load_following_type="ELF", class_dict=class_dict)
    # Convert from power to energy
    elf_tes_flow_btu = []
    for item in elf_tes_heat_flow_list:
        new_item = (item * Q_(1, ureg.hours)).to(ureg.Btu)
        elf_tes_flow_btu.append(new_item)
    elf_tes_thermal_dispatch = -1 * sum(item for item in elf_tes_flow_btu if item < 0) * ureg.Btu

    elf_boiler_dispatch_hourly = boiler.calc_aux_boiler_output_rate(chp_gen_hourly_kwh_dict=chp_gen_hourly_kwh_dict,
                                                                    chp_size=chp_size_elf, tes_size=tes_size_elf,
                                                                    class_dict=class_dict, load_following_type="ELF")
    # Convert from power to energy
    elf_boiler_btu = []
    for item in elf_boiler_dispatch_hourly:
        new_item = (item * Q_(1, ureg.hours)).to(ureg.Btu)
        elf_boiler_btu.append(new_item)
    elf_boiler_dispatch = sum(elf_boiler_btu)

    ###############

    # # Thermal Cost Savings (current energy costs - proposed energy costs)
    # thermal_cost_baseline = thermal_consumption_baseline.to(ureg.megaBtu) * demand.fuel_cost     # TODO: Use costs.py
    # elf_thermal_cost_total = elf_thermal_cost_chp + elf_thermal_cost_ab
    # elf_thermal_cost_savings = thermal_cost_baseline - elf_thermal_cost_total

    # Electrical Cost Savings
    electric_cost_baseline = costs.calc_electric_charges(class_dict=class_dict,
                                                         electricity_bought_hourly=class_dict['costs'].el)
    elf_electric_cost_new = costs.calc_electric_charges(class_dict=class_dict,
                                                        electricity_bought_hourly=elf_electricity_bought_hourly)
    elf_electric_cost_savings = electric_cost_baseline - elf_electric_cost_new

    # # Total Cost Savings
    # elf_total_cost_savings = elf_electric_cost_savings + elf_thermal_cost_savings
    #
    # # Implementation Cost (material cost + installation cost)
    # capex_chp_elf = class_dict['chp'].incremental_cost * chp_size_elf
    # capex_tes_elf = class_dict['tes'].incremental_cost * tes_size_elf.to(ureg.kWh)
    # implementation_cost_elf = capex_chp_elf + capex_tes_elf
    #
    # # Simple Payback Period (implementation cost / annual cost savings)
    # elf_simple_payback = (implementation_cost_elf / elf_total_cost_savings) * ureg.year

    """
    TLF Analysis
    """

    # Thermal Demand Met by Equipment
    tlf_chp_gen_btuh, tlf_tes_heat_flow_list, tlf_tes_soc_list = \
        cogen.tlf_calc_hourly_heat_chp_tes_soc(chp_size=chp_size_tlf, class_dict=class_dict)
    chp_gen_hourly_btuh_dict["TLF"] = tlf_chp_gen_btuh

    # Convert from power to energy
    tlf_chp_gen_btu = []
    for item in tlf_chp_gen_btuh:
        new_item = (item * Q_(1, ureg.hours)).to(ureg.Btu)
        tlf_chp_gen_btu.append(new_item)
    tlf_chp_thermal_gen = sum(tlf_chp_gen_btu)

    # Convert from power to energy
    tlf_tes_flow_btu = []
    for item in tlf_tes_heat_flow_list:
        new_item = (item * Q_(1, ureg.hours)).to(ureg.Btu)
        tlf_tes_flow_btu.append(new_item)
    tlf_tes_thermal_dispatch = -1 * sum(item for item in tlf_tes_flow_btu if item < 0)

    # Electrical Energy Savings
    tlf_electric_gen_list = \
        cogen.tlf_calc_electricity_generated(chp_gen_hourly_btuh=chp_gen_hourly_btuh_dict["TLF"], class_dict=class_dict)
    tlf_electricity_bought_hourly = cogen.calc_electricity_bought(chp_gen_hourly_kwh=tlf_electric_gen_list,
                                                                  chp_size=chp_size_tlf, class_dict=class_dict)
    tlf_electric_energy_savings = class_dict['demand'].annual_sum_el - sum(tlf_electricity_bought_hourly)

    chp_gen_hourly_kwh_dict["TLF"] = tlf_electric_gen_list

    # Retrieve TES Size
    tes_size_tlf = sizing.size_tes(chp_gen_hourly_kwh_dict=chp_gen_hourly_kwh_dict, chp_size=chp_size_tlf,
                                   class_dict=class_dict, load_following_type='TLF')

    # Get Boiler Thermal Output
    tlf_boiler_dispatch_hourly = boiler.calc_aux_boiler_output_rate(tes_size=tes_size_tlf, chp_size=chp_size_tlf,
                                                                    class_dict=class_dict, load_following_type="TLF",
                                                                    chp_gen_hourly_kwh_dict=chp_gen_hourly_kwh_dict)
    # Convert from power to energy
    tlf_boiler_btu = []
    for item in tlf_boiler_dispatch_hourly:
        new_item = (item * Q_(1, ureg.hours)).to(ureg.Btu)
        tlf_boiler_btu.append(new_item)
    tlf_boiler_dispatch = sum(tlf_boiler_btu)

    # Thermal Energy Savings (current energy consumption - proposed energy consumption)
    tlf_thermal_consumption_chp = cogen.calc_annual_fuel_use(chp_gen_hourly_btuh=chp_gen_hourly_btuh_dict["TLF"],
                                                             chp_size=chp_size_tlf, class_dict=class_dict,
                                                             load_following_type="TLF")
    tlf_thermal_consumption_ab = \
        boiler.calc_annual_fuel_use(chp_gen_hourly_kwh_dict=chp_gen_hourly_kwh_dict, chp_size=chp_size_tlf,
                                    tes_size=tes_size_tlf, class_dict=class_dict, load_following_type="TLF")
    tlf_thermal_consumption_total = tlf_thermal_consumption_chp + tlf_thermal_consumption_ab
    tlf_thermal_energy_savings = thermal_consumption_baseline - tlf_thermal_consumption_total

    ##################

    # # Thermal Cost Savings (current energy costs - proposed energy costs)
    # tlf_thermal_cost_total = tlf_thermal_cost_chp + tlf_thermal_cost_ab
    # tlf_thermal_cost_savings = thermal_cost_baseline - tlf_thermal_cost_total

    # Electrical Cost Savings
    tlf_electric_cost_new = costs.calc_electric_charges(class_dict=class_dict,
                                                        electricity_bought_hourly=tlf_electricity_bought_hourly)
    tlf_electric_cost_savings = electric_cost_baseline - tlf_electric_cost_new

    # # Total Cost Savings
    # tlf_total_cost_savings = tlf_electric_cost_savings + tlf_thermal_cost_savings
    #
    # # Implementation Cost (material cost + installation cost)
    # capex_chp_tlf = class_dict['chp'].incremental_cost * chp_size_tlf
    # capex_tes_tlf = class_dict['tes'].incremental_cost * tes_size_tlf.to(ureg.kWh)
    # implementation_cost_tlf = capex_chp_tlf + capex_tes_tlf
    #
    # # Simple Payback Period (implementation cost / annual cost savings)
    # tlf_simple_payback = (implementation_cost_tlf / tlf_total_cost_savings) * ureg.year

    """
    PP Analysis
    """

    # Electrical Energy Savings
    pp_electric_gen_list, pp_electric_sold_list = cogen.pp_calc_electricity_gen_sold(chp_size=chp_size_pp,
                                                                                     class_dict=class_dict)
    pp_electricity_bought_hourly = cogen.calc_electricity_bought(chp_gen_hourly_kwh=pp_electric_gen_list,
                                                                 chp_size=chp_size_pp, class_dict=class_dict)
    pp_electric_energy_savings = class_dict['demand'].annual_sum_el - sum(pp_electricity_bought_hourly)

    chp_gen_hourly_kwh_dict["PP"] = pp_electric_gen_list

    # Retrieve TES Size
    tes_size_pp = sizing.size_tes(chp_gen_hourly_kwh_dict=chp_gen_hourly_kwh_dict, chp_size=chp_size_pp,
                                  class_dict=class_dict, load_following_type='PP')

    # # Thermal Energy Savings (current energy consumption - proposed energy consumption)
    # pp_thermal_consumption_chp, pp_thermal_cost_chp = \
    #     cogen.calc_annual_fuel_use_and_costs(chp_size=chp_size_pp, class_dict=class_dict, load_following_type="PP")
    # pp_thermal_consumption_ab, pp_thermal_cost_ab = \
    #     boiler.calc_annual_fuel_use_and_cost(chp_gen_hourly_kwh_dict=chp_gen_hourly_kwh_dict, chp_size=chp_size_pp,
    #                                          tes_size=tes_size_pp, class_dict=class_dict, load_following_type="PP")
    # pp_thermal_consumption_total = pp_thermal_consumption_chp + pp_thermal_consumption_ab
    # pp_thermal_energy_savings = thermal_consumption_baseline - pp_thermal_consumption_total

    # Thermal Demand Met by Equipment
    pp_chp_gen_btuh = cogen.pp_calc_hourly_heat_generated(chp_gen_hourly_kwh=chp_gen_hourly_kwh_dict["PP"],
                                                          class_dict=class_dict)
    chp_gen_hourly_btuh_dict["PP"] = pp_chp_gen_btuh

    # Convert from power to energy
    pp_chp_gen_btu = []
    for item in pp_chp_gen_btuh:
        new_item = (item * Q_(1, ureg.hours)).to(ureg.Btu)
        pp_chp_gen_btu.append(new_item)
    pp_chp_thermal_gen = sum(pp_chp_gen_btu)


    pp_tes_heat_flow_list, pp_tes_soc = \
        storage.calc_tes_heat_flow_and_soc(chp_gen_hourly_kwh_dict=chp_gen_hourly_kwh_dict, tes_size=tes_size_pp,
                                           load_following_type="PP", class_dict=class_dict)
    # Convert from power to energy
    pp_tes_flow_btu = []
    for item in pp_tes_heat_flow_list:
        new_item = (item * Q_(1, ureg.hours)).to(ureg.Btu)
        pp_tes_flow_btu.append(new_item)
    pp_tes_thermal_dispatch = -1 * sum(item for item in pp_tes_flow_btu if item < 0)

    pp_boiler_dispatch_hourly = boiler.calc_aux_boiler_output_rate(chp_gen_hourly_kwh_dict=chp_gen_hourly_kwh_dict,
                                                                   tes_size=tes_size_pp, chp_size=chp_size_pp,
                                                                   class_dict=class_dict, load_following_type="PP")
    # Convert from power to energy
    pp_boiler_btu = []
    for item in pp_boiler_dispatch_hourly:
        new_item = (item * Q_(1, ureg.hours)).to(ureg.Btu)
        pp_boiler_btu.append(new_item)
    pp_boiler_dispatch = sum(pp_boiler_btu)

    ################

    # # Thermal Cost Savings (current energy costs - proposed energy costs)
    # pp_thermal_cost_total = pp_thermal_cost_chp + pp_thermal_cost_ab
    # pp_thermal_cost_savings = thermal_cost_baseline - pp_thermal_cost_total

    # Electrical Cost Savings
    pp_electric_cost_new = costs.calc_electric_charges(class_dict=class_dict,
                                                       electricity_bought_hourly=pp_electricity_bought_hourly)
    pp_revenue = costs.calc_pp_revenue(class_dict=class_dict, electricity_sold_hourly=pp_electric_sold_list)
    pp_electric_cost_savings = electric_cost_baseline - pp_electric_cost_new + pp_revenue

    # # Total Cost Savings
    # pp_total_cost_savings = pp_electric_cost_savings + pp_thermal_cost_savings  # TODO: Account for sold electricity
    #
    # # Implementation Cost (material cost + installation cost)
    # capex_chp_pp = chp.incremental_cost * chp_size_pp
    # capex_tes_pp = tes.incremental_cost * tes_size_pp.to(ureg.kWh)
    # implementation_cost_pp = capex_chp_pp + capex_tes_pp
    #
    # # Simple Payback Period (implementation cost / annual cost savings)
    # pp_simple_payback = (implementation_cost_pp / pp_total_cost_savings) * ureg.year

    """
    Table: Display system property inputs
    """

    head_equipment = ["", "mCHP", "TES", "Aux Boiler"]

    system_properties = [
        ["Minimum Load Operation", "{} %".format(round(class_dict['chp'].min_pl * 100, 2)), "N/A", "N/A"],
        ["ELF Equipment Sizes", round(chp_size_elf.to(ureg.kW), 2), round(tes_size_elf.to(ureg.megaBtu), 3), round(class_dict['ab'].annual_peak_hl, 2)],
        ["TLF Equipment Sizes", round(chp_size_tlf.to(ureg.kW), 2), round(tes_size_tlf.to(ureg.megaBtu), 3), round(class_dict['ab'].annual_peak_hl, 2)],
        ["PP Equipment Sizes", round(chp_size_pp.to(ureg.kW), 2), round(tes_size_pp.to(ureg.megaBtu), 3), round(class_dict['ab'].annual_peak_hl, 2)]
    ]

    table_system_properties = tabulate(system_properties, headers=head_equipment, tablefmt="fancy_grid")
    print(table_system_properties)

    """
    Table: Display key input data
    """

    head_units = ["", "Value"]

    input_data = [
        ["Location", "{}, {}".format(class_dict["demand"].city, class_dict["demand"].state)],
        ["Electric Meter Type", "{}".format(class_dict["costs"].meter_type_el)],
        ["Electric Rate Schedule Type", "{}".format(class_dict["costs"].schedule_type_el)],
        ["Fuel Meter Type", "{}".format(class_dict["costs"].meter_type_fuel)],
        ["Electric Rate Schedule Type", "{}".format(class_dict["costs"].schedule_type_fuel)]
    ]

    table_input_data = tabulate(input_data, headers=head_units, tablefmt="fancy_grid")
    print(table_input_data)

    """
    Table: Display Energy Generation by Equipment Type
    """

    head_energy = ["", "ELF", "TLF", "PP"]

    energy = [
        ["Annual Electrical Demand [kWh]", round(class_dict['demand'].annual_sum_el.to(ureg.megaWh), 2), "N/A", "N/A"],
        ["Peak Electrical Demand [kW]", round(class_dict['demand'].annual_peak_el, 2), "N/A", "N/A"],
        ["CHP Electrical Generation", round(elf_electric_energy_savings.to(ureg.kWh), 2),
         round(tlf_electric_energy_savings.to(ureg.kWh), 2), round(pp_electric_energy_savings.to(ureg.kWh), 2)],
        ["Electrical Energy Bought", round(sum(elf_electricity_bought_hourly), 2), round(sum(tlf_electricity_bought_hourly), 2),
         round(sum(pp_electricity_bought_hourly), 2)],
        # ["Electrical Energy Sold", 0, 0, round(pp_electricity_sold, 2)],
        ["Annual Thermal Demand [MMBtu]", round(class_dict['demand'].annual_sum_hl.to(ureg.megaBtu), 3), "N/A", "N/A"],
        ["Peak Thermal Demand [MMBtu/hr]", round(class_dict['demand'].annual_peak_hl.to(ureg.megaBtu / ureg.hours), 3), "N/A", "N/A"],
        ["CHP Thermal Generation", round(elf_chp_thermal_gen.to(ureg.megaBtu), 2),
         round(tlf_chp_thermal_gen.to(ureg.megaBtu), 2), round(pp_chp_thermal_gen.to(ureg.megaBtu), 2)],
        ["TES Thermal Dispatched", round(elf_tes_thermal_dispatch.to(ureg.megaBtu), 2),
         round(tlf_tes_thermal_dispatch.to(ureg.megaBtu), 2), round(pp_tes_thermal_dispatch.to(ureg.megaBtu), 2)],
        ["Boiler Thermal Generation", round(elf_boiler_dispatch.to(ureg.megaBtu), 2),
         round(tlf_boiler_dispatch.to(ureg.megaBtu), 2), round(pp_boiler_dispatch.to(ureg.megaBtu), 2)]
    ]

    table_energy = tabulate(energy, headers=head_energy, tablefmt="fancy_grid")
    print(table_energy)

    """
    Table: Display economic calculations
    """

    head_costs = ["", "ELF", "TLF", "PP"]

    costs_table = [
        # ["Thermal Energy Savings [MMBtu]", round(elf_thermal_energy_savings.to(ureg.megaBtu), 2),
        #  round(tlf_thermal_energy_savings.to(ureg.megaBtu), 2), round(pp_thermal_energy_savings.to(ureg.megaBtu), 2)],
        # ["Thermal Cost Savings [$]", round(elf_thermal_cost_savings, 2), round(tlf_thermal_cost_savings, 2),
        #  round(pp_thermal_cost_savings, 2)],
        ["Electrical Energy Savings [kWh]", round(elf_electric_energy_savings.to('kWh'), 2),
         round(tlf_electric_energy_savings.to('kWh'), 2), round(pp_electric_energy_savings.to('kWh'), 2)],
        ["Electrical Cost Savings [$]", round(elf_electric_cost_savings, 2), round(tlf_electric_cost_savings, 2),
         round(pp_electric_cost_savings, 2)],
        # ["Total Cost Savings [$]", round(elf_total_cost_savings, 2), round(tlf_total_cost_savings, 2),
        #  round(pp_total_cost_savings, 2)],
        # ["Simple Payback [Yrs]", round(elf_simple_payback, 2), round(tlf_simple_payback, 2), round(pp_simple_payback)]
    ]

    table_costs = tabulate(costs_table, headers=head_costs, tablefmt="fancy_grid")
    print(table_costs)

    """
    Table: Display Emissions Analysis
    """

    head_emissions_co2 = ["City, State", "Baseline Electrical Load", "Baseline Heating Load", "Baseline Emissions",
                          "CHP (ELF): Total Annual CO2 (tons)", "CHP (TLF): Total Annual CO2 (tons)",
                          "CHP (PP): Total Annual CO2 (tons)"]

    baseline_total_co2 = emissions.calc_baseline_fuel_emissions(class_dict=class_dict) + \
        emissions.calc_baseline_grid_emissions(class_dict=class_dict)[1]

    tlf_total_co2 = emissions.calc_chp_emissions(chp_gen_hourly_btuh=chp_gen_hourly_btuh_dict["TLF"],
                                                 chp_gen_hourly_kwh_dict=chp_gen_hourly_kwh_dict, chp_size=chp_size_tlf,
                                                 tes_size=tes_size_tlf, load_following_type="TLF", class_dict=class_dict)[1]
    elf_total_co2 = emissions.calc_chp_emissions(chp_gen_hourly_btuh=chp_gen_hourly_btuh_dict["ELF"],
                                                 chp_gen_hourly_kwh_dict=chp_gen_hourly_kwh_dict, chp_size=chp_size_elf,
                                                 tes_size=tes_size_elf, load_following_type="ELF", class_dict=class_dict)[1]
    pp_total_co2 = emissions.calc_chp_emissions(chp_gen_hourly_btuh=chp_gen_hourly_btuh_dict["PP"],
                                                chp_gen_hourly_kwh_dict=chp_gen_hourly_kwh_dict, chp_size=chp_size_pp,
                                                tes_size=tes_size_pp, load_following_type="PP", class_dict=class_dict)[1]

    emissions_data_co2 = [
        ["{}, {}".format(class_dict['demand'].city, class_dict['demand'].state), round(class_dict['demand'].annual_sum_el.to(ureg.megaWh)),
         round(class_dict['demand'].annual_sum_hl.to(ureg.megaBtu), 2), round(baseline_total_co2.to(ureg.tons)),
         round(elf_total_co2.to('tons')), round(tlf_total_co2.to('tons')), round(pp_total_co2.to('tons'))],
        ["In SI Units...", round(class_dict['demand'].annual_sum_el.to(ureg.megaWh)), round(class_dict['demand'].annual_sum_hl.to(ureg.megaWh)),
         round(baseline_total_co2.to(ureg.metric_ton)), round(elf_total_co2.to(ureg.metric_ton)),
         round(tlf_total_co2.to(ureg.metric_ton)), round(pp_total_co2.to(ureg.metric_ton))]
    ]

    table_emissions_co2 = tabulate(emissions_data_co2, headers=head_emissions_co2, tablefmt="fancy_grid")
    print(table_emissions_co2)

    """
    Plots
    """

    plots.plot_max_rectangle_example(demand=class_dict['demand'], chp_size=chp_size_elf)

    plots.plot_electrical_demand_curve(demand=class_dict['demand'])
    plots.plot_thermal_demand_curve(demand=class_dict['demand'])

    plots.elf_plot_electric(elf_electric_gen_list=elf_electric_gen_list,
                            elf_electricity_bought_list=elf_electricity_bought_hourly, demand=class_dict['demand'])
    plots.elf_plot_thermal(elf_chp_gen_btuh=elf_chp_gen_btuh, elf_tes_heat_flow_list=elf_tes_heat_flow_list,
                           elf_boiler_dispatch_hourly=elf_boiler_dispatch_hourly, demand=class_dict['demand'])
    plots.elf_plot_tes_soc(elf_tes_soc=elf_tes_soc)

    plots.tlf_plot_electric(tlf_electric_gen_list=tlf_electric_gen_list,
                            tlf_electricity_bought_list=tlf_electricity_bought_hourly, demand=class_dict['demand'])
    plots.tlf_plot_thermal(tlf_chp_gen_btuh=tlf_chp_gen_btuh, tlf_tes_heat_flow_list=tlf_tes_heat_flow_list,
                           tlf_boiler_dispatch_hourly=tlf_boiler_dispatch_hourly, demand=class_dict['demand'])
    plots.tlf_plot_tes_soc(tlf_tes_soc_list=tlf_tes_soc_list)

    plots.pp_plot_electric(pp_electric_gen_list=pp_electric_gen_list,
                           pp_electricity_bought_list=pp_electricity_bought_hourly,
                           pp_electricity_sold_list=pp_electric_sold_list, demand=class_dict['demand'])
    plots.pp_plot_thermal(pp_chp_gen_btuh=pp_chp_gen_btuh, pp_tes_heat_flow_list=pp_tes_heat_flow_list,
                          pp_boiler_dispatch_hourly=pp_boiler_dispatch_hourly, demand=class_dict['demand'])
    plots.pp_plot_tes_soc(pp_tes_soc=pp_tes_soc)


if __name__ == "__main__":
    main()
