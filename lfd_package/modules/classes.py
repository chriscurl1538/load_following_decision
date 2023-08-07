"""
Module description:
    These classes store data pulled from the .yaml file and the simulated demand profile (EnergyDemand class) and also
     initialize the operating parameters of the energy generation and storage systems (CHP, TES, and AuxBoiler class)
"""

import math, pathlib, pandas as pd, numpy as np
from datetime import datetime, timedelta
from lfd_package.modules.__init__ import ureg, Q_


class EnergyDemand:
    def __init__(self, file_name='default_file.csv', city=None, state=None, grid_efficiency=None,
                 summer_start_inclusive=None, winter_start_inclusive=None, sim_ab_efficiency=None):
        """
        Docstring updated on 9/24/22

        This class stores information from EnergyPlus building demand profile simulations,
        which are fed in via a .csv file. By default, this class imports data from the
        'default_file.csv' file in the /input_files folder.

        Parameters
        ----------
        file_name: str
            This is the file name of the .csv file containing hourly electrical and heating demand data.
            The user can change this value in the .yaml file located in the /input_files folder.
        city: str
            This is the name of one of 7 accepted city locations.
        state: str
            This is the name of one of 7 accepted state locations.
        grid_efficiency: float
            This is the efficiency of the local electrical subgrid region as a decimal value
            (ie: 50% is 0.5).
        summer_start_inclusive: int
            Integer value between 1-12 (Jan-Dec) indicating the month summer starts for utility
            billing purposes.
        winter_start_inclusive: int
            See above.
        sim_ab_efficiency: float
            User must enter the assumed EnergyPlus boiler efficiency in the .yaml file so it
            may be modified as needed.
        """
        # Reads load profile data from .csv file
        cwd = pathlib.Path(__file__).parent.parent.resolve() / 'input_files'
        self.demand_file_name = file_name
        df = pd.read_csv(cwd / file_name)

        # Plucks electrical metering data from the file using row and column locations
        electric_metering_df = df["Electricity:Facility [J](Hourly)"]
        electric_demand_hourly = electric_metering_df.to_numpy()

        # Plucks thermal metering data from the file using row and column locations
        try:
            heating_metering_df = df["Gas:Facility [J](Hourly)"]
        except KeyError:
            heating_metering_df = df["Gas:Facility [J](Hourly) "]
        heating_metering_hourly = heating_metering_df.to_numpy()

        # Plucks month numbers from metering data file     # TODO: Test
        meter_dates_array = df["Date/Time"].to_numpy(dtype=str)
        meter_months_hourly = []
        for item in meter_dates_array:
            date = self.standardize_date_str(date_str=item)
            meter_months_hourly.append(date.month)

        self.meter_months_hourly = np.array(meter_months_hourly, dtype=int)
        self.sim_ab_efficiency = float(sim_ab_efficiency)

        # Convert heat metering to heating demand using EnergyPlus assumed heating efficiency value
        heating_demand_hourly = [item * self.sim_ab_efficiency for item in heating_metering_hourly]

        ##############################
        # General Info
        ##############################

        # Location information
        self.city = city.lower()
        self.state = state.lower()

        # National Average Grid Efficiency
        self.grid_efficiency = float(grid_efficiency)

        # Energy Costs - Seasonal
        self.summer_start_month = int(summer_start_inclusive)
        self.winter_start_month = int(winter_start_inclusive)

        ################################
        # Energy Demand Info
        ################################

        # Annual and monthly peaks and sums
        heat_load_joules = self.convert_to_float_numpy(heating_demand_hourly) * (ureg.joules / ureg.hour)
        electric_load_joules = self.convert_to_float_numpy(electric_demand_hourly) * (ureg.joules / ureg.hour)

        self.hl = heat_load_joules.to(ureg.Btu / ureg.hours)
        self.el = electric_load_joules.to(ureg.kW)

        self.summer_weight_el, self.winter_weight_el = self.seasonal_weights_hourly_data(dem_profile=self.el)
        self.summer_weight_hl, self.winter_weight_hl = self.seasonal_weights_hourly_data(dem_profile=self.hl)

        self.annual_sum_el = self.sum_annual_demand(array=self.el).to(ureg.kWh)
        self.annual_sum_hl = self.sum_annual_demand(array=self.hl).to(ureg.Btu)

        self.annual_peak_hl = max(self.hl)
        self.annual_peak_el = max(self.el)

        self.monthly_peaks_list_el = self.monthly_demand_peaks(dem_profile=self.el)
        self.monthly_peaks_list_hl = self.monthly_demand_peaks(dem_profile=self.hl)

        self.monthly_sums_list_el = self.monthly_energy_sums(dem_profile=self.el)
        self.monthly_sums_list_hl = self.monthly_energy_sums(dem_profile=self.hl)

    #####################################
    # Methods
    #####################################

    def standardize_date_str(self, date_str):
        assert isinstance(date_str, str)
        date_list = date_str.split()
        year = datetime.now().year
        new_date = "{}/{} {}".format(date_list[0], year, date_list[1])
        try:
            new_datetime = datetime.strptime(new_date, '%m/%d/%Y %H:%M:%S')
        except ValueError:
            rollback_str = new_date.replace(' 24', ' 23')
            rollback_datetime = datetime.strptime(rollback_str, '%m/%d/%Y %H:%M:%S')
            new_datetime = rollback_datetime + timedelta(hours=1)
        return new_datetime

    def convert_units(self, values_list=None, units_to_str=None):
        assert 1 < len(values_list)
        converted_list = []
        if values_list[0].check('[power]'):
            for item in values_list:
                new_item = item * Q_(1, ureg.hours)
                new_item.to(units_to_str)
                assert new_item.check('[energy]')
                converted_list.append(new_item)
        elif values_list[0].check('[energy]'):
            for item in values_list:
                new_item = item / Q_(1, ureg.hours)
                new_item.to(units_to_str)
                assert new_item.check('[power]')
                converted_list.append(new_item)
        else:
            raise Exception('only converts between kWh and kW units')
        return converted_list

    def convert_to_float_numpy(self, array=None):
        float_list = []
        for item in array:
            f = float(item)
            float_list.append(f)
        float_array = np.array(float_list, dtype=float)
        return float_array

    def sum_annual_demand(self, array=None):
        annual_hours = 8760 * ureg.hour
        avg_dem = sum(array) / len(array)
        total_energy = avg_dem * annual_hours
        return total_energy

    def seasonal_weights_hourly_data(self, dem_profile=None):     # TODO: Test
        summer_start = int(self.summer_start_month)
        winter_start = int(self.winter_start_month)
        month_list = self.meter_months_hourly
        summer_index_list = []
        winter_index_list = []

        for index, i in enumerate(month_list):
            if summer_start <= int(i) < winter_start:
                summer_index_list.append(index)
            else:
                winter_index_list.append(index)

        summer_weight_list = []
        for index in summer_index_list:
            # TODO: Unit issue - need to be consistent in passing power or energy
            item = dem_profile[index] * Q_(1, ureg.hours)
            summer_weight_list.append(item)

        winter_weight_list = []
        for index in winter_index_list:
            item = dem_profile[index] * Q_(1, ureg.hours)
            winter_weight_list.append(item)

        summer_sum = sum(summer_weight_list)
        winter_sum = sum(winter_weight_list)
        total = (sum(dem_profile) * Q_(1, ureg.hours)).to_reduced_units()
        assert math.isclose(summer_sum.magnitude + winter_sum.magnitude, total.magnitude)

        if total.magnitude != 0:
            summer_weight = summer_sum / total
            winter_weight = winter_sum / total
            return summer_weight, winter_weight
        else:
            raise Exception("The array passed to EnergyDemand class seasonal_weights_hourly_data() method is all zeros")

    def seasonal_weights_monthly_data(self, monthly_data=None):
        summer_start = int(self.summer_start_month)
        winter_start = int(self.winter_start_month)
        summer_index_list = []
        winter_index_list = []

        for index, item in enumerate(monthly_data):
            if summer_start <= int(index+1) < winter_start:
                summer_index_list.append(index)
            else:
                winter_index_list.append(index)

        summer_weight_list = []
        for index in summer_index_list:
            item = monthly_data[index]
            summer_weight_list.append(item)

        winter_weight_list = []
        for index in winter_index_list:
            item = monthly_data[index]
            winter_weight_list.append(item)

        summer_sum = sum(summer_weight_list)
        winter_sum = sum(winter_weight_list)
        total = sum(monthly_data)
        assert math.isclose(summer_sum.magnitude + winter_sum.magnitude, total.magnitude)

        summer_weight = summer_sum / total
        winter_weight = winter_sum / total

        return summer_weight, winter_weight

    def monthly_demand_peaks(self, dem_profile=None):  # TODO: Test
        month_list = self.meter_months_hourly
        month_demand_list = []
        monthly_peak_list = []
        for index, item in enumerate(month_list):
            if index == 0 or month_list[index] == month_list[index - 1]:
                month_demand_list.append(dem_profile[index])
            else:
                monthly_peak_list.append(max(month_demand_list))
                month_demand_list = list()
                month_demand_list.append(dem_profile[index])
        return monthly_peak_list

    def monthly_energy_sums(self, dem_profile=None):
        month_list = self.meter_months_hourly
        month_demand_list = []
        monthly_sum_list = []
        for index, item in enumerate(month_list):
            if index == 0 or month_list[index] == month_list[index - 1]:
                month_demand_list.append(dem_profile[index])
            else:
                energy_sum = sum(month_demand_list) * Q_(1, ureg.hours)
                energy_sum.ito_reduced_units()
                monthly_sum_list.append(energy_sum)
                month_demand_list = list()
                month_demand_list.append(dem_profile[index])
        return monthly_sum_list


