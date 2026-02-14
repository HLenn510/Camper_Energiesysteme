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


network_1 = pypsa.Network()
network_1.set_snapshots(loads_pv_temp_hourly.index)

#Busse hinzufügen
network_1.add("Bus", name = "electricity")
network_1.add("Bus", name = "thermal")
network_1.add("Bus", name = "thermal_heating")
network_1.add("Bus", name = "thermal_cooling")
network_1.add("Bus", name = "hot_water")

#Lasten hinzufügen
network_1.add("Load", name = "electrical_load", bus = "electricity" ,p_set = electrical_load )
network_1.add("Load", name = "hot_water_load", bus = "hot_water", p_set = warmwasser_load)
network_1.add("Load", name = "thermal_heating_load", bus = "thermal_heating", p_set = heating_load_e_van)
network_1.add("Load", name = "thermal_cooling_load", bus = "thermal_cooling", p_set = cooling_load_e_van)



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


############################# PV Generator ###############################
#Annahme: Verwendung von Ja Solar 450 W, 70 Euro pro Modul
#6,4286 Euro pro kW
price_per_module = 70
p_nom_modul = 450
price_pv_per_kw =  (price_per_module  /p_nom_modul)*1000 + 800 #preis pro kW
lifetime_pv = 20
network_1.add("Generator", 
              name = "pv",
              bus = "electricity",
              
              p_nom_extendable = True,
              p_max_pu = pv_p_nom_pu,
              lifetime = lifetime_pv,
              
              capital_cost = annuity(price_pv_per_kw, lifetime_pv )
              
              )



############################# Batterie Speicher vom eSprinter PRO 314 ###############################
capacity_kwh_eSprinter = 80.7  # Kapazität in kWh
p_nom_kw_eSprinter = 11.0  # Nennleistung in kW
capex_euro_eSprinter = 60734.15  # Investitionskosten in Euro für den Van plus 20000 Euro Batterietausch
price_euro_esprinter_per_p_nom = 60734.15/p_nom_kw_eSprinter
lifetime_years_eSprinter = 10  # Lebensdauer in Jahren
charging_efficiency_eSprinter = 0.9  # Wirkungsgrad (90%)
discharge_efficiency_eSprinter = 0.95  # Entladewirkungsgrad (95%)
network_1.add("StorageUnit",
    name = "batterie_van",
    bus="electricity",

    # Technische Daten
    p_nom = p_nom_kw_eSprinter,           # 11 kW (fest)
    max_hours = capacity_kwh_eSprinter/p_nom_kw_eSprinter, # ~7.34 Stunden (ergibt 80.7 kWh)

    # Wirtschaftliche Daten (Annualisiert)
    capital_cost = annuity(price_euro_esprinter_per_p_nom, lifetime_years_eSprinter), # Beispiel: 60.734,15€ Investition über 10 Jahre
    lifetime = lifetime_years_eSprinter,
    
    # Effizienz & Verhalten
    efficiency_store = charging_efficiency_eSprinter,    # AC-Laden
    efficiency_dispatch = discharge_efficiency_eSprinter, # Entladen
    cyclic_state_of_charge = True, 
    
    overwrite = True
)


########################### LiTime 12V 200Ah Plus Deep Cycle LiFePO4 Lithium Batterie – 200A BMS ###########################
capacity_kwh_battery = 2.4  # Kapazität in kWh
p_nom_kw_battery = 2.4  # Nennleistung in kW
capex_euro_battery = 469.99 # Investitionskosten in Euro
capex_euro_battery_per_kwh = capex_euro_battery / capacity_kwh_battery  # Investitionskosten in Euro
lifetime_years_battery = 10  # Lebensdauer in Jahren
charging_efficiency_battery = 0.95  # Wirkungsgrad (95%)
discharge_efficiency_battery = 0.95  # Entladewirkungsgrad (95%)
network_1.add("StorageUnit",
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
    
    overwrite = True
)




