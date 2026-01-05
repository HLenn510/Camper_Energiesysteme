import pandas as pd
import pypsa


network = pypsa.Network()
network.set_snapshots(range(8784))

network.add(
    "Bus", 
    name = "electricity"
)
network.add(
    "Bus",
    name = "heat"
)
network.add(
    "Bus",
    name = "warm_water"
)

network.add(
    "Generator",
    name = "pv_solar",
    bus="electricity",
    p_nom_extendable=True,
)
network.add(
    "Generator",
    name = "solar_thermal",
    bus="warm_water",
    p_nom_extendable=True,
)

#TODO: efficiency values
network.add(
    "Link",
    name = "electric_boiler",
    bus0="electricity",
    bus1="warm_water",
    efficiency = efficiency_electric_boiler,
)

network.add(
    "Link",
    name = "heat_pump",
    bus0="electricity",
    bus1="heat",
    efficiency = efficiency_heat_pump,
)

#TODO: max_hours = 2, was ist das
network.add(
    "StorageUnit",
    overwrite = True,
    name = "battery",
    bus="electricity",
    max_hours = 2,
    p_nom_extendable = True,
    cyclic_state_of_charge = True,
)
network.add(
    "StorageUnit",
    overwrite = True,
    name = "thermal_storage",
    bus="warm_water",
    max_hours = 6,
    p_nom_extendable = True,
    cyclic_state_of_charge = True,
)

## Load data
network.add(
    "Load",
    name = "electrical_load",
    bus="electricity",
    p_set=data['Netzlast [MWh]'],
)
network.add(
    "Load",
    name = "heat_load",
    bus="heat",
    p_set=data['Wärmelast [MWh]'],
)

network.optimize(solver_name = 'gurobi')
network.generators.p_nom_opt