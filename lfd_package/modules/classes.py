"""
Module description:
    These classes store data pulled from the .yaml file and the simulated demand profile (EnergyDemand class) and also
     initialize the operating parameters of the energy generation and storage systems (CHP, TES, and AuxBoiler class)
"""

import pathlib, pandas as pd, numpy as np
from lfd_package.modules.__init__ import ureg


class EnergyDemand:
    def __init__(self, file_name='default_file.csv', grid_efficiency=None, electric_cost=None,
                 fuel_cost=None, city=None, state=None):
        """
        Docstring updated on 9/24/22

        This class stores information from eQuest building demand profile simulations,
        which are fed in via a .csv file. By default, this class imports data from the
        'default_file.csv' file in the /input_files folder.

        Parameters
        ----------
        file_name: string
            This is the file name of the .csv file from which the building demand profile
            data is pulled. The user inputs this name by including it in the .yaml file located
            in the /input_files folder.
        grid_efficiency: float
            This is the efficiency of the local electrical subgrid region as a decimal value
            (ie: 50% is 0.5). Dimensionless
        electric_cost: Quantity (float)
            The cost of electricity in units of $/kWh
        fuel_cost: Quantity (float)
            The cost of fuel in units of $/MMBtu
        """
        # Reads load profile data from .csv file
        cwd = pathlib.Path(__file__).parent.parent.resolve() / 'input_files'
        self.demand_file_name = file_name
        df = pd.read_csv(cwd / file_name)

        # Plucks electrical load data from the file using row and column locations
        electric_demand_df = df.iloc[:, 1]
        electric_demand_hourly = electric_demand_df.to_numpy()

        # Plucks thermal load data from the file using row and column locations
        heating_demand_df = df.iloc[:, 9]
        heating_demand_hourly = heating_demand_df.to_numpy()

        # Energy Costs
        self.grid_efficiency = grid_efficiency
        self.el_cost = electric_cost * (1/ureg.kWh)
        self.fuel_cost = fuel_cost * (1/ureg.megaBtu)

        def convert_numpy_to_float(array=None):
            float_list = []
            for item in array:
                f = float(item)
                float_list.append(f)
            float_array = np.array(float_list, dtype=float)
            return float_array

        heat_load_joules = convert_numpy_to_float(heating_demand_hourly) * (ureg.joules / ureg.hour)
        self.hl = heat_load_joules.to(ureg.Btu / ureg.hours)
        electric_load_joules = convert_numpy_to_float(electric_demand_hourly) * (ureg.joules / ureg.hour)
        self.el = electric_load_joules.to(ureg.kW)

        self.peak_hl = max(self.hl)
        self.peak_el = max(self.el)

        def sum_annual_demand(array=None):
            annual_hours = 8760 * ureg.hour
            avg_dem = sum(array) / len(array)
            total_energy = avg_dem * annual_hours
            return total_energy

        self.annual_el = sum_annual_demand(array=self.el).to(ureg.kWh)
        self.annual_hl = sum_annual_demand(array=self.hl).to(ureg.Btu)

        # Emissions information
        self.city = city
        self.state = state
        self.ng_co2 = 14.43 * (ureg.kg / ureg.megaBtu)  # source: https://www.epa.gov/energy/greenhouse-gases-equivalencies-calculator-calculations-and-references)

        # Marginal Emissions
        self.nw_emissions_co2 = 1575 * (ureg.lbs / ureg.MWh)
        self.fl_emissions_co2 = 1098 * (ureg.lbs / ureg.MWh)
        self.midwest_emissions_co2 = 1837 * (ureg.lbs / ureg.MWh)
        self.sw_emissions_co2 = 1366 * (ureg.lbs / ureg.MWh)
        # TODO: Add for illinois
        # TODO: Add for alaska

        # Average Emissions (accounts for losses)
        self.nwpp_emissions_co2 = 662.5 * (ureg.lbs / ureg.MWh)
        self.frcc_emissions_co2 = 870.4 * (ureg.lbs / ureg.MWh)
        self.mrow_emissions_co2 = 1040.6 * (ureg.lbs / ureg.MWh)
        self.aznm_emissions_co2 = 855.8 * (ureg.lbs / ureg.MWh)
        self.akgd_emissions_co2 = 1114.7 * (ureg.lbs / ureg.MWh)
        self.rfcw_emissions_co2 = 1093.2 * (ureg.lbs / ureg.MWh)


class CHP:
    def __init__(self, turn_down_ratio=None, cost=None):
        """
        Docstring updated on 9/24/22

        This class defines the operating parameters of the CHP system.

        Parameters
        ----------
        turn_down_ratio: float
            The turn down ratio of the CHP system. Defines the lower operating limit
            that CHP can operate at. Dimensionless. This value is converted to a
            decimal percentage of capacity (ie: 50% is 0.5) before being stored.
        cost: Quantity (float)
            Incremental installed cost of CHP with units of $/kW. This value is converted
            to a dimensionless quantity representing the installed cost of the system
            before being stored within the class. TODO: Is this material + installation labor?
        """
        self.incremental_cost = cost * 1/ureg.kW
        try:
            chp_min_pl = 1 / turn_down_ratio
        except ZeroDivisionError:
            chp_min_pl = 0
        self.min_pl = chp_min_pl


class TES:
    def __init__(self, start=None, cost=None):
        """
        Docstring updated on 9/24/22

        This class defines the operating parameters of the TES (thermal energy storage) system

        Parameters
        ----------
        start: Quantity (float)
            The starting energy level of the TES system when the simulation begins in terms of SOC
        cost: Quantity (float)
            The incremental cost of the system in units of $/kWh. This value is converted to
            a dimensionless Quantity representing installed cost before being stored
            TODO: Add incremental cost for power system ($/kW) and combine with system_cost,
             then store as total cost
        """
        self.start = start
        self.incremental_cost = cost * (1/ureg.kWh)


class AuxBoiler:
    def __init__(self, capacity=None, efficiency=None, turn_down_ratio=None):
        """
        Docstring updated on 9/24/22

        This class defines the operating parameters of the Auxiliary Boiler.

        Parameters
        ----------
        capacity: Quantity (float)
            Size of the boiler in units of Btu/hr (Btu = British thermal units)
        efficiency: float
            The efficiency of the boiler when operating at full load expressed
            as a decimal value (ie: 50% = 0.5). Dimensionless
        turn_down_ratio: float
            Represents the minimum capacity of the boiler, expressed as the
            ratio of the maximum capacity to the minimum capacity. This value
            is converted to minimum capacity as a decimal percentage (ie: 50% = 0.5)
            of full capacity before being stored.
        """
        self.cap = capacity * (ureg.Btu / ureg.hour)
        self.eff = efficiency