########################### Link Wärmepumpe electricity zu thermal ###########################
capex_euro_heatpump = 2699.0  # Investitionskosten in Euro von Dometic.com  Dometic Freshjet FJX7 2200
lifetime_years_heatpump = 10  # Lebensdauer in Jahren
p_nom_kw_heatpump_el = 1.05  # Elektrische Nennleistung in kW (Richtwert)
capex_euro_heatpump_per_kw = capex_euro_heatpump / p_nom_kw_heatpump_el
network_1.add("Link",
              name = "waermepumpe",
              bus0 = "electricity",
              bus1 = "thermal", efficiency = 1,
              p_nom_extendable = True, 
              capital_cost = annuity(capex_euro_heatpump_per_kw, lifetime_years_heatpump),
              lifetime = lifetime_years_heatpump
              ,overwrite = True)
#keine Kosten, nur Leistung der WP Dimensionieren


########################### Wärmepumpe_heizen (Camper, variabler COP, extendable) ###########################
# Beispiel: Dometic FreshJet 2200 
network_1.add("Link",
    name = "waermepumpe_heating",
    bus0="thermal",
    bus1="thermal_heating",
    
    # Technische Daten
    p_nom_extendable = True, 
    p_max_pu = df_data["el_p_pu_heating"],  #elektrische Leistungs begrenzung aufgrund der Außentemperatur
    efficiency = df_data["cop_heating"]     #COP
)

########################### Wärmepumpe_kühlen (Camper, variabler EER, extendable) ###########################
# Beispiel: Dometic FreshJet 2200 
network_1.add("Link",
    name = "waermepumpe_cooling",
    bus0="thermal",
    bus1="thermal_cooling",

    # Technische Daten
    p_nom_extendable=True,
    p_max_pu = df_data["el_p_pu_cooling"],  #elektrische Leistungs begrenzung aufgrund der Außentemperatur
    efficiency = df_data["eer_cooling"],    # EER
)

########################### Elektrischer Boiler (Camper, extendable) ###########################
# Beispiel: Truma Therme TT2 (elektrischer Warmwasserbereiter für Camper)
efficiency_boiler = 0.98  # Wirkungsgrad (98%) sehr hohe Effizienz annahme
p_nom_kw_boiler = 1.4  # Elektrische Nennleistung in kW
capex_euro_boiler = 800.0  # Investitionskosten in Euro (Richtwert)
lifetime_years_boiler = 15  # Lebensdauer in Jahren
capex_euro_boiler_per_kw = capex_euro_boiler / p_nom_kw_boiler  # €/kW

network_1.add("Link",
    name = "boiler",
    bus0="electricity",
    bus1="hot_water",

    # Technische Daten
    p_nom_extendable = True,
    efficiency = efficiency_boiler,  # Elektrisch -> Warmwasser
    
    # Wirtschaftliche Daten (Annualisiert)
    capital_cost=annuity(capex_euro_boiler_per_kw, lifetime_years_boiler),
    lifetime = lifetime_years_boiler
)

########################### Warmwasserspeicher (Camper) ###########################
#Beispiel: 30 Liter Warmwasserseicher für Camper
capacity_kwh_hot_water_storage = 0.0349  # Kapazität in kWh (30L * 4.18 kJ/kg/K * 40K / 3600)
p_nom_kw_hot_water_storage = 2.0  # Nennleistung in kW (Be- und Entladerate)
capex_euro_hot_water_storage = 300.0  # Investitionskosten in Euro (Richtwert)
capex_euro_hot_water_storage_per_kwh = capex_euro_hot_water_storage / capacity_kwh_hot_water_storage  # €/kWh
lifetime_years_hot_water_storage = 15  # Lebensdauer in Jahren
standing_loss_hot_water_storage = 0.02  # Wärmeverlust (2% pro Stunde)
network_1.add("StorageUnit",
    name = "warmwasserspeicher",
    bus="hot_water",

    # Technische Daten
    p_nom_extendable = True,
    max_hours = 1/12,  # Annahme ein Duschvorgang pro Stunde maximal --> 5 Minuten in Stunden = 1/12

    # Wirtschaftliche Daten (Annualisiert)
    capital_cost = annuity(capex_euro_hot_water_storage_per_kwh * capacity_kwh_hot_water_storage, lifetime_years_hot_water_storage),
    lifetime = lifetime_years_hot_water_storage,
    
    # Effizienz & Verhalten
    efficiency_store = 1.0,  # Speichern ohne Verluste
    efficiency_dispatch = 1.0,  # Entladen ohne Verluste
    standing_loss = standing_loss_hot_water_storage,  # Wärmeverlust
    cyclic_state_of_charge = True,
)


