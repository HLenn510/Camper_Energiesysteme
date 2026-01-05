#import pandas as pd
import pypsa
import matplotlib.pyplot as plt

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


network.optimize(solver_name="gurobi")
print(network.generators.p_nom_opt)
print(network.storage_units.p_nom_opt)

# Daten aus dem optimierten Netzwerk extrahieren
hours = network.snapshots
load = network.loads_t.p.loc[:, network.loads.bus == "electricity"].sum(axis=1)  # Nur elektrische Last
solar = network.generators_t.p.loc[:, "pv_solar"]  # Solarleistung
storage = network.storage_units_t.p.loc[:, "battery"]  # Speicherleistung

# Daten für Wärme-Last und Wärmepumpe extrahieren
#heat_load = network.loads_t.p.loc[:, network.loads.bus == "heat"].sum(axis=1)  # Nur Wärme-Last
heat_pump = network.links_t.p0.loc[:, "heat_pump"]  # Leistung der Wärmepumpe

# Kombinierter Plot für Wärme-Last und Wärmepumpe
plt.figure(figsize=(10, 6))
plt.plot(hours, load, label="Stromlast", color="blue")
plt.plot(hours, solar, label="Solarleistung (p_nom)", color="orange")
plt.plot(hours, storage, label="Speicherleistung (p_nom)", color="green")
#plt.plot(hours, heat_load, label="Wärmelast", color="red")
plt.plot(hours, heat_pump, label="Wärmepumpe (Leistung)", color="purple")

# Achsenbeschriftungen und Titel
plt.xlabel("Stunden des Tages")
plt.ylabel("Leistung (kWh)")
plt.title("Optimiertes Netzwerk: Lasten und Leistungen")
plt.legend()
plt.grid()

# Plot anzeigen
plt.show()