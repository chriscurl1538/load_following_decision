"""
Module description:
    These classes initialize the operating parameters of each element of the
    energy system (mCHP, TES, Aux Boiler, Energy Demand)
"""

import pandas as pd
import numpy as np


# TODO: Consider having optional chp_min input that can be entered instead of turn_down_ratio
class CHP:
    def __init__(self, capacity, heat_power, turn_down_ratio, part_load=np.empty([10, 2])):
        """
        This class defines the operating parameters of the mCHP system.

        Parameters
        ----------
        capacity: float
            Size of the CHP system in kW (kilowatts)
        heat_power: int
            The heat-to-power ratio of the CHP system
        turn_down_ratio: float
            The ratio of the maximum capacity to minimum capacity
        part_load: numpy.ndarray
            An array where column 0 is the partial load as a percent of max
            capacity and column 1 is the associated mCHP efficiency
        """
        self.cap = capacity
        self.hp = heat_power
        self.td = turn_down_ratio
        self.pl = part_load


class AuxBoiler:
    def __init__(self, capacity, efficiency, turn_down_ratio):
        """
        This class defines the operating parameters of the Auxiliary Boiler.

        Parameters
        ----------
        capacity: int
            Size of the boiler in BTUs (British Thermal Units)
        efficiency: float
            The rated efficiency of the boiler
        turn_down_ratio: float
            The ratio of the maximum capacity to minimum capacity
        """
        self.cap = capacity
        self.eff = efficiency
        self.td = turn_down_ratio


class EnergyDemand:
    def __init__(self, file_name, electric_cost, fuel_cost, net_metering=False):
        """
        This class defines the electricity and heating demand of a mid-
        rise apartment building.

        The data is imported from the file 'input_load_profiles_hourly.csv'
        using pandas.

        Parameters
        ----------
        file_name: string
            File name of the .csv file with the load profile data
        net_metering: boolean
            True if the local electrical utility allows the building
            owner to sell excess electricity generated back to the grid
        """
        # Reads load profile data from .csv file
        df = pd.read_csv(file_name)
        # Plucks electrical load data from the file using row and column locations
        electric_demand_df = df.iloc[8:, [0, 1, 2, 3, 16]]
        electric_demand_hourly = electric_demand_df.to_numpy()
        self.el = electric_demand_hourly
        # Plucks thermal load data from teh file using row and column locations
        heating_demand_df = df.iloc[8:, [0, 1, 2, 3, 29]]
        heating_demand_hourly = heating_demand_df.to_numpy()
        self.hl = heating_demand_hourly
        # Assigns and stores net metering boolean value
        self.nm = net_metering

        self.el_cost = electric_cost
        self.fuel_cost = fuel_cost


# class TES:
#     def __init__(self, capacity=0, state_of_charge=0, charge=False, discharge=False):
#         """
#         This class defines the operating parameters of the TES (Thermal energy storage) system
#
#         capacity: int
#             Size of the TES system in BTUs (British Thermal Units)
#         state_of_charge: float
#             Percentage of the TES capacity that is currently used
#         charge: boolean
#             True if the TES system is currently charging
#         discharge: boolean
#             True if the TES system is currently discharging
#         """
#         self.cap = capacity
#         self.soc = state_of_charge
#         self.charge = charge
#         self.discharge = discharge