#optimieren
network_1.optimize(solver_name = "gurobi", threads = 1, method = 2)


# Investitionskosten aus Netzwerk 1 ausgeben

#Annuitätsberechnung für jede komponente
invest_cost_storage_units_1_annuity = (network_1.storage_units.p_nom_opt * network_1.storage_units.capital_cost)
invest_cost_generators_1_annuity = (network_1.generators.p_nom_opt * network_1.generators.capital_cost)
invest_cost_links_1_annuity = (network_1.links.p_nom_opt * network_1.links.capital_cost)
df_invest_cost_1_annuity = pd.concat([invest_cost_storage_units_1_annuity, invest_cost_generators_1_annuity, invest_cost_links_1_annuity])


#operatiosnkosten
operational_cost_1 = round(( network_1.generators_t.p.sum() * network_1.generators.marginal_cost).sum(),2)

###############################Annuitätsberechnungen für die Ausauschgeräte damit ein Zeitrau von 20 Jahren betrachtet werden kann
#Inflation bei 3% über 10 Jahre
inflation_factor = 1.03**10

###############################Kaufpreise in 10 jahren

#Van
cost_battery_exchange = 20000 #Kaufpreis bei t = 0 Jahre
#Kaufpreis nach Ablauf der Lifetime
exchange_battery_van_in_future = inflation_factor * cost_battery_exchange 
#Annuität des Kaufpreises nach Ablauf der Lifetime über die nächste Lifetime
annuity_exchange_battery_van_in_future = annuity( exchange_battery_van_in_future , lifetime_years_eSprinter)

#Batterie
#Kaufpreis nach Ablauf der Lifetime
exchange_battery_small_in_future = inflation_factor * capex_euro_battery
#Annuität des Kaufpreises nach Ablauf der Lifetime über die nächste Lifetime
annuity_exchange_battery_small_in_future = annuity(exchange_battery_small_in_future * network_1.storage_units.p_nom_opt.batteriespeicher  , lifetime_years_battery)


#WP
#Kaufpreis nach Ablauf der Lifetime
exchange_wp_in_future = inflation_factor * capex_euro_heatpump
#Annuität des Kaufpreises nach Ablauf der Lifetime über die nächste Lifetime
annuity_exchange_wp_in_future = annuity( exchange_wp_in_future * network_1.links.p_nom_opt.waermepumpe , lifetime_years_heatpump )

#Warmwasserspeicher
#Kaufpreis nach Ablauf der Lifetime
exchange_hot_water_storage_in_future = inflation_factor * capex_euro_hot_water_storage
#Annuität des Kaufpreises nach Ablauf der Lifetime über die nächste Lifetime
annuity_exchange_hot_water_storage_in_future = annuity(exchange_hot_water_storage_in_future * network_1.storage_units.p_nom_opt.warmwasserspeicher , lifetime_years_hot_water_storage )

#Boiler
#Kaufpreis nach Ablauf der Lifetime
exchange_boiler_in_future = inflation_factor * capex_euro_boiler
#Annuität des Kaufpreises nach Ablauf der Lifetime über die nächste Lifetime
annuity_exchange_boiler_in_future = annuity( exchange_boiler_in_future * network_1.links.p_nom_opt.boiler , lifetime_years_boiler )

