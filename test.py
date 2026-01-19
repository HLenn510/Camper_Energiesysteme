# -*- coding: utf-8 -*-
"""
Created on Wed Jan  7 18:34:59 2026

@author: avick
"""

import pandas as pd
import pypsa

#Ort setzen wo nach einer Dateil gesucht werden soll
#import os
#os.chdir(r"C:\Users\avick\.spyder-py3\Pypsa\Übungscodes\ÜBbung 3")


variante= pd.read_excel("System_Input.xlsx")
variante

#Netzwerk aufsetzen
network_1 = pypsa.Network()
network_1.set_snapshots(range(8760)) # (df_data.index)

#Busse hinzufügen
network_1.add("Bus", name = "electricity", overwrite = True)
network_1.add("Bus", name = "heat", overwrite = True)
network_1.add("Bus", name = "warmwasserbedarf", overwrite = True)
network_1.add("Bus", name = "cooling", overwrite = True)
i = 0

for i, (pv, pv_leistung_optimieren, pv_nom, pv_capital_cost,
        gas, gas_leistung_optimieren, gas_p_nom, gas_capital_cost, gas_marginal_cost, carrier_gas, efficiency_gas,
        diesel, diesel_leistung_optimieren, diesel_p_nom, diesel_capital_cost, diesel_marginal_cost, carrier_diesel, efficiency_diesel,
        batteriespeicher, batteriespeicher_leistung_optimieren, batteriespeicher_e_nom, batteriespeicher_capital_cost, batterierspeicher_standing_loss,
        warmwasserspeicher, warmwasserspeicher_leistung_optimieren, warmwasserspeicher_e_nom, warmwasserspeicher_capital_cost, warmwasserspeicher_standing_loss,
        solarthermie, solarthermie_leistung_optimieren, solarthermie_p_nom, solarthermie_capital_cost,
        wärmepumpe_heizen, wärmepumpe_heizen_leistung_optimieren, wärmepumpe_heizen_p_nom, wärmepumpe_heizen_capital_cost, wärmepumpe_heizen_efficiency,
        wärmepumpe_kühlen, wärmepumpe_kühlen_leistung_optimieren, wärmepumpe_kühlen_p_nom, wärmepumpe_kühlen_capital_cost, wärmepumpe_kühlen_efficiency,
        diesel_generator, diesel_generator_leistung_optimieren, diesel_generator_p_nom, diesel_generator_capital_cost, diesel_generator_marginal_cost, carrier_diesel_generator, 
        efficiency_diesel_generator
        ) in enumerate(variante):
    #Generatoren hinzufügen
    #Es wird der Status active genutzt um in den verschiedenen Varianten zu entscheiden ob eine Komponente genutzt werden soll oder nicht
    #Die weiteren Parameter werden aus der Excel Datei übernommen

    #PV Generator hinzufügen
    network_1.add("Generator", name = "PV" , bus = "electricity", 
                  p_nom = pv_nom , p_nom_extendable = pv_leistung_optimieren, active = pv, overwrite = True
                    , capital_cost = pv_capital_cost)

    #Gaskessel hinzufügen               
    network_1.add("Generator", name = "Gaskessel" , bus = "heat", 
                  p_nom = gas_p_nom , p_nom_extendable = gas_leistung_optimieren, capital_cost = gas_capital_cost,
                  marginal_cost = gas_marginal_cost/efficiency_gas, efficiency = efficiency_gas, carrier = carrier_gas,
                  active = gas, overwrite = True)
    
    #Dieselkessel hinzufügen
    network_1.add("Generator", name = "Dieselkessel" , bus = "heat", 
                  p_nom = diesel_p_nom , p_nom_extendable = diesel_leistung_optimieren, capital_cost = diesel_capital_cost,
                  marginal_cost = diesel_marginal_cost/efficiency_diesel, efficiency = efficiency_diesel, carrier = carrier_diesel,
                  active = diesel, e_cyclic = True, overwrite = True)
    
    #Batteriespeicher hinzufügen
    network_1.add("Store", name = "Batteriespeicher" , bus = "electricity", 
                  e_nom = batteriespeicher_e_nom , e_nom_extendable = batteriespeicher_leistung_optimieren, capital_cost = batteriespeicher_capital_cost,
                  standing_loss = batterierspeicher_standing_loss,
                  active = batteriespeicher, overwrite = True)
    
    #Dieselgenerator hinzufügen
    network_1.add("Generator", name = "diesel_generator" , bus = "electricity", 
                  p_nom = diesel_generator_p_nom , p_nom_extendable = diesel_generator_leistung_optimieren, capital_cost = diesel_generator_capital_cost,
                  marginal_cost = diesel_generator_marginal_cost/efficiency_diesel_generator, efficiency = efficiency_diesel_generator, carrier = carrier_diesel_generator,
                  active = diesel_generator, overwrite = True)
    i = i +1

