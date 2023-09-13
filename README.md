## Software Package: load_following_decision

### Welcome to the load_following_decision README file! 

This file will give a brief explanation of what this package does, 
when and why you should use it, how to install it, and basic 
guidelines for getting started. It will also delve into the 
limitations of this package and explain the assumptions this 
project is built on. Finally, we will delve into future work, 
aka the functionality I plan to add to this software in the 
future.

### First, a brief note on nomenclature

In this package the following terms are used interchangeably:

- Heating demand, thermal demand, heating load, thermal load
- Energy demand, load profile

### Overview: What this package does

In simple terms, this package answers the following question: if
an apartment building owner replaces their conventional energy
system with a small-scale (under 100 kWe) cogeneration (CHP) unit paired 
with a thermal energy storage (TES) system, what would the emissions, 
costs, savings, and payback period be?

To answer that question, this software package needs the operating
parameters of the proposed CHP system, the building's existing 
boiler, and the proposed TES system. Once the user has that 
information, they can enter it into the .yaml file located in the 
package's /input_yaml folder. The .yaml file also has keys for entering 
the electricity and natural gas rate schedules for the location being 
analyzed. This software package also needs 
the energy demand of the building in the form of a .csv file.
The package assumes that the energy demand has been modeled in an 
open source energy modeling software called "EnergyPlus" and exported
as a .csv file. You can find examples of such a file in the 
/input_demand_profiles folder. The data resolution
is hourly and spans the length of one year for a total of 8760
data points for both the electrical demand of the building and the
heating demand.

So why is the package called "load_following_decision"?

The CHP system has three dispatch options: it can either operate 
so that the electricity produced by the system matches the 
electrical demand of the building (this is mode is called "electric
load following", or ELF), operate so that the thermal energy 
produced by the system matches the building’s thermal demands 
(which is called "thermal load following", or TLF), or operate such 
that energy is contantly produced at full capacity (this mode is called 
"power purchase", or PP, since it maximizes electricity buyback revenue). 
This software package is intended to perform an emissions analyssi and 
an economic analysis of all three operating modes to reveal which modes 
are most economically and environmentally favorable.

Further details can be found in /docs/LFD_user_manual.pdf

### When and why to use this package

This package was originally created as part of my Master's Thesis in
Mechanical Engineering. The intended users for this package consist of 
academic researchers investigating small-scale (under 100 kWe) CHP systems.
Files are available for analyzing mid-rise apartment buildings in seven 
climate zones across the US, with demand profiles available for eight 
building constructions (ASHRAE 90.1 building standards).

Disclaimer: DO NOT make financial
decisions based on these analysis results. Please consult with
a professional before making a final decision on whether a CHP 
system is right for you.

### Installation Instructions

**Installing from GitHub:**

This project can be installed from GitHub by entering the following command in your 
terminal:

`pip install git+git://github.com/SoftwareDevEngResearch/load_following_decision.git`

This package is dependent on a number of libraries that you 
will need to install before using this package. Here is a list 
of current known dependencies:

- python>=3.7.4
- pandas>=1.3.5
- numpy>=1.21.5
- PyYAML>=6.0
- matplotlib>=3.5.1
- pint>=0.18
- openpyxl>=3.1.2

From your terminal, you can install these dependencies manually 
with the following command:

`pip install package_name`

For example, to install the pandas package, enter the following 
command:

`pip install pandas>=1.3.5`

Use `pip freeze` to double-check that the correct version of each
dependency is installed.

### Getting Started

Once the package and its dependencies have been installed, it is
time to add the energy demand .csv file to the /input_demand_profiles
folder. If you would like to analyze your own hourly 
demand data, export it from EnergyPlus as a .csv and add it to this 
folder.

Next, make a copy of the .yaml template (named "template.yaml")
and change the file name of the copy as you see fit. Fill out 
the new .yaml file with the operating parameters of the CHP 
and TES units you are interested in analyzing. Also add in the 
operating parameters of the building's existing boiler (please 
note that moving forward the boiler will be referred to as the 
"auxiliary boiler"). 

In addition to the operating parameters of the equipment, the
.yaml file has entries for the cost of fuel and electricity
in your area (these have been pre-filled with 2023 data in the
pre-existing filled .yaml files for the seven locations assessed
in my research). Make sure to convert values to the correct
units as indicated in the template before entering them.

Finally, enter the file name of the energy demand .csv file that
you would like to analyze. For example, a file named "default_file" 
would be entered as `default_file.csv`

Use case examples with step-by-step instructions and expected
results are located in /docs/LFD_user_manual.pdf.

### Limitations and Assumptions

This package operates under the following assumptions:

- CHP Fuel = Natural gas
- Aux Boiler Fuel = Natural gas
- CHP Prime Mover = Reciprocating Engine
- Building Type = Mid-rise Multi-family Building
- TES = Power rating (Btu/hr) is unrestricted
- TES = Assumes no energy is lost during storage
- Building already has a boiler installed
- Aux Boiler = No restrictions on turn-down
- Power rating is assumed to be equal to peak thermal demand
- The electricity buyback rate is equal to the price paid by the consumer

This package also has the following limitations:

- Energy demand data resolution must be hourly
- Energy demand data must span the course of one year
- Weather, location, and building information (square footage, number of floors, etc.) must be specified in EnergyPlus when simulating the building's energy demand

Additional assumptions and limitations are described in /docs/LFD_user_manual.pdf

### Future Work

The package currently does not have a testing suite for unit testing. This oversight 
will be rectified in the next software update. Until then, a data_validation.xlsx file
has been included in the /docs folder for confirming that results output values are as 
expected. Calculations were re-created in Excel in the first sheet, and Python calculation
outputs for Fairbanks, AK (2019 construction) were included in the second sheet.

### Questions?

For questions regarding this package, please contact:

- Christopher Curl
- email: christopher.r.curl@gmail.com