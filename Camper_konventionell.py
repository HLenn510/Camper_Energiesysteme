import pypsa
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

#Ort setzen wo nach einer Dateil gesucht werden soll
import os
os.chdir(r"C:\Users\avick\.spyder-py3\Pypsa\Übungscodes\ÜBbung 3")


loads_pv_temp_hourly = pd.read_csv("Temp_loads_pv_hourly_utf_8.csv", sep= ";", decimal = ",")

electrical_load = loads_pv_temp_hourly["Elektrische_Last [kW]"] * 0.25   #mal 0,25 aufgrund fehlender Umrechnung in der Userstory
warmwasser_load = loads_pv_temp_hourly["Warmwasser_Last [kW]"]
outside_temperature = loads_pv_temp_hourly[" Außentemperatur [ºC]"] 
pv_p_nom_pu = loads_pv_temp_hourly["PV_Erzeugung [kW]"]
heating_load_e_van = loads_pv_temp_hourly["Wärme_Last_elektrisch 23°C [kW]"]
cooling_load_e_van = loads_pv_temp_hourly["Kühl_Last_elektrisch 23°C [kW]"]


network_2 = pypsa.Network()
network_2.set_snapshots(loads_pv_temp_hourly.index)

#Busse hinzufügen
network_2.add("Bus", name = "electricity")
network_2.add("Bus", name = "thermal")
network_2.add("Bus", name = "thermal_heating")
network_2.add("Bus", name = "thermal_cooling")
network_2.add("Bus", name = "hot_water")
network_2.add("Bus", name = "diesel")

#Lasten hinzufügen
network_2.add("Load", name = "electrical_load", bus = "electricity" ,p_set = electrical_load )
network_2.add("Load", name = "hot_water_load", bus = "hot_water", p_set = warmwasser_load)
network_2.add("Load", name = "thermal_heating_load", bus = "thermal_heating", p_set = heating_load_e_van)
network_2.add("Load", name = "thermal_cooling_load", bus = "thermal_cooling", p_set = cooling_load_e_van)

#Funktion zur Berechnung von Annuity mitdefault 3% Zins, n steht für Jahre, capex für Investitionskosten
def annuity(invest, t, r = 0.03):
    return invest * (r * (1 + r) ** t) / ((1 + r) ** t - 1)

#COP Kühlen und Heizen 
#Annahme verhält sich ähnlich wie Viessman 151-A04, 230V~
#Annhame betreiben bei 45 Grad heizen,  Seite 31
temp_heating = [-20, -15, -7, -2, 7, 10, 20, 30 ,35]
el_power_heating = [1.33, 1.39, 1.46, 0.77, 1.02, 1.01, 0.98, 0.92, 0.88]
cop_heating = [1.82, 2.06, 2.52, 3.12, 3.67, 4.05, 5.65, 8.09, 8.70]
hp_p_nom_heating = 0.8 # A7/W35 

#Betreiben bei W 7,   Seite 32
temp_cooling = [20, 25, 27, 30, 35, 40, 45]
el_power_cooling = [0.65, 0.73, 0.76, 0.81, 0.90, 0.97, 0.98]
eer_cooling = [5.4, 4.4, 4.1, 3.6, 2.9, 2.3, 1.8]
hp_p_nom_cooling = 0.85 #A35/W18




df_data = pd.DataFrame(columns= ["eer_cooling", "cop_heating", "el_p_pu_cooling", "el_p_pu_heating"])

df_data["eer_cooling"] = np.interp(outside_temperature , temp_cooling, eer_cooling)
df_data["el_p_pu_cooling"] = np.interp(outside_temperature , temp_cooling, el_power_cooling)/hp_p_nom_cooling

df_data["cop_heating"] = np.interp(outside_temperature, temp_heating, cop_heating)
df_data["el_p_pu_heating"] = np.interp(outside_temperature, temp_heating, el_power_heating)/hp_p_nom_heating


