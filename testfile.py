import pypsa
network_1 = pypsa.Network()

network_1.set_snapshots([0,1,2,3])

network_1.add('Bus', name = 'electricity', overwrite = True)
#fügt den Knoten hinzu mit einem Namen und einem carrier (Energieträger), Energieträger nur wichtig für co2 bilanzen.

#elektrische Last hinzufügen 
#es ist möglich den Wirk- und Blindleistungsbedarf als Zeitreihe vorzugeben
network_1.add('Load', name = 'electrical_load', bus = 'electricity', p_set = [4,5,14,12] ,overwrite = True)

network_1.add('Generator', name ='pv_generator', bus = 'electricity',p_nom = 10 , p_max_pu = [0,0.6,0.6,0], marginal_cost = 0 ,overwrite = True)
#nie beim generator p_set beutzen, nur für lastfluss betrachtungen
network_1.add('Generator', name ='diesel_generator', bus = 'electricity', p_nom = 20, marginal_cost = 15, overwrite = True)
#network_1.generators  gibt alle generatoren aus in pandas dataframe

network_1.generators
network_1.optimize(solver_name = 'gurobi')

network_1.generators_t.p.plot(kind = 'bar')
network_1.buses_t.marginal_price.plot()

plot.show()