class Emissions(EnergyDemand):
    def __init__(self, file_name, city, state, grid_efficiency, summer_start_inclusive, winter_start_inclusive,
                 sim_ab_efficiency):
        super().__init__(file_name, city, state, grid_efficiency, summer_start_inclusive, winter_start_inclusive,
                         sim_ab_efficiency)

        # NG Emissions
        self.ng_co2 = 14.43 * (ureg.kg / ureg.megaBtu)  # source: https://www.epa.gov/energy/greenhouse-gases-equivalencies-calculator-calculations-and-references)

        # Average Emissions (accounts for losses)
        self.avg_emissions = {
            "seattle, wa": Q_(662.5, ureg.lbs / ureg.MWh),
            "helena, mt": Q_(662.5, ureg.lbs / ureg.MWh),
            "great falls, mt": Q_(662.5, ureg.lbs / ureg.MWh),
            "miami, fl": Q_(870.4, ureg.lbs / ureg.MWh),
            "duluth, mn": Q_(1040.6, ureg.lbs / ureg.MWh),
            "international falls, mn": Q_(1040.6, ureg.lbs / ureg.MWh),
            "phoenix, az": Q_(855.8, ureg.lbs / ureg.MWh),
            "tuscon, az": Q_(855.8, ureg.lbs / ureg.MWh),
            "fairbanks, ak": Q_(1114.7, ureg.lbs / ureg.MWh),
            "chicago, il": Q_(1093.2, ureg.lbs / ureg.MWh),
            "buffalo, ny": Q_(243.6, ureg.lbs / ureg.MWh),
            "honolulu, hi": Q_(1711.5, ureg.lbs / ureg.MWh)
        }


