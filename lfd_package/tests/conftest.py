import pytest


@pytest.fixture
def class_info():
    import pathlib, yaml, numpy as np
    from lfd_package import classes

    try:
        from yaml import CLoader as Loader
    except ImportError:
        from yaml import Loader

    yaml_filename = 'default_file.yaml'  # these match the "dest": dest="input"
    cwd = pathlib.Path(__file__).parent.parent.resolve() / 'input_files'

    with open(cwd / yaml_filename) as f:
        data = yaml.load(f, Loader=Loader)
    f.close()

    part_load_list = []
    for i in range(30, 110, 10):
        part_load_list.append([i, data[i]])
    part_load_array = np.array(part_load_list)

    # Class initialization using CLI arguments
    chp = classes.CHP(capacity=data['chp_cap'], heat_power=data['chp_heat_power'],
                      turn_down_ratio=data['chp_turn_down'],
                      part_load=part_load_array, cost=data['chp_installed_cost'])
    ab = classes.AuxBoiler(capacity=data['ab_capacity'], efficiency=data['ab_eff'],
                           turn_down_ratio=data['ab_turn_down'])
    demand = classes.EnergyDemand(file_name=data['demand_filename'], electric_cost=data['electric_utility_cost'],
                                  fuel_cost=data['fuel_cost'])
    tes = classes.TES(capacity=data['tes_cap'], cost=data['tes_installed_cost'])

    return [chp, ab, demand, tes]


@pytest.fixture
def chp_pl():
    import numpy as np

    part_load_list = [
        [30, 0.344],
        [40, 0.379],
        [50, 0.407],
        [60, 0.420],
        [70, 0.427],
        [80, 0.437],
        [90, 0.449],
        [100, 0.457]
    ]
    part_load_array = np.array(part_load_list)
    return part_load_array