########################### LiTime 12V 200Ah Plus Deep Cycle LiFePO4 Lithium Batterie – 200A BMS ###########################
capacity_kwh_battery = 2.4  # Kapazität in kWh
p_nom_kw_battery = 2.4  # Nennleistung in kW
capex_euro_battery = 469.99 # Investitionskosten in Euro
capex_euro_battery_per_kwh = capex_euro_battery / capacity_kwh_battery  # Investitionskosten in Euro
lifetime_years_battery = 10  # Lebensdauer in Jahren
charging_efficiency_battery = 0.95  # Wirkungsgrad (95%)
discharge_efficiency_battery = 0.95  # Entladewirkungsgrad (95%)
network_2.add("StorageUnit",
    name = "batteriespeicher",
    bus="electricity",

    # Technische Daten
    p_nom_extendable = True,
    p_nom = p_nom_kw_battery,           # 2.4 kW (fest)
    max_hours= capacity_kwh_battery / p_nom_kw_battery, # 1 Stunde (ergibt 2.4 kWh)

    # Wirtschaftliche Daten (Annualisiert)
    capital_cost = annuity(capex_euro_battery_per_kwh * capacity_kwh_battery, lifetime_years_battery), # Beispiel: 3.000€ Investition über 10 Jahre
    lifetime = lifetime_years_battery,
    
    # Effizienz & Verhalten
    efficiency_store = charging_efficiency_battery,    # AC-Laden
    efficiency_dispatch = discharge_efficiency_battery, # Entladen
    cyclic_state_of_charge = True,
    active = True,
    
    overwrite = True
)

########################### Diesel Generator / Van
capital_cost_sprinter_price = 50235.14
lifetime_Sprinter = 20
capital_cost_sprinter = annuity (capital_cost_sprinter_price, lifetime_Sprinter)

#Dieselkosten
diesel_energy_density = 9.8
diesel_price_per_liter = 1.70
diesel_marginal_cost = diesel_price_per_liter  # Euro/Liter

#output dieses Generators ist Diesel --> Umwandlung erst bei den Links
network_2.add("Generator",
    name= "diesel_supply",
    bus="diesel",
    p_nom_extendable = True,
    marginal_cost = diesel_marginal_cost, # Preis Euro/kWh
    capital_cost = 0,
)

########################### Diesel Notsrom aggregat
#Piccolo 5 Diesel Generator

#Annahme nie im leerlauf, wird ausgeschaltet und eingechaltet nach bedarf
p_nom_diesel_generator = 3.5 #kW bei Dauerbetrieb und Spitzenleistung
#Verbrauch im bei 3600 Watt elektrisch 0,8 bis 1,21 Liter pro Stunde
#Größere Geneartoren haben auch einen ähnlichen Verbrauch
lifetime_diesel_generator = 20
capex_diesel_generator = 8300 #Euro
annuity_diesel_generator = annuity(capex_diesel_generator / p_nom_diesel_generator , lifetime_diesel_generator)


network_2.add(
    "Link",
    name = "diesel_generator",
    bus0 = "diesel", 
    bus1 = "electricity",         
    p_nom_extendable = True, 
    efficiency = 0.35 ,      # 30% Wirkungsgrad bei Teillast und 37 % Wirkungsgrad bei Volllast
    capital_cost = annuity_diesel_generator, 
    lifetime = lifetime_diesel_generator
)

########################### Diesel Kombi Heizung

#Kombidieselheizung - Aqua-Hot Gen1 D4E Diesel
capital_cost_kombi_heater = 1795
lifetime_kombi_heater = 10
capital_cost_kombi_heater_annuity = annuity(capital_cost_kombi_heater, lifetime_kombi_heater)
p_kombi_heater = 4.0
efficiency_kombi_heater = 0.629    #0.63 zu 0.629 elektrische verluste
#efficiency2_kombi_heater= -0.012 #durch elektrische Verluste

network_2.add(
    "Link",
    name = "dieselheizung",
    bus0 = "diesel",
    bus1 = "thermal",
    p_nom_extendable = True,
    efficiency = efficiency_kombi_heater,
    capital_cost = capital_cost_kombi_heater_annuity,
    marginal_cost = 0
    )

########################### Leitung von thermal zu hot water
network_2.add(
    "Link",
    name = "warmwater",
    bus0 = "thermal", 
    bus1 = "hot_water",          # Ausgang: Wärme umgerechnet in kW
    p_nom_extendable = True,      # Solver legt größe fest --> Rohrleitung
    efficiency = 1,           #sehr gute Wärmedämmung keine Verluste
    capital_cost = 0, 
    marginal_cost =0    
)  

########################### "Leitung" von thermal zum Camperinneren
network_2.add(
    "Link",
    name = "heating",
    bus0 = "thermal", 
    bus1 = "thermal_heating",          # Ausgang: Wärme (Dein Heat-Bus)
    p_nom_extendable = True,        # Solver legt größe fest --> Rohrleitung
    efficiency= 1,      # 
    capital_cost= 0, 
    marginal_cost=0    
)  