###############################


############################### Hinzufügen der ergebniss in den Dataframe

new_rows = pd.DataFrame(
    {0: [ annuity_exchange_battery_van_in_future , 
         annuity_exchange_battery_small_in_future,
         annuity_exchange_wp_in_future,
         annuity_exchange_hot_water_storage_in_future,
         annuity_exchange_boiler_in_future]
     },
    index = ["Van_Batterie_Austausch", 
             "PV_Batterie_Austausch" ,
             "WP_Austausch" , 
             "Warmwasserspeicher_Austausch", 
             "Boiler_Austausch"]
      )
df_invest_cost_1_annuity = pd.concat([df_invest_cost_1_annuity, new_rows], axis = 0)

invest_cost_1_annuity = round(df_invest_cost_1_annuity.sum(), 2)
###############################


############################### Berechnung der Investionskosten mit Austauschgeräten
df_liftimes = pd.DataFrame(
    {0:[lifetime_years_eSprinter , lifetime_years_battery,
        lifetime_years_hot_water_storage, lifetime_pv, 
        lifetime_years_heatpump, 0, 0,
        lifetime_years_boiler,
        lifetime_years_eSprinter, #keine 20 - Lifetime weil sonnst die investitionskosten nicht korrekt sind.
        lifetime_years_battery,
        lifetime_years_heatpump,
        lifetime_years_hot_water_storage,
        lifetime_years_boiler]},
    index = ["Lebendsauer_Batterie_Van", "Lebensdauer_Batterie_PV",
             "Lebensdauer_Warmwasserspeicher", "Lebensdauer_PV",
             "Lebensdauer_WP", "Keine Lebensdauer" , "Keine Lebensdauer",
             "Lebensdauer_Boiler",
             "Lebensdauer_Batterie_Van_nach_Austausch_bis_20_Jahre",
             "Lebensdauer_Batterie_PV_nach_Austausch_bis_20_Jahre",
             "Lebensdauer_WP_nach_Austausch_bis_20_Jahre",
             "Lebensdauer_Warmwasserspeicher_nach_Austausch_bis_20_Jahre",
             "Lebensdauer_Boiler_nach_Austausch_bis_20_Jahre"]
        )
#Multipliziert jede Zeile mit jeder Zeile, unabhängig von den Zeilennamen
#df_invest_cost_1 = df_invest_cost_1_annuity * df_liftimes
#hier oben funktioniert nicht aufgrund unterschiedlicher zeilennamen

df_invest_cost_1 = df_invest_cost_1_annuity.mul(df_liftimes.to_numpy())

#axis = 0 --> aus einer Spalte einzelne Zeilen addieren
invest_cost_1 = round(df_invest_cost_1.loc[["batterie_van", "batteriespeicher","warmwasserspeicher",
                                            "pv", "waermepumpe", "boiler", "Van_Batterie_Austausch",
                                            "WP_Austausch", "Warmwasserspeicher_Austausch", "Boiler_Austausch"]].sum(axis = 0), 2)
#df_invest_cost_1 = df_invest_cost_1_annuity * df_liftimes

###############################


print("Installierte PVleistung", round(network_1.generators.p_nom_opt.pv,2), "kW")
print("Installierte Wärmepumpenleistung", round(network_1.links.p_nom_opt.waermepumpe,2), "kW elektrisch")
print("Installierte Batterspeicherkapazität", round(network_1.storage_units.p_nom_opt.batteriespeicher,2), "kWh elektrisch")
print("Installierte Boilerleistung", round(network_1.links.p_nom_opt.boiler,2), "kW elektrisch")
print("Installierte Wärmespeicherleistungleistung", round(network_1.storage_units.p_nom_opt.warmwasserspeicher,2), "kWh elektrisch")
warmwasserspeicher_p_nom_opt_in_liter = network_1.storage_units.p_nom_opt.warmwasserspeicher * 3600 / 40 / 4.18
print("Installierte Wärmespeichergröße", round(warmwasserspeicher_p_nom_opt_in_liter ,2), "Liter")
print("Die Investitionskosten belaufen sich auf:", invest_cost_1, "Euro, für einen Zeitraum von 20 Jahren")
print("Die Betriebskosten belaufen sich auf:", operational_cost_1, "Euro/Jahr")

