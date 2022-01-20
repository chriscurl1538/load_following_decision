"""
Initializes characteristics of equipment
"""

import numpy as np
import pandas
from pint import UnitRegistry as ureg


class CHP:
    def __init__(self, capacity=0, heat_power=0, turn_down_ratio=0):
        """
        Defines the operating params of the micro-cogeneration system.
        Part-load efficiency data is sourced from the US EPA CHP Partnership's
        "Catalog of CHP Technologies, Section 2: Technology Characterization -
        Reciprocating Internal Combustion Engines". Data is specific to the
        Wartsila 20V34SG Generator's terminal efficiency (LHV).
        :param capacity: Size of the CHP system in kW
        :param heat_power: The heat-to-power ratio of the CHP system
        """
        self.cap = capacity
        self.hp = heat_power
        self.td = turn_down_ratio
        self.part_load = np.array([[30, 34.4],
                          [40, 37.9],
                          [50, 40.7],
                          [60, 42.0],
                          [70, 42.7],
                          [80, 43.7],
                          [90, 44.9],
                          [100, 45.7]])


class AuxBoiler:
    def __init__(self, capacity, max_efficiency, turn_down_ratio):
        self.cap = capacity
        self.eff = max_efficiency
        self.td = turn_down_ratio


class Building:
    def __init__(self, heat_load, electrical_load, net_metering=False):
        self.hl = heat_load
        self.el = electrical_load
        self.nm = net_metering

    def import_load_profile(self, file_name_el, file_name_hl):
        """
        Imports csv files with the annual electrical and thermal load profiles.
        This is sourced from an eQuest energy model for a mid-rise apartment building.
        :param file_name_el: String with file name of the electrical load profile
        :param file_name_hl: String with file name of the heating load profile
        :return: None
        """
        df_el = pandas.read_csv('{}.csv'.format(file_name_el))
        print(df_el)
        self.el = df_el
        df_hl = pandas.read_csv('{}.csv'.format(file_name_hl))
        print(df_hl)
        self.hl = df_hl


class EnergyWasted:
    def __init__(self, heat_wasted=0, electricity_wasted=0):
        self.hw = heat_wasted
        self.ew = electricity_wasted
