"""
Module description:
    These classes initialize the operating parameters of each element of the
    energy system (mCHP, TES, Aux Boiler, Energy Demand)
"""

import pandas as pd
import numpy as np
import pathlib


# TODO: Consider having optional chp_min input that can be entered instead of turn_down_ratio
class CHP:
    def __init__(self, capacity=0, heat_power=0, turn_down_ratio=0, thermal_output_to_fuel_input=0,
                 part_load=np.empty([10, 2])):
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
        self.out_in = thermal_output_to_fuel_input


class AuxBoiler:
    def __init__(self, capacity=0, efficiency=0, turn_down_ratio=0):
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
    def __init__(self, file_name='default_file.csv', electric_cost=0, fuel_cost=0):
        """
        This class defines the electricity and heating demand of a mid-
        rise apartment building.

        The data is imported from the file 'default_file.csv'
        using pandas.

        Parameters
        ----------
        file_name: string
            File name of the .csv file with the load profile data. This can be changed from the
            default value by modifying the name in the .yaml file.
        """
        # Reads load profile data from .csv file
        cwd = pathlib.Path(__file__).parent.resolve() / 'input_files'
        self.demand_file_name = file_name
        df = pd.read_csv(cwd / file_name)

        # Plucks electrical load data from the file using row and column locations
        electric_demand_df = df.iloc[9:, 16]
        electric_demand_hourly = electric_demand_df.to_numpy()
        self.el = electric_demand_hourly

        # Plucks thermal load data from the file using row and column locations
        heating_demand_df = df.iloc[9:, 29]
        heating_demand_hourly = heating_demand_df.to_numpy()
        self.hl = heating_demand_hourly

        # Assigns remaining values
        self.el_cost = electric_cost
        self.fuel_cost = fuel_cost

        def sum_annual_demand(array=np.empty([8760, 2])):
            demand_items = []
            for i in range(array.shape[0]):
                demand = float(array[i])
                assert demand >= 0
                demand_items.append(demand)
            demand_sum = sum(demand_items)
            return demand_sum

        self.annual_el = sum_annual_demand(array=self.el)
        self.annual_hl = sum_annual_demand(array=self.hl)


class TES:
    def __init__(self, capacity=0):
        """
        This class defines the operating parameters of the TES (Thermal energy storage) system

        capacity: int
            Size of the TES system in BTUs (British Thermal Units)
        """
        self.cap = capacity
