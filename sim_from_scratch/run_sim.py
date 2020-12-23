from VaxModel import VaxModel

config = {"number_of_agents" : 1000,
          "rate_of_infection_per_contact" : 0.03,
          "recovery_rate" :  0.08,
          "incubation_period" : 3,
          "number_of_hubs" : 10,
          "degree_of_homophily" : 0.89,
          "hub_densities" : [8,8,8,8,8,12,12,12,12,12],
          "hub_sizes" : [80,80,80,80,80,120,120,120,120,120],
          "starting_vaccination_rate" :  0.15,
          "cost_of_infection" : 3,
          "probability_vacc_choice" : 0.08,
          "number_of_seasons" :  25,
          "log_time_period_data" : False}

number_of_runs = 3

for i in range(number_of_runs):
    empty_model = VaxModel(config)
    empty_model.init_simulation()
    empty_model.generate_network()
    empty_model.run_full_simulation()