########################### Wärmepumpe_kühlen (Camper, variabler EER, extendable) ###########################
capex_euro_heatpump = 2699.0  # Investitionskosten in Euro von Dometic.com  Dometic Freshjet FJX7 2200
lifetime_years_heatpump = 10  # Lebensdauer in Jahren
p_nom_kw_heatpump_el = 1.05  # Elektrische Nennleistung in kW (Richtwert)
capex_euro_heatpump_per_kw = capex_euro_heatpump / p_nom_kw_heatpump_el
# Beispiel: Dometic FreshJet 2200 
network_2.add("Link",
    name = "waermepumpe_cooling",
    bus0="electricity",
    bus1="thermal_cooling",

    # Technische Daten
    p_nom_extendable=True,
    p_max_pu = df_data["el_p_pu_cooling"],  #elektrische Leistungs begrenzung aufgrund der Außentemperatur
    efficiency = df_data["eer_cooling"],    # EER
    capital_cost = annuity(capex_euro_heatpump_per_kw, lifetime_years_heatpump),
)

########################### Warmwasserspeicher (Camper) ###########################
#Beispiel: 30 Liter Warmwasserseicher für Camper
capacity_kwh_hot_water_storage = 0.0349  # Kapazität in kWh (30L * 4.18 kJ/kg/K * 40K / 3600)
p_nom_kw_hot_water_storage = 2.0  # Nennleistung in kW (Be- und Entladerate)
capex_euro_hot_water_storage = 300.0  # Investitionskosten in Euro (Richtwert)
capex_euro_hot_water_storage_per_kwh = capex_euro_hot_water_storage / capacity_kwh_hot_water_storage  # €/kWh
lifetime_years_hot_water_storage = 15  # Lebensdauer in Jahren
standing_loss_hot_water_storage = 0.02  # Wärmeverlust (2% pro Stunde)
network_2.add("StorageUnit",
    name = "warmwasserspeicher",
    bus="hot_water",

    # Technische Daten
    p_nom_extendable = True,
    max_hours = (1/12),  # Annahme ein Duschvorgang pro Stunde maximal --> 5 Minuten in Stunden = 1/12

    # Wirtschaftliche Daten (Annualisiert)
    capital_cost = annuity(capex_euro_hot_water_storage_per_kwh * capacity_kwh_hot_water_storage, lifetime_years_hot_water_storage),
    lifetime = lifetime_years_hot_water_storage,
    
    # Effizienz & Verhalten
    efficiency_store = 1.0,  # Speichern ohne Verluste
    efficiency_dispatch = 1.0,  # Entladen ohne Verluste
    standing_loss = standing_loss_hot_water_storage,  # Wärmeverlust
    cyclic_state_of_charge = True,
)


network_2.optimize(solver_name = "gurobi", threads = 1, method = 2)
network_2.loads_t.p.plot()
network_2.generators_t.p.plot()
#diesel_supply

#Ergebnisse ausgeben Netzwerk 2
invest_cost_storage_units_2 = (network_2.storage_units.p_nom_opt * network_2.storage_units.capital_cost)
invest_cost_generators_2 = network_2.generators.p_nom_opt * network_2.generators.capital_cost 
invest_cost_links_2 = network_2.links.p_nom_opt * network_2.links.capital_cost
df_invest_cost_2_annuity = pd.concat([invest_cost_storage_units_2, invest_cost_generators_2, invest_cost_links_2])
invest_cost_2 = round(df_invest_cost_2_annuity.sum() ,2)

df_invest_cost_2_annuity.loc["Sprinter"] = capital_cost_sprinter
#operatiosnkosten
operational_cost_2 = round(( network_2.generators_t.p.sum() * network_2.generators.marginal_cost).sum(),2)


###############################Annuitätsberechnungen für die Ausauschgeräte damit ein Zeitrau von 20 Jahren betrachtet werden kann
#Inflation bei 3% über 10 Jahre
inflation_factor = 1.03**10

###############################Kaufpreise in 10 jahren

#Batterie
#Kaufpreis nach Ablauf der Lifetime
exchange_battery_small_in_future = inflation_factor * capex_euro_battery
#Annuität des Kaufpreises nach Ablauf der Lifetime über die nächste Lifetime
annuity_exchange_battery_small_in_future = annuity(exchange_battery_small_in_future * network_2.storage_units.p_nom_opt.batteriespeicher , lifetime_years_battery)


