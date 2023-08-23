import pytest


@pytest.fixture
def class_info():
    import pathlib, yaml
    from lfd_package.modules import classes

    try:
        from yaml import CLoader as Loader
    except ImportError:
        from yaml import Loader

    yaml_filename = 'seattle_wa.yaml'  # these match the "dest": dest="input"
    cwd = pathlib.Path(__file__).parent.parent.resolve() / 'input_yaml'

    with open(cwd / yaml_filename) as f:
        data = yaml.load(f, Loader=Loader)
    f.close()

    # Class initialization using CLI arguments
    demand = classes.EnergyDemand(file_name=data['demand_filename'], city=data['city'], state=data['state'],
                                  grid_efficiency=data['grid_efficiency'], sim_ab_efficiency=data["energy_plus_eff"],
                                  winter_start_inclusive=data['winter_start_inclusive'],
                                  summer_start_inclusive=data['summer_start_inclusive'])
    emissions_class = classes.Emissions(file_name=data['demand_filename'], city=data['city'], state=data['state'],
                                        grid_efficiency=data['grid_efficiency'],
                                        sim_ab_efficiency=data["energy_plus_eff"],
                                        summer_start_inclusive=data['summer_start_inclusive'],
                                        winter_start_inclusive=data['winter_start_inclusive'])
    costs_class = classes.EnergyCosts(file_name=data['demand_filename'], city=data['city'], state=data['state'],
                                      grid_efficiency=data['grid_efficiency'], no_apts=data['no_apts'],
                                      winter_start_inclusive=data['winter_start_inclusive'],
                                      summer_start_inclusive=data['summer_start_inclusive'],
                                      sim_ab_efficiency=data["energy_plus_eff"], meter_type_el=data['meter_type_el'],
                                      meter_type_fuel=data['meter_type_fuel'],
                                      schedule_type_el=data['schedule_type_el'],
                                      schedule_type_fuel=data['schedule_type_fuel'],
                                      master_metered_el=data['master_metered_el'],
                                      single_metered_el=data['single_metered_el'],
                                      master_metered_fuel=data['master_metered_fuel'],
                                      single_metered_fuel=data['single_metered_fuel'])
    chp = classes.CHP(file_name=data['demand_filename'], city=data['city'], state=data['state'],
                      grid_efficiency=data['grid_efficiency'], sim_ab_efficiency=data["energy_plus_eff"],
                      summer_start_inclusive=data['summer_start_inclusive'],
                      winter_start_inclusive=data['winter_start_inclusive'], turn_down_ratio=data['chp_turn_down'],
                      chp_installed_cost=data['chp_installed_cost'], chp_om_cost=data['chp_om_cost'])
    ab = classes.AuxBoiler(file_name=data['demand_filename'], city=data['city'], state=data['state'],
                           grid_efficiency=data['grid_efficiency'],
                           summer_start_inclusive=data['summer_start_inclusive'],
                           winter_start_inclusive=data['winter_start_inclusive'],
                           sim_ab_efficiency=data["energy_plus_eff"], efficiency=data['ab_eff'])
    tes = classes.TES(file_name=data['demand_filename'], city=data['city'], state=data['state'],
                      grid_efficiency=data['grid_efficiency'], sim_ab_efficiency=data["energy_plus_eff"],
                      summer_start_inclusive=data['summer_start_inclusive'], start=data['tes_init'],
                      winter_start_inclusive=data['winter_start_inclusive'], energy_density=data['tes_energy_density'],
                      tes_installed_cost=data['tes_installed_cost'], tes_om_cost=data['tes_om_cost'])

    class_dict = {
        "demand": demand,
        "emissions": emissions_class,
        "costs": costs_class,
        "chp": chp,
        "ab": ab,
        "tes": tes
    }

    return class_dict
