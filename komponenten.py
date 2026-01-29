import pypsa
import numpy as np
#Funktion zur Berechnung von Annuity mitdefault 3% Zins, n steht für Jahre, capex für Investitionskosten
def annuity(capex, n, r=0.035):
    if r == 0:
        return capex / n
    else:
        annuity_factor = r / (1 - (1 + r) ** -n)
        return capex * annuity_factor
    

temperature = np.random.uniform(-20, 35, 8760)  # Beispielhafte Außentemperaturen für ein Jahr


n = pypsa.Network()
n.set_snapshots(range(8760))  # Ein Jahr mit stündlichen Zeitschritten
n.add("Bus", "electricity")
n.add("Bus", "thermal_heating")
n.add("Bus", "thermal_cooling")
n.add("Bus", "hot_water")
n.add("Bus", "heatpump_electrical")

############################ GENERATOR: Photovoltaik-Anlage (Camper) ##############################
# Beispiel: 500W Photovoltaik-Anlage für Camper
capital_cost_pv_camper = 200.0  # Investitionskosten in Euro (Richtwert)
lifetime_years_pv_camper = 20  # Lebensdauer in Jahren
p_nom_per_module = 0.5  # Leistung pro Modul in kW
capital_cost_pv_camper_per_kw = capital_cost_pv_camper / p_nom_per_module  # €/kW
n.add("Generator",
    "500W Photovoltaik-Anlage (Camper)",
    bus="electricity",
    p_nom_extendable=True,  # Anzahl der Module bleibt offen
    p_max_pu=[], # Zeitabhängiges Sonneneinstrahlungsprofil kommt von renewablesninja
    capital_cost=annuity(capital_cost_pv_camper_per_kw, lifetime_years_pv_camper),  # Beispielwert, anpassen nach Bedarf
    marginal_cost=0.0,  # PV hat keine Brennstoffkosten
)

############################# Batterie Speicher vom eSprinter PRO 314 ###############################
capacity_kwh_eSprinter = 80.7  # Kapazität in kWh
p_nom_kw_eSprinter = 11.0  # Nennleistung in kW
capex_euro_eSprinter = 60734.15  # Investitionskosten in Euro
lifetime_years_eSprinter = 10  # Lebensdauer in Jahren
charging_efficiency_eSprinter = 0.9  # Wirkungsgrad (90%)
discharge_efficiency_eSprinter = 0.95  # Entladewirkungsgrad (95%)
n.add("StorageUnit",
    "eSprinter PRO 314 (81 kWh)",
    bus="electricity",

    # Technische Daten
    p_nom=p_nom_kw_eSprinter,           # 11 kW (fest)
    max_hours=capacity_kwh_eSprinter / p_nom_kw_eSprinter, # ~7.34 Stunden (ergibt 80.7 kWh)

    # Wirtschaftliche Daten (Annualisiert)
    capital_cost=annuity(capex_euro_eSprinter, lifetime_years_eSprinter), # Beispiel: 60.734,15€ Investition über 10 Jahre

    # Effizienz & Verhalten
    efficiency_store=charging_efficiency_eSprinter,    # AC-Laden
    efficiency_dispatch=discharge_efficiency_eSprinter, # Entladen
    cyclic_state_of_charge=True, 
)

########################### LiTime 12V 200Ah Plus Deep Cycle LiFePO4 Lithium Batterie – 200A BMS ###########################
capacity_kwh_battery = 2.4  # Kapazität in kWh
p_nom_kw_battery = 2.4  # Nennleistung in kW
capex_euro_battery = 469.99  # Investitionskosten in Euro
capex_euro_battery_per_kwh = capex_euro_battery / capacity_kwh_battery  # Investitionskosten in Euro
lifetime_years_battery = 10  # Lebensdauer in Jahren
charging_efficiency_battery = 0.95  # Wirkungsgrad (95%)
discharge_efficiency_battery = 0.95  # Entladewirkungsgrad (95%)
n.add("StorageUnit",
    "LiTime 12V 200Ah Plus Deep Cycle LiFePO4",
    bus="electricity",

    # Technische Daten
    p_nom_extendable=True,
    max_hours=capacity_kwh_battery / p_nom_kw_battery, #1 Stunde (ergibt 2.4 kWh)

    # Wirtschaftliche Daten (Annualisiert)
    capital_cost=annuity(capex_euro_battery_per_kwh * capacity_kwh_battery, lifetime_years_battery), # Beispiel: 3.000€ Investition über 10 Jahre

    # Effizienz & Verhalten
    efficiency_store=charging_efficiency_battery,    # AC-Laden
    efficiency_dispatch=discharge_efficiency_battery, # Entladen
    cyclic_state_of_charge=True, 
)

########################### Wärmepumpe (Camper, fester COP, extendable) ###########################
# Viessmann Vitocal 150A04 Compact
# cop_heatpump = 2.1  # Leistungszahl (COP, konstant; Richtwert aus Heizleistung/El.-Leistung)
p_nom_kw_heatpump_el = 0.8  # Elektrische Nennleistung in kW (Richtwert) 
# p_th_kw_heatpump = p_nom_kw_heatpump_el * cop_heatpump  # Thermische Leistung in kW
capex_euro_heatpump = 2200  # Investitionskosten in Euro (Richtwert)
lifetime_years_heatpump = 10  # Lebensdauer in Jahren
capex_euro_heatpump_per_kw = capex_euro_heatpump / p_nom_kw_heatpump_el  # €/kW
n.add("Link",
    "Viessmann Vitocal 150A04 Compact",
    bus0="electricity",
    bus1="heatpump_electrical",

    # Technische Daten
    p_nom_extendable=True,
    efficiency=1,     # Elektrisch zu Elektrisch (Wärmepumpe hat eigenen COP in den folgenden Links)
    
    # Wirtschaftliche Daten (Annualisiert)
    capital_cost=annuity(capex_euro_heatpump_per_kw, lifetime_years_heatpump),
)

