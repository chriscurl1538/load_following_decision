"""
Module description:
    These classes store data pulled from the .yaml file and the simulated demand profile (EnergyDemand class) and also
     initialize the operating parameters of the energy generation and storage systems (CHP, TES, and AuxBoiler class)
"""

import pathlib, pandas as pd, numpy as np
from lfd_package.modules.__init__ import ureg, Q_


class EnergyDemand:
    def __init__(self, file_name='default_file.csv', net_metering_status=None, grid_efficiency=None, electric_cost=None,
                 fuel_cost=None):
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
        net_metering_status: string
            This string reads "True" if net metering is allowed and excess electricity generated
            can be sold to the grid and "False" otherwise. This value is converted to Boolean
            type before being stored within the class.
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
        electric_demand_df = df.iloc[9:, 16]
        electric_demand_hourly = electric_demand_df.to_numpy()

        # Plucks thermal load data from the file using row and column locations
        heating_demand_df = df.iloc[9:, 29]
        heating_demand_hourly = heating_demand_df.to_numpy()

        # Energy Costs
        self.net_metering_status = eval(net_metering_status)
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

        self.hl = convert_numpy_to_float(heating_demand_hourly) * (ureg.Btu / ureg.hour)
        self.el = convert_numpy_to_float(electric_demand_hourly) * ureg.kW

        def sum_annual_demand(array=None):
            annual_hours = 8760 * ureg.hour
            avg_dem = sum(array) / len(array)
            total_energy = avg_dem * annual_hours
            return total_energy

        self.annual_el = sum_annual_demand(array=self.el).to(ureg.kWh)
        self.annual_hl = sum_annual_demand(array=self.hl).to(ureg.Btu)

        # Emissions information
        self.ng_co2e = 14.43 * (ureg.kg / ureg.megaBtu)  # source: https://www.epa.gov/energy/greenhouse-gases-equivalencies-calculator-calculations-and-references)

        nw_emissions_dict = {
            'co2': 1575 * (ureg.lbs / ureg.MWh),
            'nox': 0.93 * (ureg.lbs / ureg.MWh),
            'so2': 0.52 * (ureg.lbs / ureg.MWh),
            'pm': 0.08 * (ureg.lbs / ureg.MWh),
            'voc': 0.04 * (ureg.lbs / ureg.MWh),
            'nh3': 0.02 * (ureg.lbs / ureg.MWh)
        }

        self.nw_emissions = nw_emissions_dict

        fl_emissions_dict = {
            'co2': 1098 * (ureg.lbs / ureg.MWh),
            'nox': 0.34 * (ureg.lbs / ureg.MWh),
            'so2': 0.32 * (ureg.lbs / ureg.MWh),
            'pm': 0.07 * (ureg.lbs / ureg.MWh),
            'voc': 0.01 * (ureg.lbs / ureg.MWh),
            'nh3': 0.03 * (ureg.lbs / ureg.MWh)
        }

        self.fl_emissions = fl_emissions_dict

        midwest_emissions_dict = {
            'co2': 1837 * (ureg.lbs / ureg.MWh),
            'nox': 1.18 * (ureg.lbs / ureg.MWh),
            'so2': 1.58 * (ureg.lbs / ureg.MWh),
            'pm': 0.11 * (ureg.lbs / ureg.MWh),
            'voc': 0.03 * (ureg.lbs / ureg.MWh),
            'nh3': 0.03 * (ureg.lbs / ureg.MWh)
        }

        self.midwest_emissions = midwest_emissions_dict

        sw_emissions_dict = {
            'co2': 1366 * (ureg.lbs / ureg.MWh),
            'nox': 0.53 * (ureg.lbs / ureg.MWh),
            'so2': 0.19 * (ureg.lbs / ureg.MWh),
            'pm': 0.07 * (ureg.lbs / ureg.MWh),
            'voc': 0.02 * (ureg.lbs / ureg.MWh),
            'nh3': 0.03 * (ureg.lbs / ureg.MWh)
        }

        self.sw_emissions = sw_emissions_dict


class CHP:
    def __init__(self, fuel_input_rate=None, turn_down_ratio=None,
                 part_load_electrical=None, part_load_thermal=None, chp_electric_eff=None, chp_thermal_eff=None,
                 percent_availability=None, cost=None):
        """
        Docstring updated on 9/24/22

        This class defines the operating parameters of the CHP system.

        Parameters
        ----------
        fuel_type: string
            Type of fuel used by the CHP system
        fuel_input_rate: Quantity (float)
            CHP fuel input rate in units of Btu/hour
        turn_down_ratio: float
            The turn down ratio of the CHP system. Defines the lower operating limit
            that CHP can operate at. Dimensionless. This value is converted to a
            decimal percentage of capacity (ie: 50% is 0.5) before being stored.
        part_load_electrical: numpy.ndarray
            Numpy array of electrical part-load efficiencies. Column 0 contains
            the partial loads as percentages (ie: 50% is 50). Column 1 contains
            the efficiencies as decimal values (ie: 50% is 0.5). Dimensionless
        part_load_thermal: numpy.ndarray
            Numpy array of thermal part-load efficiencies. Column 0 contains
            the partial loads as percentages (ie: 50% is 50). Column 1 contains
            the efficiencies as decimal values (ie: 50% is 0.5). Dimensionless
        chp_electric_eff: float
            Electrical efficiency of CHP at full load as a percentage (ie: 50% is 0.5).
            Dimensionless
        chp_thermal_eff: float
            Thermal efficiency of CHP at full load as a percentage (ie: 50% is 0.5).
            Dimensionless
        percent_availability: float
            Annual availability of CHP as a percentage (ie: 50% is 0.5). Accounts for
            maintenance downtime. Dimensionless. This value is converted to Quantity
            with units of hours before being stored within the class.
        cost: Quantity (float)
            Incremental installed cost of CHP with units of $/kW. This value is converted
            to a dimensionless quantity representing the installed cost of the system
            before being stored within the class. TODO: Is this material + installation labor?
        """
        self.fuel_input_rate = fuel_input_rate * (ureg.Btu / ureg.hour)
        self.el_pl_eff = part_load_electrical
        self.th_pl_eff = part_load_thermal
        self.el_nominal_eff = chp_electric_eff
        self.th_nominal_eff = chp_thermal_eff
        self.incremental_cost = cost * 1/ureg.kW
        try:
            chp_min_pl = 1 / turn_down_ratio
        except ZeroDivisionError:
            chp_min_pl = 0
        self.min_pl = chp_min_pl
        self.available_hours = percent_availability * Q_(8760, ureg.hour)


class TES:
    def __init__(self, start=None, discharge=None, cost=None):
        """
        Docstring updated on 9/24/22

        This class defines the operating parameters of the TES (thermal energy storage) system

        Parameters
        ----------
        start: Quantity (float)
            The starting energy level of the TES system when the simulation begins in units of Btu
            TODO: Change from Energy to SOC format
        discharge: Quantity (float)
            The maximum discharge rate of the TES system in units of Btu/hour
        cost: Quantity (float)
            The incremental cost of the system in units of $/kWh. This value is converted to
            a dimensionless Quantity representing installed cost before being stored
            TODO: Add incremental cost for power system ($/kW) and combine with system_cost,
             then store as total cost
        """
        self.start = start * ureg.Btu
        self.discharge = discharge * ureg('Btu/hr')
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
        try:
            ab_min_pl = 1 / turn_down_ratio
        except ZeroDivisionError:
            ab_min_pl = 0
        self.min_pl = ab_min_pl
