"""
Initializes characteristics of equipment
"""

import numpy as np
import pandas as pd


class CHP:
    def __init__(self, capacity=0, heat_power=0, turn_down_ratio=0, part_load=0):
        """
        Defines the operating params of the mCHP system.
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
        self.pl = part_load


class AuxBoiler:
    def __init__(self, capacity, max_efficiency, turn_down_ratio):
        self.cap = capacity
        self.eff = max_efficiency
        self.td = turn_down_ratio


class Building:     # TODO: Sum hourly load data to get monthly data
    def __init__(self, file_name, net_metering=False):
        df = pd.read_csv('{}.csv'.format(file_name))
        df_el = df.iloc[8:, [0, 1, 2, 3, 16]]
        self.el = df_el
        df_hl = df.iloc[8:, [0, 1, 2, 3, 29]]
        self.hl = df_hl
        self.nm = net_metering


class TES:  # TODO: is a rate of charge or rate of discharge needed?
    def __init__(self, size=0, state_of_charge=0, charge=False, discharge=False):
        """
        Initializes the thermal energy storage system
        :param size: float, How much thermal energy the TES system holds
        :param state_of_charge: float, What percentage of the TES capacity is currently used
        :param charge: Boolean, whether the TES system is currently charging
        :param discharge: Boolean, whether the TES system is currently discharging
        """
        self.size = size
        self.soc = state_of_charge
        self.charge = charge
        self.discharge = discharge


class EnergyWasted:
    def __init__(self, heat_wasted=0, electricity_wasted=0):
        self.hw = heat_wasted
        self.ew = electricity_wasted


if __name__ == '__main__':
    x = Building(file_name="input_load_profiles_hourly")
    heat_load = x.hl
    electrical_load = x.el
    print(heat_load)