#WP
#Kaufpreis nach Ablauf der Lifetime
exchange_wp_in_future = inflation_factor * capex_euro_heatpump
#Annuität des Kaufpreises nach Ablauf der Lifetime über die nächste Lifetime
annuity_exchange_wp_in_future = annuity( exchange_wp_in_future * network_2.links.p_nom_opt.waermepumpe_cooling , lifetime_years_heatpump )

#Warmwasserspeicher
#Kaufpreis nach Ablauf der Lifetime
exchange_hot_water_storage_in_future = inflation_factor * capex_euro_hot_water_storage
#Annuität des Kaufpreises nach Ablauf der Lifetime über die nächste Lifetime
annuity_exchange_hot_water_storage_in_future = annuity(exchange_hot_water_storage_in_future * network_2.storage_units.p_nom_opt.warmwasserspeicher , lifetime_years_hot_water_storage )

#Kombi heater --> Diesel heizung
#Kaufpreis nach Ablauf der Lifetime
exchange_kombi_heizung_in_future = inflation_factor * capital_cost_kombi_heater
#Annuität des Kaufpreises nach Ablauf der Lifetime über die nächste Lifetime
annuity_exchange_kombi_heizung_in_future = annuity( exchange_kombi_heizung_in_future * network_2.links.p_nom_opt.dieselheizung , lifetime_kombi_heater) #operatiosnkosten
###############################



############################### Hinzufügen der ergebniss in den Dataframe

new_rows = pd.DataFrame(
    {0: [annuity_exchange_battery_small_in_future,
         annuity_exchange_wp_in_future,
         annuity_exchange_hot_water_storage_in_future,
         annuity_exchange_kombi_heizung_in_future]
     },
    index = ["Batterie_Austausch" ,
             "WP_Austausch" , 
             "Warmwasserspeicher_Austausch", 
             "Kombi_Heizung_Austausch"]
      )
df_invest_cost_2_annuity = pd.concat([df_invest_cost_2_annuity, new_rows], axis = 0)

invest_cost_1_annuity = round(df_invest_cost_2_annuity.sum(), 2)
###############################


############################### Berechnung der Investionskosten mit Austauschgeräten
df_liftimes = pd.DataFrame(
    {0:[lifetime_years_battery,
        lifetime_years_hot_water_storage, 0, 
        lifetime_diesel_generator ,
        lifetime_kombi_heater,
        0, 0,
        lifetime_years_heatpump ,
        20, lifetime_years_battery,
        lifetime_years_heatpump,
        lifetime_years_hot_water_storage,
        lifetime_kombi_heater]},
    index = ["Lebendsauer_Batteriespeicher",
             "Lebensdauer_Warmwasserspeicher", "Lebensdauer_Dieselversorgung",
             "Lebensdauer_Diesel_Generator", "Lebensdauer_Dieselheizung",
             "Keine Lebensdauer" , "Keine Lebensdauer",
             "Lebensdauer_WP", "Lebensdauer_Sprinter",
             "Lebensdauer_Batteriespeicher_nach_Austausch_bis_20_Jahre",
             "Lebensdauer_WP_nach_Austausch_bis_20_Jahre",
             "Lebensdauer_Warmwasserspeicher_nach_Austausch_bis_20_Jahre",
             "Lebensdauer_Kombi_Heizung_nach_Austausch_bis_20_Jahre"]
        )
#Multipliziert jede Zeile mit jeder Zeile, unabhängig von den Zeilennamen
#df_invest_cost_1 = df_invest_cost_1_annuity * df_liftimes
#hier oben funktioniert nicht aufgrund unterschiedlicher zeilennamen

df_invest_cost_2 = df_invest_cost_2_annuity.mul(df_liftimes.to_numpy())

#axis = 0 --> aus einer Spalte einzelne Zeilen addieren
invest_cost_2 = round(df_invest_cost_2.loc[["batteriespeicher", "warmwasserspeicher", "diesel_generator", 
                                            "dieselheizung", "waermepumpe_cooling", "Sprinter", "Batterie_Austausch", 
                                            "WP_Austausch", "Kombi_Heizung_Austausch"]].sum(axis = 0), 2)

#df_invest_cost_1 = df_invest_cost_1_annuity * df_liftimes

###############################

