"""
These classes initialize the operating parameters of each piece of equipment
"""

import pandas as pd
import numpy as np


class CHP:
    def __init__(self, capacity=0, heat_power=0, turn_down_ratio=0, part_load=np.empty(10, 2)):
        """
        This class defines the operating parameters of the mCHP system.
        :param capacity: Size of the CHP system in kW (kilowatts)
        :param heat_power: The heat-to-power ratio of the CHP system
        :param turn_down_ratio: The ratio of the maximum capacity to minimum capacity
        :param part_load: An array where column 0 is the partial load as a percent of max
            capacity and column 1 is the associated mCHP efficiency
        """
        self.cap = capacity
        self.hp = heat_power
        self.td = turn_down_ratio
        self.pl = part_load


class AuxBoiler:
    def __init__(self, capacity=0, efficiency=0, turn_down_ratio=0):
        """
        This class defines the operating parameters of the Auxiliary Boiler.
        :param capacity: Size of the boiler in BTUs (British Thermal Units)
        :param efficiency: The rated efficiency of the boiler
        :param turn_down_ratio: The ratio of the maximum capacity to minimum capacity
        """
        self.cap = capacity
        self.eff = efficiency
        self.td = turn_down_ratio


class Building:
    def __init__(self, file_name, net_metering=False):
        """
        This class defines the electrical and thermal load profiles of a mid-rise apartment
        building. The data is imported from the file 'input_load_profiles_hourly.csv' using
        pandas.
        :param file_name: String, file name of the .csv file with the load profile data
        :param net_metering: Boolean, True if the local electrical utility allows the building
        owner to sell excess electricity generated back to the grid
        """
        # Reads load profile data from .csv file
        df = pd.read_csv('{}.csv'.format(file_name))
        # Plucks electrical load data from the file using row and column locations
        df_el = df.iloc[8:, [0, 1, 2, 3, 16]]
        self.el = df_el
        # Plucks thermal load data from teh file using row and column locations
        df_hl = df.iloc[8:, [0, 1, 2, 3, 29]]
        self.hl = df_hl
        # Assigns and stores net metering boolean value
        self.nm = net_metering


class TES:
    def __init__(self, capacity=0, state_of_charge=0, charge=False, discharge=False):
        """
        This class defines the operating parameters of the TES (Thermal energy storage) system
        :param capacity: Size of the TES system in BTUs (British Thermal Units)
        :param state_of_charge: Percentage of the TES capacity that is currently used
        :param charge: Boolean, True if the TES system is currently charging
        :param discharge: Boolean, True if the TES system is currently discharging
        """
        self.cap = capacity
        self.soc = state_of_charge
        self.charge = charge
        self.discharge = discharge
