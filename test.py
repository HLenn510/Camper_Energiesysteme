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
i = 0

for i, (pv_active, pv_leistung_optimieren, pv_nom) in enumerate(variante):
    network_1.add("Generator", name = "PV" , bus = "electricity", 
                  p_nom = pv_nom , p_nom_extendable = pv_leistung_optimieren, active = pv_active, overwrite = True)
    i = i +1