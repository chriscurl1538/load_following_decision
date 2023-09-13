"""
Module Description:
    Command line interface - imports .yaml file and uses equipment operating parameters
    from the file to initialize the class variables.
TODO: Update all documentation
"""
import os.path

import pint
import pandas as pd
import openpyxl
from lfd_package.modules.__init__ import ureg, Q_
from lfd_package.modules import aux_boiler as boiler, classes, chp as cogen
from lfd_package.modules import sizing_calcs as sizing, plots, emissions
from lfd_package.modules import thermal_storage as storage, costs, sa
from SALib.sample import saltelli
from SALib.analyze import sobol
import numpy as np
import pathlib
import argparse
import yaml


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
    cwd = pathlib.Path(__file__).parent.resolve() / 'input_yaml'

    with open(cwd / yaml_filename) as f:
        data = yaml.load(f, Loader=Loader)
    f.close()

    # Class initialization using CLI arguments
    demand = classes.EnergyDemand(file_name=data['demand_filename'], city=data['city'], state=data['state'],
                                  grid_efficiency=data['grid_efficiency'], sim_ab_efficiency=data["energy_plus_eff"],
                                  winter_start_inclusive=data['winter_start_inclusive'],
                                  summer_start_inclusive=data['summer_start_inclusive'])
    emissions_class = classes.Emissions(file_name=data['demand_filename'], city=data['city'], state=data['state'],
                                        grid_efficiency=data['grid_efficiency'],
                                        sim_ab_efficiency=data["energy_plus_eff"],
                                        summer_start_inclusive=data['summer_start_inclusive'],
                                        winter_start_inclusive=data['winter_start_inclusive'])
    costs_class = classes.EnergyCosts(file_name=data['demand_filename'], city=data['city'], state=data['state'],
                                      grid_efficiency=data['grid_efficiency'], no_apts=data['no_apts'],
                                      winter_start_inclusive=data['winter_start_inclusive'],
                                      summer_start_inclusive=data['summer_start_inclusive'],
                                      sim_ab_efficiency=data["energy_plus_eff"], meter_type_el=data['meter_type_el'],
                                      meter_type_fuel=data['meter_type_fuel'],
                                      schedule_type_el=data['schedule_type_el'],
                                      schedule_type_fuel=data['schedule_type_fuel'],
                                      master_metered_el=data['master_metered_el'],
                                      single_metered_el=data['single_metered_el'],
                                      master_metered_fuel=data['master_metered_fuel'],
                                      single_metered_fuel=data['single_metered_fuel'])
    chp = classes.CHP(file_name=data['demand_filename'], city=data['city'], state=data['state'],
                      grid_efficiency=data['grid_efficiency'], sim_ab_efficiency=data["energy_plus_eff"],
                      summer_start_inclusive=data['summer_start_inclusive'],
                      winter_start_inclusive=data['winter_start_inclusive'], turn_down_ratio=data['chp_turn_down'],
                      chp_installed_cost=data['chp_installed_cost'], chp_om_cost=data['chp_om_cost'])
    ab = classes.AuxBoiler(file_name=data['demand_filename'], city=data['city'], state=data['state'],
                           grid_efficiency=data['grid_efficiency'],
                           summer_start_inclusive=data['summer_start_inclusive'],
                           winter_start_inclusive=data['winter_start_inclusive'],
                           sim_ab_efficiency=data["energy_plus_eff"], efficiency=data['ab_eff'])
    tes = classes.TES(file_name=data['demand_filename'], city=data['city'], state=data['state'],
                      grid_efficiency=data['grid_efficiency'], sim_ab_efficiency=data["energy_plus_eff"],
                      summer_start_inclusive=data['summer_start_inclusive'], start=data['tes_init'],
                      winter_start_inclusive=data['winter_start_inclusive'],
                      tes_installed_cost=data['tes_installed_cost'], tes_om_cost=data['tes_om_cost'])

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
    chp_size_peak = sizing.size_chp(load_following_type='Peak', class_dict=class_dict)

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
    # TODO: Commented for SA analysis only
    # baseline_electric_energy_use = class_dict['demand'].annual_sum_el / class_dict['demand'].grid_efficiency
    # elf_electric_energy_use = sum(elf_electricity_bought_hourly) / class_dict['demand'].grid_efficiency
    # elf_electric_energy_savings = (baseline_electric_energy_use - elf_electric_energy_use).to(ureg.kWh)

    chp_gen_hourly_kwh_dict["ELF"] = elf_electric_gen_list

    ###########################
    # Thermal Demand Met by Equipment
    ###########################
    elf_chp_gen_btuh = cogen.elf_calc_hourly_heat_generated(chp_gen_hourly_kwh=chp_gen_hourly_kwh_dict["ELF"],
                                                            class_dict=class_dict)
    chp_gen_hourly_btuh_dict["ELF"] = elf_chp_gen_btuh

    # Retrieve TES Size
    tes_size_elf = sizing.size_tes(chp_size=chp_size_elf, class_dict=class_dict)

    # Convert from power to energy
    # TODO: Commented for SA analysis only
    # elf_chp_gen_btu = class_dict['demand'].convert_units(units_to_str="Btu", values_list=elf_chp_gen_btuh)
    # elf_chp_thermal_gen = sum(elf_chp_gen_btu)

    # TODO: Add assessment for tes_size_zero
    elf_tes_heat_flow_list, elf_tes_soc = \
        storage.calc_tes_heat_flow_and_soc(chp_gen_hourly_btuh=elf_chp_gen_btuh, tes_size=tes_size_elf,
                                           load_following_type="ELF", class_dict=class_dict)

    # Convert from power to energy
    elf_tes_heat_flow_btu = \
        class_dict['demand'].convert_units(units_to_str="Btu", values_list=elf_tes_heat_flow_list)
    elf_tes_thermal_dispatch = -1 * sum([flow for flow in elf_tes_heat_flow_btu if flow.magnitude < 0])
    if isinstance(elf_tes_thermal_dispatch, pint.Quantity) is False:
        elf_tes_thermal_dispatch = Q_(elf_tes_thermal_dispatch, elf_tes_heat_flow_btu[0].units)
    assert elf_tes_thermal_dispatch.units == ureg.Btu

    # TODO: Add assessment for tes_size_zero
    elf_boiler_dispatch_hourly = boiler.calc_aux_boiler_output_rate(chp_gen_hourly_btuh_dict=chp_gen_hourly_btuh_dict,
                                                                    chp_size=chp_size_elf, tes_size=tes_size_elf,
                                                                    class_dict=class_dict, load_following_type="ELF",
                                                                    tes_heat_flow_btuh=elf_tes_heat_flow_list)
    # Convert from power to energy
    # TODO: Commented for SA analysis only
    # elf_boiler_btu = class_dict["demand"].convert_units(units_to_str="Btu", values_list=elf_boiler_dispatch_hourly)
    # elf_boiler_dispatch = sum(elf_boiler_btu)

    ###########################
    # Thermal Energy Savings (current energy consumption - proposed energy consumption)
    ###########################
    thermal_consumption_baseline = class_dict['demand'].annual_sum_hl / class_dict['ab'].eff

    elf_thermal_consumption_hourly_chp = cogen.calc_hourly_fuel_use(chp_size=chp_size_elf, load_following_type="ELF",
                                                                    class_dict=class_dict)
    elf_thermal_consumption_hourly_ab = boiler.calc_hourly_fuel_use(ab_output_rate_list=elf_boiler_dispatch_hourly,
                                                                    class_dict=class_dict)
    # TODO: Commented for SA analysis only
    # elf_thermal_consumption_total = sum(elf_thermal_consumption_hourly_chp) + sum(elf_thermal_consumption_hourly_ab)
    # elf_thermal_energy_savings = thermal_consumption_baseline - elf_thermal_consumption_total

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

    ###########################
    # Electrical Cost Savings
    ###########################
    electric_cost_baseline = costs.calc_electric_charges(class_dict=class_dict,
                                                         electricity_bought_hourly=class_dict['costs'].el)
    elf_electric_cost_new = costs.calc_electric_charges(class_dict=class_dict,
                                                        electricity_bought_hourly=elf_electricity_bought_hourly)

    ###########################
    # Simple Payback Period (implementation cost / annual cost savings)
    ###########################
    incentive_base_pct = 0.375
    # TODO: Commented for SA analysis only
    # TODO: Add assessment for tes_size_zero
    # elf_cost_data_dict = costs.calc_costs(thermal_cost_new=elf_thermal_cost_total, tes_size=tes_size_elf,
    #                                       electrical_cost_new=elf_electric_cost_new, pct_incentive=incentive_base_pct,
    #                                       thermal_cost_baseline=thermal_cost_baseline, class_dict=class_dict,
    #                                       electrical_cost_baseline=electric_cost_baseline, load_following_type="ELF",
    #                                       chp_gen_hourly_kwh=chp_gen_hourly_kwh_dict["ELF"], chp_size=chp_size_elf,
    #                                       tes_heat_flow_list=elf_tes_heat_flow_list)

    ##########################################################################################################

    """
    TLF Analysis
    """

    ###########################
    # Thermal Demand Met by Equipment
    ###########################
    # Retrieve TES Size
    tes_size_tlf = sizing.size_tes(chp_size=chp_size_tlf, class_dict=class_dict)

    # TODO: Add assessment for tes_size_zero
    tlf_chp_gen_btuh, tlf_tes_heat_flow_list, tlf_tes_soc_list = \
        cogen.tlf_calc_hourly_heat_chp_tes_soc(chp_size=chp_size_tlf, tes_size=tes_size_tlf, class_dict=class_dict)
    chp_gen_hourly_btuh_dict["TLF"] = tlf_chp_gen_btuh

    # Convert from power to energy
    # TODO: Commented for SA analysis only
    # tlf_chp_gen_btu = class_dict["demand"].convert_units(units_to_str="Btu", values_list=tlf_chp_gen_btuh)
    # tlf_chp_thermal_gen = sum(tlf_chp_gen_btu)

    # Convert from power to energy
    tlf_tes_flow_btu = class_dict["demand"].convert_units(units_to_str="Btu", values_list=tlf_tes_heat_flow_list)
    tlf_tes_thermal_dispatch = -1 * sum([item for item in tlf_tes_flow_btu if item.magnitude < 0])
    if isinstance(tlf_tes_thermal_dispatch, pint.Quantity) is False:
        tlf_tes_thermal_dispatch = Q_(tlf_tes_thermal_dispatch, tlf_tes_flow_btu[0].units)
    assert tlf_tes_thermal_dispatch.units == ureg.Btu

    ###########################
    # Electrical Energy Savings
    ###########################
    tlf_electric_gen_list = \
        cogen.tlf_calc_electricity_generated(chp_gen_hourly_btuh=chp_gen_hourly_btuh_dict["TLF"], class_dict=class_dict)
    tlf_electricity_bought_hourly = cogen.calc_electricity_bought(chp_gen_hourly_kwh=tlf_electric_gen_list,
                                                                  chp_size=chp_size_tlf, class_dict=class_dict)
    # TODO: Commented for SA analysis only
    # tlf_electric_energy_use = sum(tlf_electricity_bought_hourly) / class_dict['demand'].grid_efficiency
    # tlf_electric_energy_savings = (baseline_electric_energy_use - tlf_electric_energy_use).to(ureg.kWh)

    chp_gen_hourly_kwh_dict["TLF"] = tlf_electric_gen_list

    # Get Boiler Thermal Output
    # TODO: Add assessment for tes_size_zero
    tlf_boiler_dispatch_hourly = boiler.calc_aux_boiler_output_rate(tes_size=tes_size_tlf, chp_size=chp_size_tlf,
                                                                    class_dict=class_dict, load_following_type="TLF",
                                                                    chp_gen_hourly_btuh_dict=chp_gen_hourly_btuh_dict,
                                                                    tes_heat_flow_btuh=tlf_tes_heat_flow_list)
    # Convert from power to energy
    # TODO: Commented for SA analysis only
    # tlf_boiler_btu = class_dict["demand"].convert_units(units_to_str="Btu", values_list=tlf_boiler_dispatch_hourly)
    # tlf_boiler_dispatch = sum(tlf_boiler_btu)

    ###########################
    # Thermal Energy Savings (current energy consumption - proposed energy consumption)
    ###########################
    tlf_thermal_consumption_hourly_chp = cogen.calc_hourly_fuel_use(chp_gen_hourly_btuh=chp_gen_hourly_btuh_dict["TLF"],
                                                                    chp_size=chp_size_tlf, class_dict=class_dict,
                                                                    load_following_type="TLF")
    tlf_thermal_consumption_hourly_ab = \
        boiler.calc_hourly_fuel_use(ab_output_rate_list=tlf_boiler_dispatch_hourly, class_dict=class_dict)
    # TODO: Commented for SA analysis only
    # tlf_thermal_consumption_total = sum(tlf_thermal_consumption_hourly_chp) + sum(tlf_thermal_consumption_hourly_ab)
    # tlf_thermal_energy_savings = thermal_consumption_baseline - tlf_thermal_consumption_total

    ###########################
    # Thermal Cost Savings (current energy costs - proposed energy costs)
    ###########################

    tlf_fuel_use_list = []
    for index, item in enumerate(thermal_consumption_baseline_hourly):
        hourly_fuel = tlf_thermal_consumption_hourly_chp[index] + tlf_thermal_consumption_hourly_ab[index]
        tlf_fuel_use_list.append(hourly_fuel)

    tlf_thermal_cost_total = costs.calc_fuel_charges(class_dict=class_dict,
                                                     fuel_bought_hourly=tlf_fuel_use_list)

    ###########################
    # Electrical Cost Savings
    ###########################
    tlf_electric_cost_new = costs.calc_electric_charges(class_dict=class_dict,
                                                        electricity_bought_hourly=tlf_electricity_bought_hourly)
    tlf_electricity_sold = cogen.tlf_calc_electricity_sold(class_dict=class_dict,
                                                           chp_gen_hourly_kwh=tlf_electric_gen_list)
    tlf_revenue = costs.calc_pp_revenue(class_dict=class_dict, electricity_sold_hourly=tlf_electricity_sold)

    ###########################
    # Simple Payback Period (implementation cost / annual cost savings)
    ###########################
    # TODO: Commented for SA analysis only
    # TODO: Add assessment for tes_size_zero
    # tlf_cost_data_dict = costs.calc_costs(thermal_cost_new=tlf_thermal_cost_total, tes_size=tes_size_tlf,
    #                                       electrical_cost_new=tlf_electric_cost_new, pct_incentive=incentive_base_pct,
    #                                       thermal_cost_baseline=thermal_cost_baseline, class_dict=class_dict,
    #                                       electrical_cost_baseline=electric_cost_baseline, load_following_type="TLF",
    #                                       chp_gen_hourly_kwh=chp_gen_hourly_kwh_dict["TLF"],
    #                                       tes_heat_flow_list=tlf_tes_heat_flow_list, chp_size=chp_size_tlf,
    #                                       electricity_sold_hourly=tlf_electricity_sold)

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
    # TODO: Commented for SA analysis only
    # peak_electric_energy_use = sum(peak_electricity_bought_hourly) / class_dict['demand'].grid_efficiency
    # peak_electric_energy_savings = baseline_electric_energy_use - peak_electric_energy_use

    chp_gen_hourly_kwh_dict["Peak"] = peak_electric_gen_list

    ###########################
    # Thermal Demand Met by Equipment
    ###########################
    peak_chp_gen_btuh = cogen.pp_calc_hourly_heat_generated(chp_gen_hourly_kwh=chp_gen_hourly_kwh_dict["Peak"],
                                                            class_dict=class_dict)
    assert peak_chp_gen_btuh[0].units == ureg.Btu / ureg.hours
    chp_gen_hourly_btuh_dict["Peak"] = peak_chp_gen_btuh

    # Retrieve TES Size
    tes_size_peak = sizing.size_tes(chp_size=chp_size_peak, class_dict=class_dict)

    # Convert from power to energy
    peak_chp_gen_btu = class_dict["demand"].convert_units(units_to_str="Btu", values_list=peak_chp_gen_btuh)
    assert peak_chp_gen_btu[0].units == ureg.Btu
    peak_chp_thermal_gen = sum(peak_chp_gen_btu)
    assert peak_chp_thermal_gen.units == ureg.Btu

    # TODO: Add assessment for tes_size_zero
    peak_tes_heat_flow_list, peak_tes_soc = \
        storage.calc_tes_heat_flow_and_soc(chp_gen_hourly_btuh=peak_chp_gen_btuh, tes_size=tes_size_peak,
                                           load_following_type="Peak", class_dict=class_dict)
    # Convert from power to energy
    peak_tes_flow_btu = class_dict["demand"].convert_units(units_to_str="Btu", values_list=peak_tes_heat_flow_list)
    peak_tes_thermal_dispatch = -1 * sum([item for item in peak_tes_flow_btu if item.magnitude < 0])
    if isinstance(peak_tes_thermal_dispatch, pint.Quantity) is False:
        peak_tes_thermal_dispatch = Q_(peak_tes_thermal_dispatch, peak_tes_flow_btu[0].units)
    assert peak_tes_thermal_dispatch.units == ureg.Btu

    # TODO: Add assessment for tes_size_zero
    peak_boiler_dispatch_hourly = boiler.calc_aux_boiler_output_rate(chp_gen_hourly_btuh_dict=chp_gen_hourly_btuh_dict,
                                                                     tes_size=tes_size_peak, chp_size=chp_size_peak,
                                                                     class_dict=class_dict, load_following_type="Peak",
                                                                     tes_heat_flow_btuh=peak_tes_heat_flow_list)
    # Convert from power to energy
    # TODO: Commented for SA analysis only
    # peak_boiler_btu = class_dict["demand"].convert_units(units_to_str="Btu", values_list=peak_boiler_dispatch_hourly)
    # peak_boiler_dispatch = sum(peak_boiler_btu)

    ###########################
    # Thermal Energy Savings (current energy consumption - proposed energy consumption)
    ###########################
    peak_thermal_consumption_hourly_chp = \
        cogen.calc_hourly_fuel_use(chp_size=chp_size_peak, class_dict=class_dict, load_following_type="Peak")
    peak_thermal_consumption_hourly_ab = \
        boiler.calc_hourly_fuel_use(ab_output_rate_list=peak_boiler_dispatch_hourly, class_dict=class_dict)
    # TODO: Commented for SA analysis only
    # peak_thermal_consumption_total = sum(peak_thermal_consumption_hourly_chp) + sum(peak_thermal_consumption_hourly_ab)
    # peak_thermal_energy_savings = thermal_consumption_baseline - peak_thermal_consumption_total

    ###########################
    # Thermal Cost Savings (current energy costs - proposed energy costs)
    ###########################
    peak_fuel_use_list = []
    for index, item in enumerate(peak_thermal_consumption_hourly_chp):
        hourly_fuel = peak_thermal_consumption_hourly_chp[index] + peak_thermal_consumption_hourly_ab[index]
        peak_fuel_use_list.append(hourly_fuel)

    peak_thermal_cost_total = costs.calc_fuel_charges(class_dict=class_dict, fuel_bought_hourly=peak_fuel_use_list)

    ###########################
    # Electrical Cost Savings
    ###########################
    peak_electric_cost_new = costs.calc_electric_charges(class_dict=class_dict,
                                                         electricity_bought_hourly=peak_electricity_bought_hourly)

    ###########################
    # Simple Payback Period (implementation cost / annual cost savings)
    ###########################
    # TODO: Commented for SA analysis only
    # TODO: Add assessment for tes_size_zero
    # peak_cost_data_dict = costs.calc_costs(thermal_cost_new=peak_thermal_cost_total, tes_size=tes_size_peak,
    #                                        electrical_cost_new=peak_electric_cost_new, chp_size=chp_size_peak,
    #                                        pct_incentive=incentive_base_pct, class_dict=class_dict,
    #                                        thermal_cost_baseline=thermal_cost_baseline, load_following_type="Peak",
    #                                        electrical_cost_baseline=electric_cost_baseline,
    #                                        chp_gen_hourly_kwh=chp_gen_hourly_kwh_dict["Peak"],
    #                                        tes_heat_flow_list=peak_tes_heat_flow_list,
    #                                        electricity_sold_hourly=peak_electric_sold_list)

    ##########################################################################################################

    ###########################
    # Sensitivity Analysis
    ###########################

    # TODO: SA assumed ELF operation mode - need to change values before running SA
    def sa_payback_model(thermal_cost_new=None, electrical_cost_new=None, tes_size=None, pct_incentive=None,
                         thermal_cost_baseline=thermal_cost_baseline, electrical_cost_baseline=electric_cost_baseline,
                         load_following_type="ELF", chp_size=chp_size_elf, class_dict=class_dict,
                         chp_gen_hourly_kwh=chp_gen_hourly_kwh_dict["ELF"], tes_heat_flow_list=elf_tes_heat_flow_list,
                         electricity_sold_hourly=None):
        """
        Calculates the payback period of CHP and TES installation. Used only for sensitivity analysis.

        Parameters
        ----------
        thermal_cost_new: Quantity
            Dimensionless quantity representing annual sum of natural gas cost for CHP + TES
        electrical_cost_new: Quantity
            Dimensionless quantity representing annual sum of electricity costs for CHP + TES
        tes_size: Quantity
            The size of the TES unit in units of Btu.
        pct_incentive: float
            The percent of the total installed cost of CHP + TES covered by incentives.
        thermal_cost_baseline: Quantity
            Dimensionless quantity representing the natural gas costs associated with the Baseline case (non-CHP).
        electrical_cost_baseline: Quantity
            Dimensionless quantity representing the electricity costs associated with the Baseline case (non-CHP).
        load_following_type: str
            String representing the operating mode of the CHP unit (ELF, TLF, PP, Peak).
        chp_size: Quantity
            The size of the CHP unit in units of kW.
        class_dict: dict
            contains initialized class data using CLI inputs (see command_line.py)
        chp_gen_hourly_kwh: list
            contains electricity generated hourly by CHP in units of kWh.
        tes_heat_flow_list: list
            Storage heat rate for each hour. Values are positive for heat added and
            negative for heat discharged.Units are Btu/hr
        electricity_sold_hourly: list
            contains excess electricity generated hourly by CHP and sold to grid.
            Units are in kWh.

        Returns
        -------
        simple_payback: Quantity
            The payback period of the CHP + TES installation in units of years.
        """
        thermal_cost_new = Q_(thermal_cost_new, thermal_cost_baseline.units)
        electrical_cost_new = Q_(electrical_cost_new, electrical_cost_baseline.units)
        tes_size = Q_(tes_size, class_dict['tes'].tes_size_units)

        # Calculate Cost Savings
        if load_following_type == "TLF" or load_following_type == "Peak":
            revenue = costs.calc_pp_revenue(class_dict=class_dict, electricity_sold_hourly=electricity_sold_hourly)
        else:
            revenue = Q_(0, '')

        thermal_cost_savings = thermal_cost_baseline - thermal_cost_new
        electrical_cost_savings = electrical_cost_baseline - electrical_cost_new
        total_cost_savings = electrical_cost_savings + thermal_cost_savings

        # Implementation Cost (material cost + installation cost)
        installed_cost_chp, om_cost_chp = costs.calc_installed_om_cost(class_dict=class_dict, size=chp_size,
                                                                       class_str="chp",
                                                                       dispatch_hourly=chp_gen_hourly_kwh)
        installed_cost_tes, om_cost_tes = costs.calc_installed_om_cost(class_dict=class_dict, size=tes_size,
                                                                       class_str="tes",
                                                                       dispatch_hourly=tes_heat_flow_list)
        incremental_cost = om_cost_chp + om_cost_tes
        total_installed_cost = installed_cost_chp + installed_cost_tes
        implementation_cost = installed_cost_chp + installed_cost_tes - (pct_incentive * total_installed_cost)/100

        # Simple Payback Period (implementation cost / annual cost savings)
        simple_payback = implementation_cost / (revenue + total_cost_savings - incremental_cost)
        print(simple_payback.magnitude)
        return simple_payback.magnitude

    def wrapped_func(X, func=sa_payback_model):
        """

        Parameters
        ----------
        X
        func

        Returns
        -------

        """
        # We transpose to obtain each column (the model factors) as separate variables
        thermal_cost_new, electrical_cost_new, tes_size, pct_incentive = X.T

        # Then call the original model
        return func(thermal_cost_new=thermal_cost_new, electrical_cost_new=electrical_cost_new, tes_size=tes_size,
                    pct_incentive=incentive_base_pct)

    def sensitivity_analysis(thermal_cost_new=None, electrical_cost_new=None, tes_size=None, max_pct_incentive=None):
        """

        Parameters
        ----------
        thermal_cost_new
        electrical_cost_new
        tes_size
        max_pct_incentive

        Returns
        -------

        """
        # Set SA analysis range for TES. Check for size of zero
        if tes_size == 0:
            sa_tes_size_list = [0, 500]
        else:
            tes_size_dev = 0.25 * tes_size
            sa_tes_size_list, unit_tes = sa.make_param_list(base=tes_size, dev=tes_size_dev, has_units=False)

        # Set SA analysis range for thermal costs. Check for value of zero
        if thermal_cost_new == 0:
            sa_thermal_cost_list = [0, 500]
        else:
            th_cost_dev = 0.25 * thermal_cost_new
            sa_thermal_cost_list, unit_tc = sa.make_param_list(base=thermal_cost_new, dev=th_cost_dev, has_units=False)

        # Set SA analysis range for electrical costs. Check for value of zero
        if electrical_cost_new == 0:
            sa_electric_cost_list = [0, 500]
        else:
            el_cost_dev = 0.25 * electrical_cost_new
            sa_electric_cost_list, unit_ec = sa.make_param_list(base=electrical_cost_new, dev=el_cost_dev,
                                                                has_units=False)

        # Set SA analysis range for financial incentives as percent of installed costs
        sa_pct_incentives_list = [0, max_pct_incentive]

        # Define problem to analyze
        problem = {
            'num_vars': 4,
            'names': ['thermal_cost_new', 'electrical_cost_new', 'tes_size', 'pct_incentive'],
            'bounds': [sa_thermal_cost_list,
                       sa_electric_cost_list,
                       sa_tes_size_list,
                       sa_pct_incentives_list]
        }

        param_values = saltelli.sample(problem, 1024)

        Y = np.zeros([param_values.shape[0]])

        for i, X in enumerate(param_values):
            Y[i] = wrapped_func(X)

        Si = sobol.analyze(problem, Y, print_to_console=False)
        return Si, problem

    # Strip units from SA factors before running analysis
    elf_thermal_cost_sa = elf_thermal_cost_total.to('').magnitude
    elf_electric_cost_sa = elf_electric_cost_new.to('').magnitude
    elf_tes_size_sa = tes_size_elf.to(ureg.Btu).magnitude

    # Run SA - TODO: Assumes ELF mode as currently defined
    test, prob = sensitivity_analysis(thermal_cost_new=elf_thermal_cost_sa,
                                      electrical_cost_new=elf_electric_cost_sa,
                                      tes_size=elf_tes_size_sa, max_pct_incentive=50)
    print(prob)
    print("-----")
    print("First Order Results: {}".format(test['S1']))
    print("-----")
    print("Second Order Results: {}".format(test['S2']))
    print("-----")
    print("Total Order Results: {}".format(test['ST']))

    ##########################################################################################################

    """
    Tables and Plots
    """

    # # Baseline Demand Calcs
    # annual_el_sum = class_dict['demand'].annual_sum_el.to(ureg.kWh)
    # annual_el_peak = class_dict['demand'].annual_peak_el.to(ureg.kW)
    # annual_hl_sum = class_dict['demand'].annual_sum_hl.to(ureg.kWh)
    # annual_hl_peak = class_dict['demand'].annual_peak_hl.to(ureg.kW)
    #
    # # Sizing Calcs
    # # TODO: Add assessment for tes_size_zero
    # tes_size_elf.ito(ureg.kWh)
    # tes_size_tlf.ito(ureg.kWh)
    # tes_size_peak.ito(ureg.kWh)
    # peak_hl_annual = class_dict['ab'].annual_peak_hl.to(ureg.kW)
    #
    # # Energy Generation Calcs
    # chp_el_cov_elf = round((sum(elf_electric_gen_list) / class_dict['demand'].annual_sum_el) * 100, 2)
    # chp_el_cov_tlf = round((sum(tlf_electric_gen_list) / class_dict['demand'].annual_sum_el) * 100, 2)
    # chp_el_cov_peak = round((sum(peak_electric_gen_list) / class_dict['demand'].annual_sum_el) * 100, 2)
    #
    # bought_el_cov_elf = round((sum(elf_electricity_bought_hourly) / class_dict['demand'].annual_sum_el) * 100, 2)
    # bought_el_cov_tlf = round((sum(tlf_electricity_bought_hourly) / class_dict['demand'].annual_sum_el) * 100, 2)
    # bought_el_cov_peak = round((sum(peak_electricity_bought_hourly) / class_dict['demand'].annual_sum_el) * 100, 2)
    #
    # chp_th_cov_elf = round((elf_chp_thermal_gen / class_dict['demand'].annual_sum_hl) * 100, 2)
    # chp_th_cov_tlf = round((tlf_chp_thermal_gen / class_dict['demand'].annual_sum_hl) * 100, 2)
    # chp_th_cov_peak = round((peak_chp_thermal_gen / class_dict['demand'].annual_sum_hl) * 100, 2)
    #
    # tes_th_cov_elf = round((elf_tes_thermal_dispatch / class_dict['demand'].annual_sum_hl) * 100, 2)
    # tes_th_cov_tlf = round((tlf_tes_thermal_dispatch / class_dict['demand'].annual_sum_hl) * 100, 2)
    # tes_th_cov_peak = round((peak_tes_thermal_dispatch / class_dict['demand'].annual_sum_hl) * 100, 2)
    #
    # ab_th_cov_elf = round((elf_boiler_dispatch / class_dict['demand'].annual_sum_hl) * 100, 2)
    # ab_th_cov_tlf = round((tlf_boiler_dispatch / class_dict['demand'].annual_sum_hl) * 100, 2)
    # ab_th_cov_peak = round((peak_boiler_dispatch / class_dict['demand'].annual_sum_hl) * 100, 2)
    #
    # elf_annual_electricity_bought = sum(elf_electricity_bought_hourly)
    # tlf_annual_electricity_bought = sum(tlf_electricity_bought_hourly)
    # peak_annual_electricity_bought = sum(peak_electricity_bought_hourly)
    # tlf_annual_electricity_sold = sum(tlf_electricity_sold)
    # peak_annual_electricity_sold = sum(peak_electric_sold_list)
    # elf_chp_thermal_gen.ito(ureg.kWh)
    # tlf_chp_thermal_gen.ito(ureg.kWh)
    # peak_chp_thermal_gen.ito(ureg.kWh)
    # elf_tes_thermal_dispatch.ito(ureg.kWh)
    # tlf_tes_thermal_dispatch.ito(ureg.kWh)
    # peak_tes_thermal_dispatch.ito(ureg.kWh)
    # elf_boiler_dispatch.ito(ureg.kWh)
    # tlf_boiler_dispatch.ito(ureg.kWh)
    # peak_boiler_dispatch.ito(ureg.kWh)
    #
    # # Energy Savings Calcs
    # elf_thermal_energy_savings.ito(ureg.kWh)
    # tlf_thermal_energy_savings.ito(ureg.kWh)
    # peak_thermal_energy_savings.ito(ureg.kWh)
    # elf_electric_energy_savings.ito('kWh')
    # tlf_electric_energy_savings.ito('kWh')
    # peak_electric_energy_savings.ito('kWh')
    # elf_total_energy_savings = round((elf_thermal_energy_savings + elf_electric_energy_savings).to(ureg.kWh), 2)
    # tlf_total_energy_savings = round((tlf_thermal_energy_savings + tlf_electric_energy_savings).to(ureg.kWh), 2)
    # peak_total_energy_savings = round((peak_thermal_energy_savings + peak_electric_energy_savings).to(ureg.kWh), 2)
    #
    # # Emissions Analysis
    # baseline_total_co2 = emissions.calc_baseline_fuel_emissions(class_dict=class_dict) + \
    #                      emissions.calc_baseline_grid_emissions(class_dict=class_dict)
    #
    # tlf_total_co2 = emissions.calc_chp_emissions(electricity_bought_annual=sum(tlf_electricity_bought_hourly),
    #                                              chp_fuel_use_annual=sum(tlf_thermal_consumption_hourly_chp),
    #                                              ab_fuel_use_annual=sum(tlf_thermal_consumption_hourly_ab),
    #                                              class_dict=class_dict)
    # elf_total_co2 = emissions.calc_chp_emissions(electricity_bought_annual=sum(elf_electricity_bought_hourly),
    #                                              chp_fuel_use_annual=sum(elf_thermal_consumption_hourly_chp),
    #                                              ab_fuel_use_annual=sum(elf_thermal_consumption_hourly_ab),
    #                                              class_dict=class_dict)
    # peak_total_co2 = emissions.calc_chp_emissions(electricity_bought_annual=sum(peak_electricity_bought_hourly),
    #                                               chp_fuel_use_annual=sum(peak_thermal_consumption_hourly_chp),
    #                                               ab_fuel_use_annual=sum(peak_thermal_consumption_hourly_ab),
    #                                               class_dict=class_dict)
    #
    # baseline_total_co2.ito(ureg.metric_ton)
    # elf_total_co2.ito(ureg.metric_ton)
    # tlf_total_co2.ito(ureg.metric_ton)
    # peak_total_co2.ito(ureg.metric_ton)
    #
    # data_header = ["Variable Name", "Baseline", "", "ELF", "", "TLF", "", "PP Peak", ""]
    #
    # # TODO: Add assessment for tes_size_zero
    # results_data = [
    #     ###########################
    #     # Baseline Demand
    #     ###########################
    #     ["Annual Electrical Demand", round(annual_el_sum.magnitude, 2), annual_el_sum.units,
    #      'N/A', 'N/A', 'N/A', 'N/A', 'N/A', 'N/A'],
    #     ["Peak Electrical Demand", round(annual_el_peak.magnitude, 2), annual_el_peak.units,
    #      'N/A', 'N/A', 'N/A', 'N/A', 'N/A', 'N/A'],
    #     ["Annual Thermal Demand", round(annual_hl_sum.magnitude, 3), annual_hl_sum.units,
    #      'N/A', 'N/A', 'N/A', 'N/A', 'N/A', 'N/A'],
    #     ["Peak Thermal Demand", round(annual_hl_peak.magnitude, 3), annual_hl_peak.units,
    #      'N/A', 'N/A', 'N/A', 'N/A', 'N/A', 'N/A'],
    #     ###########################
    #     # Sizing
    #     ###########################
    #     ["CHP Size", "N/A", "N/A",
    #      round(chp_size_elf.magnitude, 2), chp_size_elf.units,
    #      round(chp_size_tlf.magnitude, 3), chp_size_tlf.units,
    #      round(chp_size_peak.magnitude, 2), chp_size_peak.units
    #      ],
    #     ["TES Size", "N/A", "N/A",
    #      round(tes_size_elf.magnitude, 2), tes_size_elf.units,
    #      round(tes_size_tlf.magnitude, 3), tes_size_tlf.units,
    #      round(tes_size_peak.magnitude, 2), tes_size_peak.units,
    #      ],
    #     ["Aux Boiler Size", "N/A", "N/A",
    #      round(peak_hl_annual.magnitude, 2), peak_hl_annual.units,
    #      round(peak_hl_annual.magnitude, 2), peak_hl_annual.units,
    #      round(peak_hl_annual.magnitude, 2), peak_hl_annual.units,
    #      ],
    #     ###########################
    #     # Energy Generation Data
    #     ###########################
    #     ["CHP Electrical Energy Generation", "N/A", "N/A",
    #      round(sum(elf_electric_gen_list).magnitude, 2), elf_electric_gen_list[0].units,
    #      round(sum(tlf_electric_gen_list).magnitude, 2), tlf_electric_gen_list[0].units,
    #      round(sum(peak_electric_gen_list).magnitude, 2), peak_electric_gen_list[0].units],
    #     ["Electrical Energy Bought", "N/A", "N/A",
    #      round(elf_annual_electricity_bought.magnitude, 2), elf_annual_electricity_bought.units,
    #      round(tlf_annual_electricity_bought.magnitude, 2), tlf_annual_electricity_bought.units,
    #      round(peak_annual_electricity_bought.magnitude, 2), peak_annual_electricity_bought.units],
    #     ["Electrical Energy Sold", "N/A", "N/A", 0, '',
    #      round(tlf_annual_electricity_sold.magnitude, 2), tlf_annual_electricity_sold.units,
    #      round(peak_annual_electricity_sold.magnitude, 2), peak_annual_electricity_sold.units],
    #     ["CHP Thermal Energy Generation", "N/A", "N/A",
    #      round(elf_chp_thermal_gen.magnitude, 2), elf_chp_thermal_gen.units,
    #      round(tlf_chp_thermal_gen.magnitude, 2), tlf_chp_thermal_gen.units,
    #      round(peak_chp_thermal_gen.magnitude, 2), peak_chp_thermal_gen.units],
    #     ["TES Thermal Energy Dispatched", "N/A", "N/A",
    #      round(elf_tes_thermal_dispatch.magnitude, 2), elf_tes_thermal_dispatch.units,
    #      round(tlf_tes_thermal_dispatch.magnitude, 2), tlf_tes_thermal_dispatch.units,
    #      round(peak_tes_thermal_dispatch.magnitude, 2), peak_tes_thermal_dispatch.units],
    #     ["Boiler Thermal Energy Generation", "N/A", "N/A",
    #      round(elf_boiler_dispatch.magnitude, 2), elf_boiler_dispatch.units,
    #      round(tlf_boiler_dispatch.magnitude, 2), tlf_boiler_dispatch.units,
    #      round(peak_boiler_dispatch.magnitude, 2), peak_boiler_dispatch.units],
    #     ###########################
    #     # Percent Demand Coverage
    #     ###########################
    #     ["CHP Electrical Pct Coverage", "N/A", "N/A",
    #      chp_el_cov_elf.magnitude, "%",
    #      chp_el_cov_tlf.magnitude, "%",
    #      chp_el_cov_peak.magnitude, "%"],
    #     ["Electricity Bought Pct Coverage", "N/A", "N/A",
    #      bought_el_cov_elf.magnitude, "%",
    #      bought_el_cov_tlf.magnitude, "%",
    #      bought_el_cov_peak.magnitude, "%"],
    #     ["CHP Thermal Pct Coverage", "N/A", "N/A",
    #      chp_th_cov_elf.magnitude, "%",
    #      chp_th_cov_tlf.magnitude, "%",
    #      chp_th_cov_peak.magnitude, "%"],
    #     ["TES Thermal Pct Coverage", "N/A", "N/A",
    #      tes_th_cov_elf.magnitude, "%",
    #      tes_th_cov_tlf.magnitude, "%",
    #      tes_th_cov_peak.magnitude, "%"],
    #     ["Boiler Thermal Pct Coverage", "N/A", "N/A",
    #      ab_th_cov_elf.magnitude, "%",
    #      ab_th_cov_tlf.magnitude, "%",
    #      ab_th_cov_peak.magnitude, "%"],
    #     ###########################
    #     # Energy Savings
    #     ###########################
    #     ["Thermal Energy Savings", "N/A", "N/A",
    #      round(elf_thermal_energy_savings.magnitude, 2), elf_thermal_energy_savings.units,
    #      round(tlf_thermal_energy_savings.magnitude, 2), tlf_thermal_energy_savings.units,
    #      round(peak_thermal_energy_savings.magnitude, 2), peak_thermal_energy_savings.units],
    #     ["Electrical Energy Savings", "N/A", "N/A",
    #      round(elf_electric_energy_savings.magnitude, 2), elf_electric_energy_savings.units,
    #      round(tlf_electric_energy_savings.magnitude, 2), tlf_electric_energy_savings.units,
    #      round(peak_electric_energy_savings.magnitude, 2), tlf_electric_energy_savings.units],
    #     ["Total Energy Savings", "N/A", "N/A",
    #      elf_total_energy_savings.magnitude, elf_total_energy_savings.units,
    #      tlf_total_energy_savings.magnitude, tlf_total_energy_savings.units,
    #      peak_total_energy_savings.magnitude, peak_total_energy_savings.units],
    #     ###########################
    #     # Costs
    #     ###########################
    #     ["Electricity Cost",
    #      round(electric_cost_baseline.magnitude, 2), electric_cost_baseline.units,
    #      round(elf_electric_cost_new.magnitude, 2), elf_electric_cost_new.units,
    #      round(tlf_electric_cost_new.magnitude, 2), tlf_electric_cost_new.units,
    #      round(peak_electric_cost_new.magnitude, 2), peak_electric_cost_new.units],
    #     ["Fuel Cost",
    #      round(thermal_cost_baseline.magnitude, 2), thermal_cost_baseline.units,
    #      round(elf_thermal_cost_total.magnitude, 2), elf_thermal_cost_total.units,
    #      round(tlf_thermal_cost_total.magnitude, 2), tlf_thermal_cost_total.units,
    #      round(peak_thermal_cost_total.magnitude, 2), peak_thermal_cost_total.units],
    #     ["CHP Installed Cost",
    #      "N/A", "N/A",
    #      round(elf_cost_data_dict["chp_installed_cost"].magnitude, 2), elf_cost_data_dict["chp_installed_cost"].units,
    #      round(tlf_cost_data_dict["chp_installed_cost"].magnitude, 2), tlf_cost_data_dict["chp_installed_cost"].units,
    #      round(peak_cost_data_dict["chp_installed_cost"].magnitude, 2),
    #      peak_cost_data_dict["chp_installed_cost"].units],
    #     ["CHP O&M Cost",
    #      "N/A", "N/A",
    #      round(elf_cost_data_dict["chp_om_cost"].magnitude, 2), elf_cost_data_dict["chp_om_cost"].units,
    #      round(tlf_cost_data_dict["chp_om_cost"].magnitude, 2), tlf_cost_data_dict["chp_om_cost"].units,
    #      round(peak_cost_data_dict["chp_om_cost"].magnitude, 2), peak_cost_data_dict["chp_om_cost"].units],
    #     ["TES Installed Cost",
    #      "N/A", "N/A",
    #      round(elf_cost_data_dict["tes_installed_cost"].magnitude, 2), elf_cost_data_dict["tes_installed_cost"].units,
    #      round(tlf_cost_data_dict["tes_installed_cost"].magnitude, 2), tlf_cost_data_dict["tes_installed_cost"].units,
    #      round(peak_cost_data_dict["tes_installed_cost"].magnitude, 2),
    #      peak_cost_data_dict["tes_installed_cost"].units],
    #     ["TES O&M Cost",
    #      "N/A", "N/A",
    #      round(elf_cost_data_dict["tes_om_cost"].magnitude, 2), elf_cost_data_dict["tes_om_cost"].units,
    #      round(tlf_cost_data_dict["tes_om_cost"].magnitude, 2), tlf_cost_data_dict["tes_om_cost"].units,
    #      round(peak_cost_data_dict["tes_om_cost"].magnitude, 2), peak_cost_data_dict["tes_om_cost"].units],
    #     ["PP Revenue",
    #      "N/A", "N/A",
    #      round(elf_cost_data_dict["pp_rev"].magnitude, 2), elf_cost_data_dict["pp_rev"].units,
    #      round(tlf_cost_data_dict["pp_rev"].magnitude, 2), tlf_cost_data_dict["pp_rev"].units,
    #      round(peak_cost_data_dict["pp_rev"].magnitude, 2), peak_cost_data_dict["pp_rev"].units],
    #     ["Simple Payback [Yrs]",
    #      "N/A", "N/A",
    #      round(elf_cost_data_dict["simple_payback"].magnitude, 2), elf_cost_data_dict["simple_payback"].units,
    #      round(tlf_cost_data_dict["simple_payback"].magnitude, 2), tlf_cost_data_dict["simple_payback"].units,
    #      round(peak_cost_data_dict["simple_payback"].magnitude, 2), peak_cost_data_dict["simple_payback"].units],
    #     ["Simple Payback ({}% incentive)".format(incentive_base_pct * 100),
    #      "N/A", "N/A",
    #      round(elf_cost_data_dict["incentive_payback"].magnitude, 2), elf_cost_data_dict["incentive_payback"].units,
    #      round(tlf_cost_data_dict["incentive_payback"].magnitude, 2), tlf_cost_data_dict["incentive_payback"].units,
    #      round(peak_cost_data_dict["incentive_payback"].magnitude, 2), peak_cost_data_dict["incentive_payback"].units],
    #     ###########################
    #     # Emissions Analysis
    #     ###########################
    #     ["CO2", round(baseline_total_co2.magnitude), baseline_total_co2.units,
    #      round(elf_total_co2.magnitude), elf_total_co2.units,
    #      round(tlf_total_co2.magnitude), tlf_total_co2.units,
    #      round(peak_total_co2.magnitude), peak_total_co2.units]
    # ]
    #
    # ##########################
    # Table: Display SA Inputs
    # ##########################

    # sa_header = ["Operating Mode", "SA Variable Name", "Lower Bound", "Upper Bound", "Base Value"]
    #
    # sa_inputs = [
    #     ["ELF", "Electricity Cost", 0, 0, 0],
    #     ["ELF", "Electricity Cost", 0, 0, 0],
    #     ["ELF", "Electricity Cost", 0, 0, 0],
    #     ["ELF", "Electricity Cost", 0, 0, 0],
    #     ["ELF", "Electricity Cost", 0, 0, 0],
    #     ["TLF", "Electricity Cost", 0, 0, 0],
    #     ["TLF", "Electricity Cost", 0, 0, 0],
    #     ["TLF", "Electricity Cost", 0, 0, 0],
    #     ["TLF", "Electricity Cost", 0, 0, 0],
    #     ["TLF", "Electricity Cost", 0, 0, 0],
    #     ["PP", "Electricity Cost", 0, 0, 0],
    #     ["PP", "Electricity Cost", 0, 0, 0],
    #     ["PP", "Electricity Cost", 0, 0, 0],
    #     ["PP", "Electricity Cost", 0, 0, 0],
    #     ["PP", "Electricity Cost", 0, 0, 0],
    #     ["Peak", "Electricity Cost", 0, 0, 0],
    #     ["Peak", "Electricity Cost", 0, 0, 0],
    #     ["Peak", "Electricity Cost", 0, 0, 0],
    #     ["Peak", "Electricity Cost", 0, 0, 0],
    #     ["Peak", "Electricity Cost", 0, 0, 0]
    # ]

    ###########################
    # Write results in Table to Excel file
    ###########################

    # df_results = pd.DataFrame(results_data, columns=data_header)
    #
    # results_file_path = \
    #     pathlib.Path(__file__).parent.resolve() / "results/{}_{}".format(class_dict['demand'].city,
    #                                                                      class_dict['demand'].state) / \
    #                                               "{}_{}_results.xlsx".format(class_dict['demand'].city,
    #                                                                           class_dict['demand'].state)
    #
    # sheet_name = class_dict['demand'].demand_file_name
    # if os.path.exists(results_file_path):
    #     writer = pd.ExcelWriter(results_file_path, engine='openpyxl', mode='a', if_sheet_exists='replace')
    # else:
    #     writer = pd.ExcelWriter(results_file_path, engine='openpyxl', mode='w')
    #
    # with writer as w:
    #     df_results.to_excel(w, sheet_name=sheet_name)
    #
    # print("Analysis for {}, {} completed.".format(class_dict["demand"].city, class_dict["demand"].state))
    # print("...")
    # print("Generating plots.")

    ##########################
    # Plots
    ##########################
    # plots.plot_max_rectangle_electric(demand_class=class_dict['demand'], chp_size=chp_size_elf)
    # plots.plot_max_rectangle_thermal(demand_class=class_dict['demand'], chp_size=chp_size_tlf)
    #
    # plots.plot_electrical_demand_curve(demand_class=class_dict['demand'])
    # plots.plot_thermal_demand_curve(demand_class=class_dict['demand'])
    #
    # plots.elf_plot_electric(elf_electric_gen_list=elf_electric_gen_list,
    #                         elf_electricity_bought_list=elf_electricity_bought_hourly, demand_class=class_dict['demand'])
    # plots.elf_plot_thermal(elf_chp_gen_btuh=elf_chp_gen_btuh, elf_tes_heat_flow_list=elf_tes_heat_flow_list,
    #                        elf_boiler_dispatch_hourly=elf_boiler_dispatch_hourly, demand_class=class_dict['demand'])
    # plots.elf_plot_tes_soc(elf_tes_soc=elf_tes_soc, demand_class=class_dict['demand'])
    #
    # plots.tlf_plot_electric(tlf_electric_gen_list=tlf_electric_gen_list,
    #                         tlf_electricity_bought_list=tlf_electricity_bought_hourly,
    #                         tlf_electricity_sold_list=tlf_electricity_sold, demand_class=class_dict['demand'])
    # plots.tlf_plot_thermal(tlf_chp_gen_btuh=tlf_chp_gen_btuh, tlf_tes_heat_flow_list=tlf_tes_heat_flow_list,
    #                        tlf_boiler_dispatch_hourly=tlf_boiler_dispatch_hourly, demand_class=class_dict['demand'])
    # plots.tlf_plot_tes_soc(tlf_tes_soc_list=tlf_tes_soc_list, demand_class=class_dict['demand'])
    #
    # plots.peak_plot_electric(peak_electric_gen_list=peak_electric_gen_list,
    #                          peak_electricity_bought_list=peak_electricity_bought_hourly,
    #                          peak_electricity_sold_list=peak_electric_sold_list, demand_class=class_dict['demand'])
    # plots.peak_plot_thermal(peak_chp_gen_btuh=peak_chp_gen_btuh, peak_tes_heat_flow_list=peak_tes_heat_flow_list,
    #                         peak_boiler_dispatch_hourly=peak_boiler_dispatch_hourly, demand_class=class_dict['demand'])
    # plots.peak_plot_tes_soc(peak_tes_soc=peak_tes_soc, demand_class=class_dict['demand'])


if __name__ == "__main__":
    main()
