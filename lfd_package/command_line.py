"""
Module Description:
    Command line interface - imports .yaml file and uses equipment operating parameters
    from the file to initialize the class variables.
TODO: Update all docstrings and documentation
"""

from lfd_package.modules import aux_boiler as boiler, classes, chp as cogen
from lfd_package.modules import sizing_calcs as sizing, plots, emissions
from lfd_package.modules import thermal_storage as storage, costs, sa
from SALib.sample import saltelli
from SALib.analyze import sobol
# from SALib.test_functions import Ishigami
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

    # Class initialization using CLI arguments
    demand = classes.EnergyDemand(file_name=data['demand_filename'], city=data['city'], state=data['state'],
                                  grid_efficiency=data['grid_efficiency'],
                                  winter_start_inclusive=data['winter_start_inclusive'],
                                  summer_start_inclusive=data['summer_start_inclusive'], sim_ab_efficiency=data["energy_plus_eff"])
    emissions_class = classes.Emissions(file_name=data['demand_filename'], city=data['city'], state=data['state'],
                                        grid_efficiency=data['grid_efficiency'],
                                        summer_start_inclusive=data['summer_start_inclusive'],
                                        winter_start_inclusive=data['winter_start_inclusive'], sim_ab_efficiency=data["energy_plus_eff"])
    costs_class = classes.EnergyCosts(file_name=data['demand_filename'], city=data['city'], state=data['state'],
                                      grid_efficiency=data['grid_efficiency'], no_apts=data['no_apts'],
                                      winter_start_inclusive=data['winter_start_inclusive'],
                                      summer_start_inclusive=data['summer_start_inclusive'], sim_ab_efficiency=data["energy_plus_eff"],
                                      meter_type_el=data['meter_type_el'], meter_type_fuel=data['meter_type_fuel'],
                                      schedule_type_el=data['schedule_type_el'], schedule_type_fuel=data['schedule_type_fuel'],
                                      master_metered_el=data['master_metered_el'], single_metered_el=data['single_metered_el'],
                                      master_metered_fuel=data['master_metered_fuel'],
                                      single_metered_fuel=data['single_metered_fuel'])    # TODO: Implement
    chp = classes.CHP(file_name=data['demand_filename'], city=data['city'], state=data['state'],
                      grid_efficiency=data['grid_efficiency'], sim_ab_efficiency=data["energy_plus_eff"],
                      summer_start_inclusive=data['summer_start_inclusive'],
                      winter_start_inclusive=data['winter_start_inclusive'], turn_down_ratio=data['chp_turn_down'],
                      installed_cost=data['chp_installed_cost'])
    ab = classes.AuxBoiler(file_name=data['demand_filename'], city=data['city'], state=data['state'],
                           grid_efficiency=data['grid_efficiency'], summer_start_inclusive=data['summer_start_inclusive'],
                           winter_start_inclusive=data['winter_start_inclusive'], sim_ab_efficiency=data["energy_plus_eff"],
                           efficiency=data['ab_eff'])
    tes = classes.TES(file_name=data['demand_filename'], city=data['city'], state=data['state'],
                      grid_efficiency=data['grid_efficiency'], sim_ab_efficiency=data["energy_plus_eff"],
                      summer_start_inclusive=data['summer_start_inclusive'], vol_rate=data['tes_vol_rate'],
                      winter_start_inclusive=data['winter_start_inclusive'], start=data['tes_init'],
                      size_cost=data['tes_size_cost'], rate_cost=data['tes_rate_cost'],
                      energy_density=data['tes_energy_density'])

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
    chp_size_pp = sizing.size_chp(load_following_type="PP", class_dict=class_dict)
    chp_size_peak = class_dict["demand"].annual_peak_el

    # Initialize empty dictionaries
    chp_gen_hourly_kwh_dict = {}
    chp_gen_hourly_btuh_dict = {}

    ##########################################################################################################

    """
    ELF Analysis
    """

    ###########################
    # Electrical Energy Savings
    ###########################
    elf_electric_gen_list = cogen.elf_calc_electricity_generated(chp_size=chp_size_elf, class_dict=class_dict)
    elf_electricity_bought_hourly = cogen.calc_electricity_bought(chp_size=chp_size_elf, class_dict=class_dict,
                                                                  chp_gen_hourly_kwh=elf_electric_gen_list)
    elf_electric_energy_savings = (class_dict['demand'].annual_sum_el - sum(elf_electricity_bought_hourly)).to(ureg.kWh)

    chp_gen_hourly_kwh_dict["ELF"] = elf_electric_gen_list

    # Retrieve TES Size
    tes_size_elf = sizing.size_tes(chp_gen_hourly_kwh_dict=chp_gen_hourly_kwh_dict, chp_size=chp_size_elf,
                                   load_following_type='ELF', class_dict=class_dict)

    ###########################
    # Thermal Demand Met by Equipment
    ###########################
    elf_chp_gen_btuh = cogen.elf_calc_hourly_heat_generated(chp_gen_hourly_kwh=chp_gen_hourly_kwh_dict["ELF"],
                                                            class_dict=class_dict)
    chp_gen_hourly_btuh_dict["ELF"] = elf_chp_gen_btuh

    # Convert from power to energy
    elf_chp_gen_btu = class_dict['demand'].convert_units(units_to_str="Btu", values_list=elf_chp_gen_btuh)
    elf_chp_thermal_gen = sum(elf_chp_gen_btu)

    elf_tes_heat_flow_list, elf_tes_soc = \
        storage.calc_tes_heat_flow_and_soc(chp_gen_hourly_kwh_dict=chp_gen_hourly_kwh_dict, tes_size=tes_size_elf,
                                           load_following_type="ELF", class_dict=class_dict)
    # Convert from power to energy
    elf_tes_heat_flow_btu = \
        class_dict['demand'].convert_units(units_to_str="Btu", values_list=elf_tes_heat_flow_list)
    elf_tes_thermal_dispatch = -1 * sum(flow for flow in elf_tes_heat_flow_btu if flow < 0) * ureg.Btu
    assert elf_tes_thermal_dispatch.units == ureg.Btu

    elf_boiler_dispatch_hourly = boiler.calc_aux_boiler_output_rate(chp_gen_hourly_kwh_dict=chp_gen_hourly_kwh_dict,
                                                                    chp_size=chp_size_elf, tes_size=tes_size_elf,
                                                                    class_dict=class_dict, load_following_type="ELF")
    # Convert from power to energy
    elf_boiler_btu = class_dict["demand"].convert_units(units_to_str="Btu", values_list=elf_boiler_dispatch_hourly)
    elf_boiler_dispatch = sum(elf_boiler_btu)

    ###########################
    # Thermal Energy Savings (current energy consumption - proposed energy consumption)
    ###########################
    thermal_consumption_baseline = class_dict['demand'].annual_sum_hl / class_dict['ab'].eff

    elf_thermal_consumption_hourly_chp = cogen.calc_hourly_fuel_use(chp_size=chp_size_elf, load_following_type="ELF",
                                                                    class_dict=class_dict)
    elf_thermal_consumption_hourly_ab = boiler.calc_hourly_fuel_use(ab_output_rate_list=elf_boiler_dispatch_hourly,
                                                                    class_dict=class_dict)
    elf_thermal_consumption_total = sum(elf_thermal_consumption_hourly_chp) + sum(elf_thermal_consumption_hourly_ab)
    elf_thermal_energy_savings = thermal_consumption_baseline - elf_thermal_consumption_total

    # TODO: Replace some of the following lines with payback period calc function (see sa.py)
    ###########################
    # Thermal Cost Savings (current energy costs - proposed energy costs)
    ###########################
    thermal_consumption_baseline_hourly = []
    for item in class_dict['demand'].hl:
        new_item = item / class_dict['ab'].eff
        thermal_consumption_baseline_hourly.append(new_item)

    thermal_cost_baseline = costs.calc_fuel_charges(class_dict=class_dict,
                                                    fuel_bought_hourly=thermal_consumption_baseline_hourly)

    elf_fuel_use_list = []
    for index, item in enumerate(thermal_consumption_baseline_hourly):
        hourly_fuel = elf_thermal_consumption_hourly_chp[index] + elf_thermal_consumption_hourly_ab[index]
        elf_fuel_use_list.append(hourly_fuel)

    elf_thermal_cost_total = costs.calc_fuel_charges(class_dict=class_dict, fuel_bought_hourly=elf_fuel_use_list)
    elf_thermal_cost_savings = thermal_cost_baseline - elf_thermal_cost_total

    ###########################
    # Electrical Cost Savings
    ###########################
    electric_cost_baseline = costs.calc_electric_charges(class_dict=class_dict,
                                                         electricity_bought_hourly=class_dict['costs'].el)
    elf_electric_cost_new = costs.calc_electric_charges(class_dict=class_dict,
                                                        electricity_bought_hourly=elf_electricity_bought_hourly)
    elf_electric_cost_savings = electric_cost_baseline - elf_electric_cost_new

    ###########################
    # Total Cost Savings
    ###########################
    elf_total_cost_savings = elf_electric_cost_savings + elf_thermal_cost_savings

    ###########################
    # Implementation Cost (material cost + installation cost)
    ###########################
    installed_cost_chp_elf = costs.calc_installed_cost(class_dict=class_dict, size=chp_size_elf, class_str="chp",
                                                       dispatch_hourly=chp_gen_hourly_kwh_dict["ELF"])
    installed_cost_tes_elf = costs.calc_installed_cost(class_dict=class_dict, size=tes_size_elf, class_str="tes",
                                                       dispatch_hourly=elf_tes_heat_flow_list)
    implementation_cost_elf = installed_cost_chp_elf + installed_cost_tes_elf

    ###########################
    # Simple Payback Period (implementation cost / annual cost savings)
    ###########################
    elf_simple_payback = (implementation_cost_elf / elf_total_cost_savings) * ureg.year

    ##########################################################################################################

    """
    TLF Analysis
    """

    ###########################
    # Thermal Demand Met by Equipment
    ###########################
    tlf_chp_gen_btuh, tlf_tes_heat_flow_list, tlf_tes_soc_list = \
        cogen.tlf_calc_hourly_heat_chp_tes_soc(chp_size=chp_size_tlf, class_dict=class_dict)
    chp_gen_hourly_btuh_dict["TLF"] = tlf_chp_gen_btuh

    # Convert from power to energy
    tlf_chp_gen_btu = class_dict["demand"].convert_units(units_to_str="Btu", values_list=tlf_chp_gen_btuh)
    tlf_chp_thermal_gen = sum(tlf_chp_gen_btu)

    # Convert from power to energy
    tlf_tes_flow_btu = class_dict["demand"].convert_units(units_to_str="Btu", values_list=tlf_tes_heat_flow_list)
    tlf_tes_thermal_dispatch = -1 * sum(item for item in tlf_tes_flow_btu if item < 0)
    assert tlf_tes_thermal_dispatch.units == ureg.Btu

    ###########################
    # Electrical Energy Savings
    ###########################
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
    tlf_boiler_btu = class_dict["demand"].convert_units(units_to_str="Btu", values_list=tlf_boiler_dispatch_hourly)
    tlf_boiler_dispatch = sum(tlf_boiler_btu)

    ###########################
    # Thermal Energy Savings (current energy consumption - proposed energy consumption)
    ###########################
    tlf_thermal_consumption_hourly_chp = cogen.calc_hourly_fuel_use(chp_gen_hourly_btuh=chp_gen_hourly_btuh_dict["TLF"],
                                                                    chp_size=chp_size_tlf, class_dict=class_dict,
                                                                    load_following_type="TLF")
    tlf_thermal_consumption_hourly_ab = \
        boiler.calc_hourly_fuel_use(ab_output_rate_list=tlf_boiler_dispatch_hourly, class_dict=class_dict)
    tlf_thermal_consumption_total = sum(tlf_thermal_consumption_hourly_chp) + sum(tlf_thermal_consumption_hourly_ab)
    tlf_thermal_energy_savings = thermal_consumption_baseline - tlf_thermal_consumption_total

    ###########################
    # Thermal Cost Savings (current energy costs - proposed energy costs)
    ###########################

    tlf_fuel_use_list = []
    for index, item in enumerate(thermal_consumption_baseline_hourly):
        hourly_fuel = tlf_thermal_consumption_hourly_chp[index] + tlf_thermal_consumption_hourly_ab[index]
        tlf_fuel_use_list.append(hourly_fuel)

    tlf_thermal_cost_total = costs.calc_fuel_charges(class_dict=class_dict,
                                                     fuel_bought_hourly=tlf_fuel_use_list)
    tlf_thermal_cost_savings = thermal_cost_baseline - tlf_thermal_cost_total

    ###########################
    # Electrical Cost Savings
    ###########################
    tlf_electric_cost_new = costs.calc_electric_charges(class_dict=class_dict,
                                                        electricity_bought_hourly=tlf_electricity_bought_hourly)
    tlf_electric_cost_savings = electric_cost_baseline - tlf_electric_cost_new

    ###########################
    # Total Cost Savings
    ###########################
    tlf_total_cost_savings = tlf_electric_cost_savings + tlf_thermal_cost_savings

    ###########################
    # Implementation Cost (material cost + installation cost)
    ###########################
    installed_cost_chp_tlf = costs.calc_installed_cost(class_dict=class_dict, size=chp_size_tlf, class_str="chp",
                                                       dispatch_hourly=chp_gen_hourly_kwh_dict["TLF"])
    installed_cost_tes_tlf = costs.calc_installed_cost(class_dict=class_dict, size=tes_size_tlf, class_str="tes",
                                                       dispatch_hourly=tlf_tes_heat_flow_list)
    implementation_cost_tlf = installed_cost_chp_tlf + installed_cost_tes_tlf

    ###########################
    # Simple Payback Period (implementation cost / annual cost savings)
    ###########################
    tlf_simple_payback = (implementation_cost_tlf / tlf_total_cost_savings) * ureg.year

    ##########################################################################################################

    """
    PP Analysis
    """

    ###########################
    # Electrical Energy Savings
    ###########################
    pp_electric_gen_list, pp_electric_sold_list = cogen.pp_calc_electricity_gen_sold(chp_size=chp_size_pp,
                                                                                     class_dict=class_dict)
    pp_electricity_bought_hourly = cogen.calc_electricity_bought(chp_gen_hourly_kwh=pp_electric_gen_list,
                                                                 chp_size=chp_size_pp, class_dict=class_dict)
    pp_electric_energy_savings = class_dict['demand'].annual_sum_el - sum(pp_electricity_bought_hourly)

    chp_gen_hourly_kwh_dict["PP"] = pp_electric_gen_list

    # Retrieve TES Size
    tes_size_pp = sizing.size_tes(chp_gen_hourly_kwh_dict=chp_gen_hourly_kwh_dict, chp_size=chp_size_pp,
                                  class_dict=class_dict, load_following_type="PP")

    ###########################
    # Thermal Demand Met by Equipment
    ###########################
    pp_chp_gen_btuh = cogen.pp_calc_hourly_heat_generated(chp_gen_hourly_kwh=chp_gen_hourly_kwh_dict["PP"],
                                                          class_dict=class_dict)
    chp_gen_hourly_btuh_dict["PP"] = pp_chp_gen_btuh

    # Convert from power to energy
    pp_chp_gen_btu = class_dict["demand"].convert_units(units_to_str="Btu", values_list=pp_chp_gen_btuh)
    pp_chp_thermal_gen = sum(pp_chp_gen_btu)

    pp_tes_heat_flow_list, pp_tes_soc = \
        storage.calc_tes_heat_flow_and_soc(chp_gen_hourly_kwh_dict=chp_gen_hourly_kwh_dict, tes_size=tes_size_pp,
                                           load_following_type="PP", class_dict=class_dict)
    # Convert from power to energy
    pp_tes_flow_btu = class_dict["demand"].convert_units(units_to_str="Btu", values_list=pp_tes_heat_flow_list)
    pp_tes_thermal_dispatch = -1 * sum(item for item in pp_tes_flow_btu if item < 0)
    assert pp_tes_thermal_dispatch.units == ureg.Btu

    pp_boiler_dispatch_hourly = boiler.calc_aux_boiler_output_rate(chp_gen_hourly_kwh_dict=chp_gen_hourly_kwh_dict,
                                                                   tes_size=tes_size_pp, chp_size=chp_size_pp,
                                                                   class_dict=class_dict, load_following_type="PP")
    # Convert from power to energy
    pp_boiler_btu = class_dict["demand"].convert_units(units_to_str="Btu", values_list=pp_boiler_dispatch_hourly)
    pp_boiler_dispatch = sum(pp_boiler_btu)

    ###########################
    # Thermal Energy Savings (current energy consumption - proposed energy consumption)
    ###########################
    pp_thermal_consumption_hourly_chp = \
        cogen.calc_hourly_fuel_use(chp_size=chp_size_pp, class_dict=class_dict, load_following_type="PP")
    pp_thermal_consumption_hourly_ab = \
        boiler.calc_hourly_fuel_use(ab_output_rate_list=pp_boiler_dispatch_hourly, class_dict=class_dict)
    pp_thermal_consumption_total = sum(pp_thermal_consumption_hourly_chp) + sum(pp_thermal_consumption_hourly_ab)
    pp_thermal_energy_savings = thermal_consumption_baseline - pp_thermal_consumption_total

    ###########################
    # Thermal Cost Savings (current energy costs - proposed energy costs)
    ###########################
    pp_fuel_use_list = []
    for index, item in enumerate(pp_thermal_consumption_hourly_chp):
        hourly_fuel = pp_thermal_consumption_hourly_chp[index] + pp_thermal_consumption_hourly_ab[index]
        pp_fuel_use_list.append(hourly_fuel)

    pp_thermal_cost_total = costs.calc_fuel_charges(class_dict=class_dict, fuel_bought_hourly=pp_fuel_use_list)
    pp_thermal_cost_savings = thermal_cost_baseline - pp_thermal_cost_total

    ###########################
    # Electrical Cost Savings
    ###########################
    pp_electric_cost_new = costs.calc_electric_charges(class_dict=class_dict,
                                                       electricity_bought_hourly=pp_electricity_bought_hourly)
    pp_revenue = costs.calc_pp_revenue(class_dict=class_dict, electricity_sold_hourly=pp_electric_sold_list)
    pp_electric_cost_savings = electric_cost_baseline - pp_electric_cost_new + pp_revenue

    ###########################
    # Total Cost Savings
    ###########################
    pp_total_cost_savings = pp_electric_cost_savings + pp_thermal_cost_savings

    ###########################
    # Implementation Cost (material cost + installation cost)
    ###########################
    installed_cost_chp_pp = costs.calc_installed_cost(class_dict=class_dict, size=chp_size_pp, class_str="chp",
                                                      dispatch_hourly=chp_gen_hourly_kwh_dict["PP"])
    installed_cost_tes_pp = costs.calc_installed_cost(class_dict=class_dict, size=tes_size_pp, class_str="tes",
                                                      dispatch_hourly=pp_tes_heat_flow_list)
    implementation_cost_pp = installed_cost_chp_pp + installed_cost_tes_pp

    ###########################
    # Simple Payback Period (implementation cost / annual cost savings)
    ###########################
    pp_simple_payback = (implementation_cost_pp / pp_total_cost_savings) * ureg.year

    ##########################################################################################################

    """
    PP Analysis - Peak Load CHP Size
    """

    ###########################
    # Electrical Energy Savings
    ###########################
    peak_electric_gen_list, peak_electric_sold_list = cogen.pp_calc_electricity_gen_sold(chp_size=chp_size_peak,
                                                                                         class_dict=class_dict)
    peak_electricity_bought_hourly = cogen.calc_electricity_bought(chp_gen_hourly_kwh=peak_electric_gen_list,
                                                                   chp_size=chp_size_peak, class_dict=class_dict)
    peak_electric_energy_savings = class_dict['demand'].annual_sum_el - sum(peak_electricity_bought_hourly)

    chp_gen_hourly_kwh_dict["Peak"] = peak_electric_gen_list

    # Retrieve TES Size
    tes_size_peak = sizing.size_tes(chp_gen_hourly_kwh_dict=chp_gen_hourly_kwh_dict, chp_size=chp_size_peak,
                                    class_dict=class_dict, load_following_type="Peak")

    ###########################
    # Thermal Demand Met by Equipment
    ###########################
    peak_chp_gen_btuh = cogen.pp_calc_hourly_heat_generated(chp_gen_hourly_kwh=chp_gen_hourly_kwh_dict["Peak"],
                                                            class_dict=class_dict)
    assert peak_chp_gen_btuh[0].units == ureg.Btu / ureg.hours
    chp_gen_hourly_btuh_dict["Peak"] = peak_chp_gen_btuh

    # Convert from power to energy
    peak_chp_gen_btu = class_dict["demand"].convert_units(units_to_str="Btu", values_list=peak_chp_gen_btuh)
    assert peak_chp_gen_btu[0].units == ureg.Btu
    peak_chp_thermal_gen = sum(peak_chp_gen_btu)
    assert peak_chp_thermal_gen.units == ureg.Btu

    peak_tes_heat_flow_list, peak_tes_soc = \
        storage.calc_tes_heat_flow_and_soc(chp_gen_hourly_kwh_dict=chp_gen_hourly_kwh_dict, tes_size=tes_size_peak,
                                           load_following_type="Peak", class_dict=class_dict)
    # Convert from power to energy
    peak_tes_flow_btu = class_dict["demand"].convert_units(units_to_str="Btu", values_list=peak_tes_heat_flow_list)
    mag = -1 * sum(item for item in peak_tes_flow_btu if item < 0)
    peak_tes_thermal_dispatch = Q_(float(mag), ureg.Btu)
    assert peak_tes_thermal_dispatch.units == ureg.Btu

    peak_boiler_dispatch_hourly = boiler.calc_aux_boiler_output_rate(chp_gen_hourly_kwh_dict=chp_gen_hourly_kwh_dict,
                                                                     tes_size=tes_size_peak, chp_size=chp_size_peak,
                                                                     class_dict=class_dict, load_following_type="Peak")
    # Convert from power to energy
    peak_boiler_btu = class_dict["demand"].convert_units(units_to_str="Btu", values_list=peak_boiler_dispatch_hourly)
    peak_boiler_dispatch = sum(peak_boiler_btu)

    ###########################
    # Thermal Energy Savings (current energy consumption - proposed energy consumption)
    ###########################
    peak_thermal_consumption_hourly_chp = \
        cogen.calc_hourly_fuel_use(chp_size=chp_size_peak, class_dict=class_dict, load_following_type="Peak")
    peak_thermal_consumption_hourly_ab = \
        boiler.calc_hourly_fuel_use(ab_output_rate_list=peak_boiler_dispatch_hourly, class_dict=class_dict)
    peak_thermal_consumption_total = sum(peak_thermal_consumption_hourly_chp) + sum(peak_thermal_consumption_hourly_ab)
    peak_thermal_energy_savings = thermal_consumption_baseline - peak_thermal_consumption_total

    ###########################
    # Thermal Cost Savings (current energy costs - proposed energy costs)
    ###########################
    peak_fuel_use_list = []
    for index, item in enumerate(peak_thermal_consumption_hourly_chp):
        hourly_fuel = peak_thermal_consumption_hourly_chp[index] + peak_thermal_consumption_hourly_ab[index]
        peak_fuel_use_list.append(hourly_fuel)

    peak_thermal_cost_total = costs.calc_fuel_charges(class_dict=class_dict, fuel_bought_hourly=peak_fuel_use_list)
    peak_thermal_cost_savings = thermal_cost_baseline - peak_thermal_cost_total

    ###########################
    # Electrical Cost Savings
    ###########################
    peak_electric_cost_new = costs.calc_electric_charges(class_dict=class_dict,
                                                         electricity_bought_hourly=peak_electricity_bought_hourly)
    peak_revenue = costs.calc_pp_revenue(class_dict=class_dict, electricity_sold_hourly=peak_electric_sold_list)
    peak_electric_cost_savings = electric_cost_baseline - peak_electric_cost_new + peak_revenue

    ###########################
    # Total Cost Savings
    ###########################
    peak_total_cost_savings = peak_electric_cost_savings + peak_thermal_cost_savings

    ###########################
    # Implementation Cost (material cost + installation cost)
    ###########################
    installed_cost_chp_peak = costs.calc_installed_cost(class_dict=class_dict, size=chp_size_peak, class_str="chp",
                                                        dispatch_hourly=chp_gen_hourly_kwh_dict["Peak"])
    installed_cost_tes_peak = costs.calc_installed_cost(class_dict=class_dict, size=tes_size_peak, class_str="tes",
                                                        dispatch_hourly=peak_tes_heat_flow_list)
    implementation_cost_peak = installed_cost_chp_peak + installed_cost_tes_peak

    ###########################
    # Simple Payback Period (implementation cost / annual cost savings)
    ###########################
    peak_simple_payback = (implementation_cost_peak / peak_total_cost_savings) * ureg.year

    ##########################################################################################################

    ###########################
    # Sensitivity Analysis
    ###########################

    def calc_payback(thermal_cost_new=None, electrical_cost_new=None, tes_size=None, incentives=Q_(10000, ''),
                     thermal_cost_baseline=thermal_cost_baseline, electrical_cost_baseline=electric_cost_baseline,
                     load_following_type="ELF", chp_size=chp_size_elf, class_dict=class_dict,
                     chp_gen_hourly_kwh=chp_gen_hourly_kwh_dict["ELF"], tes_heat_flow_list=elf_tes_heat_flow_list,
                     electricity_sold_hourly=None, sa=True):

        if sa is True:
            thermal_cost_new = Q_(thermal_cost_new, thermal_cost_baseline.units)
            electrical_cost_new = Q_(electrical_cost_new, electrical_cost_baseline.units)
            tes_size = Q_(tes_size, class_dict['tes'].tes_size_units)
            incentives = Q_(incentives, '')

        # Calculate Cost Savings
        thermal_cost_savings = thermal_cost_baseline - thermal_cost_new
        if load_following_type == "PP" or load_following_type == "Peak":
            revenue = costs.calc_pp_revenue(class_dict=class_dict, electricity_sold_hourly=electricity_sold_hourly)
            electrical_cost_savings = electrical_cost_baseline - electrical_cost_new + revenue
        else:
            electrical_cost_savings = electrical_cost_baseline - electrical_cost_new
        total_cost_savings = electrical_cost_savings + thermal_cost_savings

        # Implementation Cost (material cost + installation cost)
        installed_cost_chp = costs.calc_installed_cost(class_dict=class_dict, size=chp_size, class_str="chp",
                                                       dispatch_hourly=chp_gen_hourly_kwh)
        installed_cost_tes = costs.calc_installed_cost(class_dict=class_dict, size=tes_size, class_str="tes",
                                                       dispatch_hourly=tes_heat_flow_list)
        implementation_cost = installed_cost_chp + installed_cost_tes - incentives

        # Simple Payback Period (implementation cost / annual cost savings)
        simple_payback = implementation_cost / total_cost_savings
        if sa is True:
            return simple_payback.magnitude
        else:
            return simple_payback

    def wrapped_func(X, func=calc_payback):
        """g(X) = Y, where X := [a b x] and g(X) := f(X)"""
        # We transpose to obtain each column (the model factors) as separate variables
        thermal_cost_new, electrical_cost_new, tes_size, incentives = X.T

        # Then call the original model
        return func(thermal_cost_new=thermal_cost_new, electrical_cost_new=electrical_cost_new, tes_size=tes_size,
                    incentives=incentives)

    def sensitivity_analysis(thermal_cost_new=None, electrical_cost_new=None, tes_size=None, incentives=Q_(10000, '')):
        # TODO: Replace incentives with average value from given city

        sa_electric_cost_list_elf, unit_ec = sa.make_param_list(base=electrical_cost_new, dev=1000, allow_neg=False)
        sa_thermal_cost_list_elf, unit_tc = sa.make_param_list(base=thermal_cost_new, dev=1000, allow_neg=False)
        sa_incentives_list_elf, unit_i = sa.make_param_list(base=incentives, dev=100, allow_neg=False)
        sa_tes_size_list_elf, unit_tes = sa.make_param_list(base=tes_size, dev=50, allow_neg=False)

        problem = {
            'num_vars': 4,
            'names': ['thermal_cost_new', 'electrical_cost_new', 'tes_size', 'incentives'],
            'bounds': [sa_thermal_cost_list_elf,
                       sa_electric_cost_list_elf,
                       sa_tes_size_list_elf,
                       sa_incentives_list_elf]
        }

        param_values = saltelli.sample(problem, 100)    # TODO: Consider best sample size value (~1050)

        Y = np.zeros([param_values.shape[0]])

        for i, X in enumerate(param_values):
            Y[i] = wrapped_func(X)

        Si = sobol.analyze(problem, Y, print_to_console=False)
        return Si, problem

    test, prob = sensitivity_analysis(thermal_cost_new=elf_thermal_cost_total, electrical_cost_new=elf_electric_cost_new,
                                      tes_size=tes_size_elf)
    print(prob)
    print("-----")
    print(test['S1'])

    ##########################################################################################################

    """
    Tables and Plots
    """

    # ###########################
    # # Table: Display system property inputs
    # ###########################
    #
    # head_equipment = ["", "mCHP", "TES", "Aux Boiler"]
    #
    # system_properties = [
    #     ["Minimum Load Operation", "{} %".format(round(class_dict['chp'].min_pl * 100, 2)), "N/A", "N/A"],
    #     ["ELF Equipment Sizes", round(chp_size_elf.to(ureg.kW), 2), round(tes_size_elf.to(ureg.megaBtu), 3),
    #      round(class_dict['ab'].annual_peak_hl, 2)],
    #     ["TLF Equipment Sizes", round(chp_size_tlf.to(ureg.kW), 2), round(tes_size_tlf.to(ureg.megaBtu), 3),
    #      round(class_dict['ab'].annual_peak_hl, 2)],
    #     ["PP Equipment Sizes", round(chp_size_pp.to(ureg.kW), 2), round(tes_size_pp.to(ureg.megaBtu), 3),
    #      round(class_dict['ab'].annual_peak_hl, 2)],
    #     ["PP Peak Equipment Sizes", round(chp_size_peak.to(ureg.kW), 2), round(tes_size_peak.to(ureg.megaBtu), 3),
    #      round(class_dict['ab'].annual_peak_hl), 2]
    # ]
    #
    # table_system_properties = tabulate(system_properties, headers=head_equipment, tablefmt="fancy_grid")
    # print(table_system_properties)
    #
    # ###########################
    # # Table: Display key input data
    # ###########################
    #
    # head_units = ["", "Value"]
    #
    # input_data = [
    #     ["Location", "{}, {}".format(class_dict["demand"].city, class_dict["demand"].state)],
    #     ["Electric Meter Type", "{}".format(class_dict["costs"].meter_type_el)],
    #     ["Electric Rate Schedule Type", "{}".format(class_dict["costs"].schedule_type_el)],
    #     ["Fuel Meter Type", "{}".format(class_dict["costs"].meter_type_fuel)],
    #     ["Electric Rate Schedule Type", "{}".format(class_dict["costs"].schedule_type_fuel)]
    # ]
    #
    # table_input_data = tabulate(input_data, headers=head_units, tablefmt="fancy_grid")
    # print(table_input_data)
    #
    # ###########################
    # # Table: Display Energy Generation by Equipment Type
    # ###########################
    #
    # head_energy = ["", "ELF", "TLF", "PP", "PP Peak"]
    #
    # energy = [
    #     ["Annual Electrical Demand [kWh]", round(class_dict['demand'].annual_sum_el.to(ureg.megaWh), 2), "N/A", "N/A", "N/A"],
    #     ["Peak Electrical Demand [kW]", round(class_dict['demand'].annual_peak_el, 2), "N/A", "N/A", "N/A"],
    #     ["CHP Electrical Generation", round(elf_electric_energy_savings.to(ureg.kWh), 2),
    #      round(tlf_electric_energy_savings.to(ureg.kWh), 2), round(pp_electric_energy_savings.to(ureg.kWh), 2),
    #      round(peak_electric_energy_savings.to(ureg.kWh), 2)],
    #     ["Electrical Energy Bought", round(sum(elf_electricity_bought_hourly), 2), round(sum(tlf_electricity_bought_hourly), 2),
    #      round(sum(pp_electricity_bought_hourly), 2), round(sum(peak_electricity_bought_hourly), 2)],
    #     ["Electrical Energy Sold", 0, 0, round(sum(pp_electric_sold_list), 2), round(sum(peak_electric_sold_list), 2)],
    #     ["Annual Thermal Demand [MMBtu]", round(class_dict['demand'].annual_sum_hl.to(ureg.megaBtu), 3), "N/A", "N/A", "N/A"],
    #     ["Peak Thermal Demand [MMBtu/hr]", round(class_dict['demand'].annual_peak_hl.to(ureg.megaBtu / ureg.hours), 3), "N/A", "N/A", "N/A"],
    #     ["CHP Thermal Generation", round(elf_chp_thermal_gen.to(ureg.megaBtu), 2),
    #      round(tlf_chp_thermal_gen.to(ureg.megaBtu), 2), round(pp_chp_thermal_gen.to(ureg.megaBtu), 2),
    #      round(peak_chp_thermal_gen.to(ureg.megaBtu), 2)],
    #     ["TES Thermal Dispatched", round(elf_tes_thermal_dispatch.to(ureg.megaBtu), 2),
    #      round(tlf_tes_thermal_dispatch.to(ureg.megaBtu), 2), round(pp_tes_thermal_dispatch.to(ureg.megaBtu), 2),
    #      round(peak_tes_thermal_dispatch.to(ureg.megaBtu), 2)],
    #     ["Boiler Thermal Generation", round(elf_boiler_dispatch.to(ureg.megaBtu), 2),
    #      round(tlf_boiler_dispatch.to(ureg.megaBtu), 2), round(pp_boiler_dispatch.to(ureg.megaBtu), 2),
    #      round(peak_boiler_dispatch.to(ureg.megaBtu), 2)]
    # ]
    #
    # table_energy = tabulate(energy, headers=head_energy, tablefmt="fancy_grid")
    # print(table_energy)
    #
    # ###########################
    # # Table: Display economic calculations
    # ###########################
    #
    # head_costs = ["", "ELF", "TLF", "PP", "PP Peak"]
    #
    # costs_table = [
    #     ["Thermal Energy Savings [MMBtu]", round(elf_thermal_energy_savings.to(ureg.megaBtu), 2),
    #      round(tlf_thermal_energy_savings.to(ureg.megaBtu), 2), round(pp_thermal_energy_savings.to(ureg.megaBtu), 2),
    #      round(peak_thermal_energy_savings.to(ureg.megaBtu), 2)],
    #     ["Thermal Cost Savings [$]", round(elf_thermal_cost_savings, 2), round(tlf_thermal_cost_savings, 2),
    #      round(pp_thermal_cost_savings, 2), round(peak_thermal_cost_savings, 2)],
    #     ["Electrical Energy Savings [kWh]", round(elf_electric_energy_savings.to('kWh'), 2),
    #      round(tlf_electric_energy_savings.to('kWh'), 2), round(pp_electric_energy_savings.to('kWh'), 2),
    #      round(peak_electric_energy_savings.to('kWh'), 2)],
    #     ["Electrical Cost Savings [$]", round(elf_electric_cost_savings, 2), round(tlf_electric_cost_savings, 2),
    #      round(pp_electric_cost_savings, 2), round(peak_electric_cost_savings)],
    #     ["Total Cost Savings [$]", round(elf_total_cost_savings, 2), round(tlf_total_cost_savings, 2),
    #      round(pp_total_cost_savings, 2), round(peak_total_cost_savings, 2)],
    #     ["Simple Payback [Yrs]", round(elf_simple_payback, 2), round(tlf_simple_payback, 2), round(pp_simple_payback, 2),
    #      round(peak_simple_payback, 2)]
    # ]
    #
    # table_costs = tabulate(costs_table, headers=head_costs, tablefmt="fancy_grid")
    # print(table_costs)
    #
    # ###########################
    # # Table: Display Emissions Analysis
    # ###########################
    #
    # head_emissions_co2 = ["City, State", "Baseline Electrical Load", "Baseline Heating Load", "Baseline Emissions",
    #                       "CHP (ELF): Total Annual CO2 (tons)", "CHP (TLF): Total Annual CO2 (tons)",
    #                       "CHP (PP): Total Annual CO2 (tons)", "CHP (PP Peak): Total Annual CO2 (tons)"]
    #
    # baseline_total_co2 = emissions.calc_baseline_fuel_emissions(class_dict=class_dict) + \
    #     emissions.calc_baseline_grid_emissions(class_dict=class_dict)
    #
    # tlf_total_co2 = emissions.calc_chp_emissions(chp_gen_hourly_btuh=chp_gen_hourly_btuh_dict["TLF"],
    #                                              ab_output_rate_list=tlf_boiler_dispatch_hourly,
    #                                              chp_gen_hourly_kwh_dict=chp_gen_hourly_kwh_dict, chp_size=chp_size_tlf,
    #                                              tes_size=tes_size_tlf, load_following_type="TLF", class_dict=class_dict)
    # elf_total_co2 = emissions.calc_chp_emissions(chp_gen_hourly_btuh=chp_gen_hourly_btuh_dict["ELF"],
    #                                              ab_output_rate_list=elf_boiler_dispatch_hourly,
    #                                              chp_gen_hourly_kwh_dict=chp_gen_hourly_kwh_dict, chp_size=chp_size_elf,
    #                                              tes_size=tes_size_elf, load_following_type="ELF", class_dict=class_dict)
    # pp_total_co2 = emissions.calc_chp_emissions(chp_gen_hourly_btuh=chp_gen_hourly_btuh_dict["PP"],
    #                                             ab_output_rate_list=pp_boiler_dispatch_hourly,
    #                                             chp_gen_hourly_kwh_dict=chp_gen_hourly_kwh_dict, chp_size=chp_size_pp,
    #                                             tes_size=tes_size_pp, load_following_type="PP", class_dict=class_dict)
    # peak_total_co2 = emissions.calc_chp_emissions(chp_gen_hourly_btuh=chp_gen_hourly_btuh_dict["Peak"],
    #                                               ab_output_rate_list=peak_boiler_dispatch_hourly,
    #                                               chp_gen_hourly_kwh_dict=chp_gen_hourly_kwh_dict, chp_size=chp_size_peak,
    #                                               tes_size=tes_size_peak, load_following_type="Peak", class_dict=class_dict)
    #
    # emissions_data_co2 = [
    #     ["{}, {}".format(class_dict['demand'].city, class_dict['demand'].state), round(class_dict['demand'].annual_sum_el.to(ureg.megaWh)),
    #      round(class_dict['demand'].annual_sum_hl.to(ureg.megaBtu), 2), round(baseline_total_co2.to(ureg.tons)),
    #      round(elf_total_co2.to('tons')), round(tlf_total_co2.to('tons')), round(pp_total_co2.to('tons')),
    #      round(peak_total_co2.to('tons'))],
    #     ["In SI Units...", round(class_dict['demand'].annual_sum_el.to(ureg.megaWh)), round(class_dict['demand'].annual_sum_hl.to(ureg.megaWh)),
    #      round(baseline_total_co2.to(ureg.metric_ton)), round(elf_total_co2.to(ureg.metric_ton)),
    #      round(tlf_total_co2.to(ureg.metric_ton)), round(pp_total_co2.to(ureg.metric_ton)),
    #      round(peak_total_co2.to(ureg.metric_ton))]
    # ]
    #
    # table_emissions_co2 = tabulate(emissions_data_co2, headers=head_emissions_co2, tablefmt="fancy_grid")
    # print(table_emissions_co2)

    ###########################
    # Plots
    ###########################

    # plots.plot_max_rectangle_example(demand=class_dict['demand'], chp_size=chp_size_elf)
    #
    # plots.plot_electrical_demand_curve(demand=class_dict['demand'])
    # plots.plot_thermal_demand_curve(demand=class_dict['demand'])
    #
    # plots.elf_plot_electric(elf_electric_gen_list=elf_electric_gen_list,
    #                         elf_electricity_bought_list=elf_electricity_bought_hourly, demand=class_dict['demand'])
    # plots.elf_plot_thermal(elf_chp_gen_btuh=elf_chp_gen_btuh, elf_tes_heat_flow_list=elf_tes_heat_flow_list,
    #                        elf_boiler_dispatch_hourly=elf_boiler_dispatch_hourly, demand=class_dict['demand'])
    # plots.elf_plot_tes_soc(elf_tes_soc=elf_tes_soc)
    #
    # plots.tlf_plot_electric(tlf_electric_gen_list=tlf_electric_gen_list,
    #                         tlf_electricity_bought_list=tlf_electricity_bought_hourly, demand=class_dict['demand'])
    # plots.tlf_plot_thermal(tlf_chp_gen_btuh=tlf_chp_gen_btuh, tlf_tes_heat_flow_list=tlf_tes_heat_flow_list,
    #                        tlf_boiler_dispatch_hourly=tlf_boiler_dispatch_hourly, demand=class_dict['demand'])
    # plots.tlf_plot_tes_soc(tlf_tes_soc_list=tlf_tes_soc_list)
    #
    # plots.pp_plot_electric(pp_electric_gen_list=pp_electric_gen_list,
    #                        pp_electricity_bought_list=pp_electricity_bought_hourly,
    #                        pp_electricity_sold_list=pp_electric_sold_list, demand=class_dict['demand'])
    # plots.pp_plot_thermal(pp_chp_gen_btuh=pp_chp_gen_btuh, pp_tes_heat_flow_list=pp_tes_heat_flow_list,
    #                       pp_boiler_dispatch_hourly=pp_boiler_dispatch_hourly, demand=class_dict['demand'])
    # plots.pp_plot_tes_soc(pp_tes_soc=pp_tes_soc)
    #
    # plots.pp_plot_electric(pp_electric_gen_list=peak_electric_gen_list,
    #                        pp_electricity_bought_list=peak_electricity_bought_hourly,
    #                        pp_electricity_sold_list=peak_electric_sold_list, demand=class_dict['demand'])
    # plots.pp_plot_thermal(pp_chp_gen_btuh=peak_chp_gen_btuh, pp_tes_heat_flow_list=peak_tes_heat_flow_list,
    #                       pp_boiler_dispatch_hourly=peak_boiler_dispatch_hourly, demand=class_dict['demand'])
    # plots.pp_plot_tes_soc(pp_tes_soc=peak_tes_soc)


if __name__ == "__main__":
    main()
