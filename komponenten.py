import pypsa
#Funktion zur Berechnung von Annuity mitdefault 3% Zins, n steht für Jahre, capex für Investitionskosten
def annuity(capex, n, r=0.03):
    if r == 0:
        return capex / n
    else:
        annuity_factor = r / (1 - (1 + r) ** -n)
        return capex * annuity_factor
    


n = pypsa.Network()


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
    p_nom=p_nom_kw_battery,           # 2.4 kW (fest)
    max_hours=capacity_kwh_battery / p_nom_kw_battery, # 1 Stunde (ergibt 2.4 kWh)

    # Wirtschaftliche Daten (Annualisiert)
    capital_cost=annuity(capex_euro_battery_per_kwh * capacity_kwh_battery, lifetime_years_battery), # Beispiel: 3.000€ Investition über 10 Jahre

    # Effizienz & Verhalten
    efficiency_store=charging_efficiency_battery,    # AC-Laden
    efficiency_dispatch=discharge_efficiency_battery, # Entladen
    cyclic_state_of_charge=True, 
)

########################### Wärmepumpe (Camper, fester COP, extendable) ###########################
# Beispiel: Dometic FreshJet 2200 (Wärmepumpe, Dachklima)
cop_heatpump = 2.1  # Leistungszahl (COP, konstant; Richtwert aus Heizleistung/El.-Leistung)
p_nom_kw_heatpump_el = 1.05  # Elektrische Nennleistung in kW (Richtwert)
p_th_kw_heatpump = p_nom_kw_heatpump_el * cop_heatpump  # Thermische Leistung in kW
capex_euro_heatpump = 2200.0  # Investitionskosten in Euro (Richtwert)
lifetime_years_heatpump = 10  # Lebensdauer in Jahren
capex_euro_heatpump_per_kw = capex_euro_heatpump / p_nom_kw_heatpump_el  # €/kW
n.add("Link",
    "Dometic FreshJet 2200 (Wärmepumpe, fester COP, extendable)",
    bus0="electricity",
    bus1="thermal",

    # Technische Daten
    p_nom_extendable=True,
    efficiency=cop_heatpump,     # COP (elektrisch -> thermisch)
    

    # Wirtschaftliche Daten (Annualisiert)
    capital_cost=annuity(capex_euro_heatpump_per_kw, lifetime_years_heatpump),
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
    "Warmwasserspeicher 30L (Camper)",
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