########################## Wärmepumpen Links mit verschiedenen COPs (Camper) ##########################
#COP Kühlen und Heizen 
#Annahme verhält sich ähnlich wie Viessman 151-A04, 230V~
#Annhame betreiben bei 45 Grad heizen,  Seite 31
temp_heating = [-20, -15, -7, -2, 7, 10, 20, 30 ,35]
el_power_heating = [1.33, 1.39, 1.46, 0.77, 1.02, 1.01, 0.98, 0.92, 0.88]
cop_heating = [1.82, 2.06, 2.52, 3.12, 3.67, 4.05, 5.65, 8.09, 8.70]
hp_p_nom_heating = 0.8 # A7/W35 
el_p_pu_heating = np.interp(temperature, temp_heating, el_power_heating) / hp_p_nom_heating

#Betreiben bei W 7,   Seite 32
temp_cooling = [20, 25, 27, 30, 35, 40, 45]
el_power_cooling = [0.65, 0.73, 0.76, 0.81, 0.90, 0.97, 0.98]
eer_cooling = [5.4, 4.4, 4.1, 3.6, 2.9, 2.3, 1.8]
hp_p_nom_cooling = 0.85 #A35/W18
el_p_pu_cooling = np.interp(temperature, temp_cooling, el_power_cooling) / hp_p_nom_cooling

n.add("Link",
    "Wärmepumpe Heizen (COP variabel)",
    bus0="heatpump_electrical",
    bus1="thermal_heating",
    p_nom_extendable=True,
    efficiency=np.interp(temperature, temp_heating, cop_heating),
    p_max_pu=el_p_pu_heating,
    capital_cost=0.0,  # Kosten sind im Wärmepumpen-Hauptlink enthalten
)

n.add("Link",
    "Wärmepumpe Kühlen (COP variabel)",
    bus0="heatpump_electrical",
    bus1="thermal_cooling",
    p_nom_extendable=True,
    efficiency=np.interp(temperature, temp_cooling, eer_cooling),
    p_max_pu=el_p_pu_cooling,
    capital_cost=0.0,  # Kosten sind im Wärmepumpen-Hauptlink enthalten
)


########################### Elektrischer Boiler (Camper, extendable) ###########################
# Beispiel: Truma Therme TT2 (elektrischer Warmwasserbereiter für Camper)
efficiency_boiler = 0.98  # Wirkungsgrad (98%)
p_nom_kw_boiler = 1.4  # Elektrische Nennleistung in kW
capex_euro_boiler = 800.0  # Investitionskosten in Euro (Richtwert)
lifetime_years_boiler = 15  # Lebensdauer in Jahren
capex_euro_boiler_per_kw = capex_euro_boiler / p_nom_kw_boiler  # €/kW
n.add("Link",
    "Truma Therme TT2 (Elektrischer Boiler, extendable)",
    bus0="electricity",
    bus1="hot_water",

    # Technische Daten
    p_nom_extendable=True,
    efficiency=efficiency_boiler,  # Elektrisch -> Warmwasser

    # Wirtschaftliche Daten (Annualisiert)
    capital_cost=annuity(capex_euro_boiler_per_kw, lifetime_years_boiler),
)

########################### Warmwasserspeicher (Camper) ###########################
# Beispiel: 30 Liter Warmwasserspeicher für Camper
capacity_kwh_hot_water_storage = 0.0349  # Kapazität in kWh (30L * 4.18 kJ/kg/K * 10K / 3600)
p_nom_kw_hot_water_storage = 2.0  # Nennleistung in kW (Be- und Entladerate)
capex_euro_hot_water_storage = 300.0  # Investitionskosten in Euro (Richtwert)
capex_euro_hot_water_storage_per_kwh = capex_euro_hot_water_storage / capacity_kwh_hot_water_storage  # €/kWh
lifetime_years_hot_water_storage = 15  # Lebensdauer in Jahren
standing_loss_hot_water_storage = 0.02  # Wärmeverlust (2% pro Stunde)
n.add("StorageUnit",
    "Warmwasserspeicher (Camper)",
    bus="hot_water",

    # Technische Daten
    p_nom=p_nom_kw_hot_water_storage,  # 2 kW (fest)
    max_hours=capacity_kwh_hot_water_storage / p_nom_kw_hot_water_storage,  # ~0.017 Stunden

    # Wirtschaftliche Daten (Annualisiert)
    capital_cost=annuity(capex_euro_hot_water_storage_per_kwh * capacity_kwh_hot_water_storage, lifetime_years_hot_water_storage),

    # Effizienz & Verhalten
    efficiency_store=1.0,  # Speichern ohne Verluste
    efficiency_dispatch=1.0,  # Entladen ohne Verluste
    standing_loss=standing_loss_hot_water_storage,  # Wärmeverlust
    cyclic_state_of_charge=True,
)


