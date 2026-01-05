import pandas as pd
import pypsa
import gurobipy

network = pypsa.Network()
network.set_snapshots(range(24))  # Beispiel: 24 Stunden

network.add(
    "Bus", 
    name = "electricity"
)
network.add(
    "Bus",
    name = "heat"
)
# network.add(
#     "Bus",
#     name = "warm_water"
# )

# Definiere das Sonneneinstrahlungsprofil (p_max_pu) für 24 Stunden
solar_potential = [
    0.0, 0.0, 0.0, 0.0, 0.1, 0.5, 1.0, 0.8, 0.6, 0.4, 0.2, 0.1,
    0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0
]

network.add(
    "Generator",
    name="pv_solar",
    bus="electricity",
    p_nom_extendable=True,  # Anzahl der Module bleibt offen
    p_max_pu=solar_potential,  # Zeitabhängiges Sonneneinstrahlungsprofil
    marginal_cost=0.0,  # PV hat keine Brennstoffkosten
    capital_cost=100.0,  # Beispielwert, anpassen nach Bedarf
)
# network.add(
#     "Generator",
#     name="dummy_generator",
#     bus="electricity",
#     p_nom_extendable=True,
#     marginal_cost=1000  # Hohe Kosten, um die Nutzung zu minimieren
# )

# network.add(
#     "Generator",
#     name = "solar_thermal",
#     bus="warm_water",
#     p_nom_extendable=True,
# )


# network.add(
#     "Link",
#     name = "electric_boiler",
#     bus0="electricity",
#     bus1="warm_water",
#     efficiency = efficiency_electric_boiler,
# )

efficiency_heat_pump = 3.5  # Beispielwert, anpassen nach Bedarf
network.add(
    "Link",
    name = "heat_pump",
    bus0="electricity",
    bus1="heat",
    efficiency = efficiency_heat_pump,
    p_nom_extendable = True,
    capital_cost=0.0,  # Beispielwert, anpassen nach Bedarf
)

#TODO: max_hours = 2, was ist das
network.add(
    "StorageUnit",
    overwrite = True,
    name = "battery",
    bus="electricity",
    max_hours = 3, # Speicherdauer in Stunden bei voller Leistung #Beispielwert
    p_nom_extendable = True,
    cyclic_state_of_charge = True, # Der Ladezustand am Ende des Zeitraums ist gleich dem Anfangszustand
    capital_cost=0.0,  # Beispielwert, anpassen nach Bedarf
)
# network.add(
#     "StorageUnit",
#     overwrite = True,
#     name = "thermal_storage",
#     bus="warm_water",
#     max_hours = 6,
#     p_nom_extendable = True,
#     cyclic_state_of_charge = True,
# )

## Load data
network.add(
    "Load",
    name = "electrical_load",
    bus="electricity",
    p_set=[0.5, 0.4, 0.3, 0.3, 0.4, 0.6, 1.2, 2.5, 3.0, 3.5, 4.0, 4.5, 4.8, 4.6, 4.2, 3.8, 3.5, 3.2, 2.8, 2.0, 1.5, 1.0, 0.8, 0.6],  # Beispielwerte
)
network.add(
    "Load",
    name = "heat_load",
    bus="heat",
    p_set=[1.0, 0.8, 0.7, 0.6, 0.8, 1.5, 3.0, 4.5, 5.0, 4.8, 4.2, 3.8, 3.5, 3.2, 3.0, 3.5, 4.0, 4.8, 5.5, 4.0, 3.0, 2.0, 1.5, 1.2],
)

# network.add(
#     "Load",
#     name = "warm_water_load",
#     bus="warm_water",
#     p_set=data['WW-Ladung [MWh]'],
# )

network.optimize(solver_name="gurobi")
print(network.generators.p_nom_opt)
print(network.storage_units.p_nom_opt)