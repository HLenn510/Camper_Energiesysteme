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
capacity_kwh_battery = 2.56  # Kapazität in kWh
p_nom_kw_battery = 1.0  # Nennleistung in kW
capex_euro_battery_per_kwh = 3000.0  # Investitionskosten in Euro
lifetime_years_battery = 10  # Lebensdauer in Jahren
charging_efficiency_battery = 0.95  # Wirkungsgrad (95%)
discharge_efficiency_battery = 0.95  # Entladewirkungsgrad (95%)
n.add("StorageUnit",
    "LiTime 12V 200Ah Plus Deep Cycle LiFePO4",
    bus="electricity",

    # Technische Daten
    p_nom=p_nom_kw_battery,           # 1 kW (fest)
    max_hours=capacity_kwh_battery / p_nom_kw_battery, # ~2.56 Stunden (ergibt 2.56 kWh)

    # Wirtschaftliche Daten (Annualisiert)
    capital_cost=annuity(capex_euro_battery_per_kwh * capacity_kwh_battery, lifetime_years_battery), # Beispiel: 3.000€ Investition über 10 Jahre

    # Effizienz & Verhalten
    efficiency_store=charging_efficiency_battery,    # AC-Laden
    efficiency_dispatch=discharge_efficiency_battery, # Entladen
    cyclic_state_of_charge=True, 
)