#Investitionskosten am Anfang
invest_cost_1_begin = round(df_invest_cost_1.loc[["batterie_van", "batteriespeicher","warmwasserspeicher",
                                            "pv", "waermepumpe", "boiler"]].sum(axis = 0), 2)
#Kosten bei Austausch
invest_cost_1_change = round(df_invest_cost_1.loc[["Van_Batterie_Austausch",
                                            "WP_Austausch", "Warmwasserspeicher_Austausch", "Boiler_Austausch"]].sum(axis = 0), 2)

print("Investiotionskosten am Anfang", invest_cost_1_begin , "Euro")
print("Investionskosten für den Austausch", invest_cost_1_change, "Euro")

############################### Diagramme zeichnen lassen

############################### Eine Woche
fig, ax = plt.subplots()

network_1.generators_t.p.iloc[168:336].plot(ax=ax)

ax.set_xlabel("Zeit [h]")
ax.set_ylabel("Leistung [kW]")
ax.set_title("Generatorleistung")
ax.grid(True)

plt.show()

fig, ax_links = plt.subplots()

network_1.links_t.p0.iloc[168:336].plot(ax=ax_links)

ax_links.set_xlabel("Zeit [h]")
ax_links.set_ylabel("Leistung [kW]")
ax_links.set_title("Links Leistungen")
ax_links.grid(True)

plt.show()

fig, ax_loads_week = plt.subplots()

network_1.loads_t.p.iloc[168:336].plot(ax = ax_loads_week)

ax_loads_week.set_xlabel("Zeit [h]")
ax_loads_week.set_ylabel("Leistung [kW]")
ax_loads_week.set_title("Loads Leistungen")
ax_loads_week.grid(True)

plt.show()

fig, ax_storage_units_week = plt.subplots()

network_1.storage_units_t.p.iloc[168:336].plot(ax = ax_storage_units_week)

ax_storage_units_week.set_xlabel("Zeit [h]")
ax_storage_units_week.set_ylabel("Leistung [kW]")
ax_storage_units_week.set_title("Speicher Leistung")
ax_storage_units_week.grid(True)

plt.show()





############################### Ein Tag
fig, ax_gen_day = plt.subplots()

network_1.generators_t.p.iloc[168:192].plot(ax=ax_gen_day)

ax_gen_day.set_xlabel("Zeit [h]")
ax_gen_day.set_ylabel("Leistung [kW]")
ax_gen_day.set_title("Generatorleistung")
ax_gen_day.grid(True)

plt.show()

fig, ax_links_day = plt.subplots()

network_1.links_t.p0.iloc[168:192].plot(ax=ax_links_day)

ax_links_day.set_xlabel("Zeit [h]")
ax_links_day.set_ylabel("Leistung [MW]")
ax_links_day.set_title("Links Leistungen")
ax_links_day.grid(True)

plt.show()

fig, ax_loads_day = plt.subplots()

network_1.loads_t.p.iloc[168:192].plot(ax = ax_loads_day)

ax_loads_day.set_xlabel("Zeit [h]")
ax_loads_day.set_ylabel("Leistung [kW]")
ax_loads_day.set_title("Loads Leistungen")
ax_loads_day.grid(True)

plt.show()

fig, ax_storage_units_day = plt.subplots()

network_1.storage_units_t.p.iloc[168:192].plot(ax = ax_storage_units_day)

ax_storage_units_day.set_xlabel("Zeit [h]")
ax_storage_units_day.set_ylabel("Leistung [kW]")
ax_storage_units_day.set_title("Speicher Leistung")
ax_storage_units_day.grid(True)

plt.show()