print("Installierte Batterspeicherkapazität", round(network_2.storage_units.p_nom_opt.batteriespeicher,2), "kWh elektrisch")
print("Installierte Wärmepumpenleistung", round(network_2.links.p_nom_opt.waermepumpe_cooling,2), "kW elektrisch")
print("Installierte Diesel_Generator", round(network_2.links.p_nom_opt.diesel_generator,2), "kWh elektrisch")
print("Installierte Diesel Kombi Heizungsleistung", round(network_2.links.p_nom_opt.dieselheizung,2), "kW elektrisch")
print("Installierte Wärmespeicherleistungleistung", round(network_2.storage_units.p_nom_opt.warmwasserspeicher,2), "kW elektrisch")
warmwasserspeicher_p_nom_opt_in_liter = network_2.storage_units.p_nom_opt.warmwasserspeicher * 3600 / 40 / 4.18
print("Installierte Wärmespeichergröße", round(warmwasserspeicher_p_nom_opt_in_liter ,2), "Liter")
print("Die Investitionskosten belaufen sich auf:", invest_cost_2, "Euro, für einen Zeitraum von 20 Jahren")
print("Die Betriebskosten belaufen sich auf:", operational_cost_2, "Euro/Jahr")
#print(network_2.generators_t.p.sum() * network_2.generators.marginal_cost / diesel_energy_density)


#Investitionskosten am Anfang
invest_cost_1_begin = round(df_invest_cost_2.loc[["batteriespeicher","warmwasserspeicher",
                                            "diesel_generator", "dieselheizung", "waermepumpe_cooling", 
                                            "Sprinter"]].sum(axis = 0), 2)
#Kosten bei Austausch
invest_cost_1_change = round(df_invest_cost_2.loc[["Batterie_Austausch",
                                            "WP_Austausch", "Warmwasserspeicher_Austausch", "Kombi_Heizung_Austausch"]].sum(axis = 0), 2)

print("Investiotionskosten am Anfang", invest_cost_1_begin , "Euro")
print("Investionskosten für den Austausch", invest_cost_1_change, "Euro")


############################### Diagramme zeichnen lassen

#Eine Woche
fig, ax = plt.subplots()

network_2.generators_t.p.iloc[168:336].plot(ax=ax)

ax.set_xlabel("Zeit [h]")
ax.set_ylabel("Leistung [kW]")
ax.set_title("Generatorleistung")
ax.grid(True)

plt.show()

fig, ax_links = plt.subplots()

network_2.links_t.p0.iloc[168:336].plot(ax=ax_links)

ax_links.set_xlabel("Zeit [h]")
ax_links.set_ylabel("Leistung [kW]")
ax_links.set_title("Links Leistungen")
ax_links.grid(True)

plt.show()

fig, ax_loads_week = plt.subplots()

network_2.loads_t.p.iloc[168:336].plot(ax = ax_loads_week)

ax_loads_week.set_xlabel("Zeit [h]")
ax_loads_week.set_ylabel("Leistung [kW]")
ax_loads_week.set_title("Loads Leistungen")
ax_loads_week.grid(True)

plt.show()


fig, ax_storage_units_week = plt.subplots()

network_2.storage_units_t.p.iloc[168:336].plot(ax = ax_storage_units_week)

ax_storage_units_week.set_xlabel("Zeit [h]")
ax_storage_units_week.set_ylabel("Leistung [kW]")
ax_storage_units_week.set_title("Speicher Leistung")
ax_storage_units_week.grid(True)

plt.show()




#Ein Tag
fig, ax_gen_day = plt.subplots()

network_2.generators_t.p.iloc[168:192].plot(ax=ax_gen_day)

ax_gen_day.set_xlabel("Zeit [h]")
ax_gen_day.set_ylabel("Leistung [kW]")
ax_gen_day.set_title("Generatorleistung")
ax_gen_day.grid(True)

plt.show()

fig, ax_links_day = plt.subplots()

network_2.links_t.p0.iloc[168:192].plot(ax=ax_links_day)

ax_links_day.set_xlabel("Zeit [h]")
ax_links_day.set_ylabel("Leistung [kW]")
ax_links_day.set_title("Links Leistungen")
ax_links_day.grid(True)

plt.show()

fig, ax_loads_day = plt.subplots()

network_2.loads_t.p.iloc[168:192].plot(ax = ax_loads_day)

ax_loads_day.set_xlabel("Zeit [h]")
ax_loads_day.set_ylabel("Leistung [kW]")
ax_loads_day.set_title("Loads Leistungen")
ax_loads_day.grid(True)

plt.show()

fig, ax_storage_units_day = plt.subplots()

network_2.storage_units_t.p.iloc[168:192].plot(ax = ax_storage_units_day)

ax_storage_units_day.set_xlabel("Zeit [h]")
ax_storage_units_day.set_ylabel("Leistung [kW]")
ax_storage_units_day.set_title("Speicher Leistung")
ax_storage_units_day.grid(True)

plt.show()