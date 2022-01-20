"""
Calculates the optimal load dispatch for a CHP system
 Assumptions:
 Fuel = NG
 Prime Mover = ICE
 Building = Mid-rise Apartment, 50 units, 700 scf each
 Other Equipment = Aux Boiler, TES
"""

# Parameters - Fixed Independent Variables
"""
Input file - Hourly Electricity Demand
Input file - Hourly Thermal Demand

[AB_cap] Aux Boiler Capacity
[AB_turn] Aux Boiler Turndown Ratio
[AB_eff] Aux Boiler Efficiency
[CHP_cap] mCHP Electrical Capacity
[CHP_turn] mCHP Turndown Ratio
[CHP_eff_el] mCHP Electrical Efficiency
[CHP_eff_th] mCHP Thermal Efficiency
[CHP_part_load] mCHP part load efficiency profile (can this be calculated?)
[CHP_hp_ratio] mCHP heat:power ratio
[NG_hhv] Fuel HHV

Example of mCHP system: neoTower 50.0 HT https://www.rmbenergie.com/en/products/
Fuel HHV values: https://www.engineeringtoolbox.com/fuels-higher-calorific-values-d_169.html
"""

# Decision Variables - Independent Variables to be Optimized
"""
Aux Boiler Hourly Output
mCHP Hourly Electrical Output
mCHP Hourly Thermal Output
"""

# Dependent Variables - Calculated from Independent Variables
"""
[AB_min] Aux Boiler Min Heat Output
    From turndown ratio
[NG_use] Fuel Use
    From Aux Boiler efficiency, mCHP efficiency, mCHP heat:power ratio, fuel HHV, Hourly Thermal Demand
[WH] Heat Wasted
[WP] Electricity Wasted
"""

if __name__ == '__main__':
    print("executed")
