import pytest


@pytest.fixture
def class_info():
    import pathlib, yaml, numpy as np
    from lfd_package.modules import classes

    try:
        from yaml import CLoader as Loader
    except ImportError:
        from yaml import Loader

    yaml_filename = 'default_file.yaml'  # these match the "dest": dest="input"
    cwd = pathlib.Path(__file__).parent.parent.resolve() / 'input_files'

    with open(cwd / yaml_filename) as f:
        data = yaml.load(f, Loader=Loader)
    f.close()

    part_load_electrical_list = []
    part_load_thermal_list = []
    for i in range(50, 125, 25):
        part_load_electrical_list.append([i, data['Electrical'][i]])
        part_load_thermal_list.append([i, data['Thermal'][i]])
    part_load_electrical_array = np.array(part_load_electrical_list)
    part_load_thermal_array = np.array(part_load_thermal_list)

    # Class initialization using CLI arguments
    chp = classes.CHP(capacity=data['chp_cap'], fuel_type=data['fuel_type'], fuel_input_rate=data['fuel_input_rate'],
                      turn_down_ratio=data['chp_turn_down'], part_load_electrical=part_load_electrical_array,
                      part_load_thermal=part_load_thermal_array, chp_electric_eff=data['Electrical']['100'],
                      chp_thermal_eff=data['Thermal']['100'], percent_availability=data['percent_availability'],
                      cost=data['chp_installed_cost'])
    ab = classes.AuxBoiler(capacity=data['ab_capacity'], efficiency=data['ab_eff'],
                           turn_down_ratio=data['ab_turn_down'])
    demand = classes.EnergyDemand(file_name=data['demand_filename'], net_metering_status=data['net_metering_status'],
                                  grid_efficiency=data['grid_efficiency'],
                                  electric_cost=data['electric_utility_cost'],
                                  fuel_cost=data['fuel_cost'])
    tes = classes.TES(capacity=data['tes_cap'], start=data['tes_init'], discharge=data['tes_discharge_rate'],
                      cost=data['tes_installed_cost'])

    return [demand, chp, tes, ab]


# @pytest.fixture
# def chp_pl():
#     import numpy as np
#
#     # TODO: UPDATE
#     part_load_list = [
#         [30, 0.344],
#         [40, 0.379],
#         [50, 0.407],
#         [60, 0.420],
#         [70, 0.427],
#         [80, 0.437],
#         [90, 0.449],
#         [100, 0.457]
#     ]
#     part_load_array = np.array(part_load_list)
#     return part_load_array
