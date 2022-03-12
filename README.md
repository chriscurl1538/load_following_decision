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
system with a micro-cogeneration (mCHP) unit paired with a thermal energy
storage (TES) system, what would the costs, savings, and payback period
be?

To answer that question, this software package needs the operating
parameters of the proposed mCHP system, the building's existing 
boiler, and the proposed (TES) system. Once the user has that 
information, they can enter it into the .yaml file located in the 
package's /input_files folder. This software package also needs 
the energy demand of the building in the form of a .csv file.
The package assumes that the energy demand has been modeled in an 
open source energy modeling software called "eQuest" and exported
as a .csv file. You can find an example of such a file in the 
/input_files folder titled "default_file.csv". The data resolution
is hourly and spans the length of one year for a total of 8760
data points for both the electrical demand of the building and the
heating demand.

So why is the package called "load_following_decision"?

The mCHP system has two dispatch options: it can either operate 
so that the electricity produced by the system matches the 
electrical demand of the building (this is mode is called "electric
load following", or ELF), or operate so that the thermal energy 
produced by the system matches the building’s thermal demands 
(which is called "thermal load following", or TLF). This software 
package is intended to perform an economic analysis of both operating
modes and select the one that is most economically favorable (has
the lowest payback period). Currently, the software only calculates
the payback period for the ELF operating mode.

Further details can be found in /docs/project_motivation.md

### When and why to use this package

This package is designed for my academic research project. I intend
to eventually use this package to examine how the economic 
feasibility of using mCHP systems for mid-rise apartment buildings
varies across the United States.

Eventually this package will be accessible for use by building owners
who are interested in installing an mCHP system in their apartments
and would like to perform a preliminary feasibility assessment 
using this tool. A note for these users: DO NOT make financial
decisions based on these analysis results. Please consult with
a professional before making a final decision on whether an mCHP 
system is right for you.

### Installation Instructions

**Installing from PyPI:**

This project can be installed from PyPI by entering the following 
command in your terminal:

`<Enter Instructions Here>`

**Installing from GitHub:**

If installing from PyPI does not work, this project can also be 
installed from GitHub by entering the following command in your 
terminal:

`pip install git+git://github.com/SoftwareDevEngResearch/load_following_decision.git`

This package is dependent on a number of libraries that you 
will need to install before using this package. Here is a list 
of current known dependencies:

- python>=3.7.4
- pandas>=1.3.5
- numpy>=1.21.5
- PyYAML>=6.0
- pytest>=7.0.1
- tabulate>=0.8.9
- matplotlib>=3.5.1
- pint>=0.18

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
time to add the energy demand .csv file to the /input_files
folder. Here you will find that there is already a .csv file
named "default_file.csv". This has the electricity and thermal
demand for a mid-rise apartment building modeled in eQuest for
your convenience. If you would like to analyze your own hourly 
demand data, export it from eQuest as a .csv and add it to this 
folder.

Next, make a copy of the .yaml template (named "template.yaml")
and change the file name of the copy as you see fit. Fill out 
the new .yaml file with the operating parameters of the mCHP 
and TES units you are interested in analyzing. Also add in the 
operating parameters of the building's existing boiler (please 
note that moving forward the boiler will be referred to as the 
"auxiliary boiler"). For your convenience I have added a 
pre-filled .yaml file called "default_file.yaml" with typical 
operating parameter values.

In addition to the operating parameters of the equipment, the
.yaml file has entries for the cost of fuel and electricity
in your area (these have also been pre-filled in the 
default_file.yaml file). Make sure to convert values to the correct
units as indicated in the template.

Finally, enter the file name of the energy demand .csv file that
you would like to analyze. For example, the default .csv file
name would be entered as `default_file.csv`

Use case examples with step-by-step instructions and expected
results are located in /docs/how_to_guide.md.

### Limitations and Assumptions

This package operates under the following assumptions:

- mCHP Fuel = Natural gas
- Aux Boiler Fuel = Natural gas
- mCHP type = Internal combustion engine
- Building Type = Residential Apartment Building
- TES = Charge and discharge rate is not limited
- TES = Assumes no energy is lost during storage
- Net metering is not accounted for
- Building already has a boiler installed

This package also has the following limitations:

- Energy demand data resolution must be hourly
- Energy demand data must span the course of an entire year
- Weather, location, and building information (square footage, number of floors, etc) must be specified in eQuest when simulating the building's energy demand

### Future Work

Features to be added to this package in the future include:

- Economic analysis for thermal load following (TLF) operating mode
- Calculation of mCHP capacity based on energy demand data
- Calculation of TES capacity based on energy demand data
- Generate results as a pdf file containing relevant tables and plots

### Questions?

For questions regarding this package, please contact:

- Christopher Curl
- email: curlc@oregonstate.edu