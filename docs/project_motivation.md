## Micro-Cogeneration Load Dispatch Assessment

**Background**: The objective of my research is to understand the techno-economic factors that influence the success of residential micro-combined heat and power (mCHP) applications (< 50 kWe) in the United States. The US has relatively low numbers of residential mCHP installations compared to other countries, and no existing literature investigates the technical and economic reasons for this discrepancy. This project is my first step towards developing a tool that will assess the technical and economic feasibility of using mCHP for meeting the electrical and thermal needs of mid-rise apartment buildings in the United States.

**Software Project Overview**:  This project is intended for use by researchers and apartment building owners who are interested in an mCHP system but are not sure if it would be appropriate for their needs. The software imports the annual electrical demand and thermal demand data for a simulated apartment building. Using this data, the software calculates the electrical and thermal load dispatch of an mCHP system paired with an auxiliary boiler and thermal energy storage system (TES). The mCHP system has two dispatch options: operate so that the electricity produced by the system matches the electrical demand of the building (electric load following), or operate so that the thermal energy produced by the system matches the building’s thermal demands (thermal load following). This software package calculates the operating costs of both and chooses the operating schedule that is most favorable.

Note that for the purpose of this project, the mCHP system is assumed to be a natural gas reciprocating engine.

The expected inputs of the program include:

- Electrical and heating demand of the building (csv file)

- Whether local policies allow the owner to sell excess electricity to its utility provider

- The size, turndown ratio, heat to power ratio, and part-load efficiencies of the mCHP system

- The size, efficiency, and turndown ratio of the auxiliary boiler

- The size of the TES system and expected thermal energy loss during storage

- The cost of natural gas in $/gal

- The cost of electricity in $/kWh

- The price of electricity sold back to the utility (if applicable)

- Capital costs of equipment

The expected outputs of the program include:

- Total costs and revenues for both electrical load following and thermal load following modes

- Graphs depicting the energy dispatched by each piece of equipment for both operating modes

- Which operation mode is most economically favorable

When deciding which operating mode is most cost-effective, the program will use the following logic. For the electrical load following mode, if the electrical demand is below the minimum operating capacity (indicated by the turndown ratio) then the owner will buy electricity from the local utility company. If the electrical demand is above the maximum operating capacity, then the owner will buy electricity from the local utility company to make up the difference. Any excess thermal energy produced by the mCHP system will be stored in the TES system. If in the course of meeting electricity demand the thermal energy produced is insufficient to meet demand, the TES system will dispatch stored thermal energy to fill the gap. If the TES system has insufficient energy for this, then the auxiliary boiler will fill the gap.

For the thermal load following mode, if the thermal demand falls below the minimum operating capacity, then the TES system will dispatch stored thermal energy to meet demand. If the TES system has insufficient energy for this, then the auxiliary boiler will fill the gap. If the thermal demand exceeds the mCHP maximum operating capacity, then the TES system will dispatch stored thermal energy to meet demand. If the TES system has insufficient energy for this, then the auxiliary boiler will fill the gap. If electricity needs are higher than what the system is producing, then electricity will be bought from the local utility. If electricity needs are lower than what the system is producing, then the building owner will sell excess electricity to the local utility (if local policies allow it).

**Existing Methodology and Prior Work**: Current literature discusses methods such as multi-integer optimization to find a happy medium between low-cost, low-emission, and energy-saving load dispatch schedules for mCHP systems [1]. Electrical load following and thermal load following schedules are typical in industrial and commercial scale applications since demand fluctuations are not significant. Residential scale applications have comparatively large demand fluctuations which means load-following strategies result in poorer performance. However, coupling mCHP with TES or battery storage has been shown to improve performance [1-4]. I have chosen the simpler load-following dispatch methods since load dispatch optimization is not the focus of my research.This limitation of my research will need to be addressed in future work.

This software package may not be significantly different from existing packages functionally, but I have not encountered literature where the software package is free to use and the code is open source. For example, Onovwiona et al created a parametric model that can be used in the design and techno-economic evaluation of internal combustion engine (ICE) based cogeneration systems for residential use [5]. It provides information about the system’s performance in response to changing thermal and electrical demands. While the ESP-r modeling program is open source, the author gives no way to access the model created for this analysis.

**Package dependency**: My software will depend on the following packages, though other packages may be added to this list during the course of development:

- Pandas
- Numpy
- Yaml
- Pint

### References

[1] P. K. Cheekatamarla and F. Nocera, “Decarbonization of Residential Building Energy Supply: Impact of Cogeneration System Performance on Energy, Environment, and Economics †,” 2021, doi: 10.3390/en14092538.

[2] A. Rosato, S. Sibilio, and G. Ciampi, “Energy, environmental and economic dynamic performance assessment of different micro-cogeneration systems in a residential application,” Appl. Therm. Eng., vol. 59, no. 1–2, pp. 599–617, 2013, doi: 10.1016/j.applthermaleng.2013.06.022.

[3] M. Bianchi, A. De Pascale, and F. Melino, “Performance analysis of an integrated CHP system with thermal and Electric Energy Storage for residential application,” Appl. Energy, vol. 112, pp. 928–938, Dec. 2013, doi: 10.1016/j.apenergy.2013.01.088.

[4] F. TeymouriHamzehkolaei and S. Sattari, “Technical and economic feasibility study of using Micro CHP in the different climate zones of Iran,” Energy, vol. 36, no. 8, pp. 4790–4798, 2011, doi: 10.1016/j.energy.2011.05.013.

[5] H. I. Onovwiona, V. Ismet Ugursal, and A. S. Fung, “Modeling of internal combustion engine based cogeneration systems for residential applications,” Appl. Therm. Eng., vol. 27, no. 5–6, pp. 848–861, 2007, doi: 10.1016/j.applthermaleng.2006.09.014.