class EnergyCosts(EnergyDemand):
    def __init__(self, file_name, city, state, grid_efficiency, summer_start_inclusive, winter_start_inclusive,
                 sim_ab_efficiency, meter_type_el=None, meter_type_fuel=None, schedule_type_el=None, schedule_type_fuel=None,
                 master_metered_el=None, single_metered_el=None, master_metered_fuel=None, single_metered_fuel=None,
                 no_apts=None):
        super().__init__(file_name, city, state, grid_efficiency, summer_start_inclusive, winter_start_inclusive,
                         sim_ab_efficiency)

        #####################################
        # Electricity Charges
        #####################################

        # General Info
        self.meter_type_el = meter_type_el
        self.meter_type_fuel = meter_type_fuel
        self.schedule_type_el = schedule_type_el
        self.schedule_type_fuel = schedule_type_fuel
        self.no_apts = no_apts

        # Dictionaries of Rates
        self.master_meter_el_dict = master_metered_el
        self.single_meter_el_dict = single_metered_el
        self.master_meter_fuel_dict = master_metered_fuel
        self.single_meter_fuel_dict = single_metered_fuel


class CHP(EnergyDemand):
    def __init__(self, file_name, city, state, grid_efficiency, summer_start_inclusive, winter_start_inclusive,
                 sim_ab_efficiency, turn_down_ratio=None, installed_cost=None):
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

        super().__init__(file_name, city, state, grid_efficiency, summer_start_inclusive, winter_start_inclusive,
                         sim_ab_efficiency)

        # CHP Units
        self.chp_size_units = ureg.kW

        # CHP Specifications
        try:
            chp_min_pl = 1 / turn_down_ratio
        except ZeroDivisionError:
            chp_min_pl = 0
        self.min_pl = chp_min_pl

        # Labor, material, and installation costs (installed cost)
        self.installed_cost = installed_cost * 1/ureg.kW


class TES(EnergyDemand):
    def __init__(self, file_name, city, state, grid_efficiency, summer_start_inclusive, winter_start_inclusive,
                 sim_ab_efficiency, start=None, vol_rate=None, energy_density=None, size_cost=None, rate_cost=None):
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
        super().__init__(file_name, city, state, grid_efficiency, summer_start_inclusive, winter_start_inclusive,
                         sim_ab_efficiency)

        # Units
        self.tes_size_units = ureg.Btu

        # TES Specifications
        self.start = float(start)
        self.vol_rate = float(vol_rate) * (ureg.liters / ureg.hours)
        self.energy_density = float(energy_density) * (ureg.kWh / ureg.meters**3)
        self.discharge_kw = (self.vol_rate * self.energy_density).to(ureg.kW)   # TODO: Implement

        # TES Materials Costs
        self.size_cost = float(size_cost) * (1/ureg.kWh)     # TODO: raname variable?
        self.rate_cost = float(rate_cost) * (1/ureg.kW)     # TODO: raname variable?


class AuxBoiler(EnergyDemand):
    def __init__(self, file_name, city, state, grid_efficiency, summer_start_inclusive, winter_start_inclusive,
                 sim_ab_efficiency, efficiency=None):
        """
        Docstring updated on 9/24/22

        This class defines the operating parameters of the Auxiliary Boiler.

        Parameters
        ----------
        efficiency: float
            The efficiency of the boiler when operating at full load expressed
            as a decimal value (ie: 50% = 0.5). Dimensionless
        """
        super().__init__(file_name, city, state, grid_efficiency, summer_start_inclusive, winter_start_inclusive,
                         sim_ab_efficiency)

        # Aux Boiler Specifications
        self.eff = efficiency
