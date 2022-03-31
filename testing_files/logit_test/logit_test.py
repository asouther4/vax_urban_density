import time
from parallel_run import run

start_time = time.time() # time the beginning of the simulation

configs_list = []    
number_of_runs = 20 #define the number of replications to run each configuration
beta_list = [0,1,2,3,4,5]
beta_normal_list = [(1,0.5), (2,1), (3,1), (4,2), (5,2) ]

for beta in beta_list:
    config = {"number_of_agents" : 1000, 
            "rate_of_infection_per_contact" : 0.03,
            "recovery_rate" : 0.08,
            "incubation_period" : 3,
            "number_of_hubs" : 10,
            "degree_of_homophily" : 0.89,
            "hub_densities" : [8,8,8,8,8,12,12,12,12,12],
            "hub_sizes" : [80,80,80,80,80,120,120,120,120,120],
            "infection_costs" : [3,3,3,3,3,3,3,3,3,3],
            "infection_cost_key" : "constant",
            "starting_vaccination_rate" : 0.15,
            "number_of_seasons" :  25,
            "vax_choice_key" : "logit_constant",
            "vax_choice_params" : {"beta": beta},
            "log_time_period_data" : False }
    configs_list.append(config)

for beta_tuple in beta_normal_list:
    config = {"number_of_agents" : 1000, 
            "rate_of_infection_per_contact" : 0.03,
            "recovery_rate" : 0.08,
            "incubation_period" : 3,
            "number_of_hubs" : 10,
            "degree_of_homophily" : 0.89,
            "hub_densities" : [8,8,8,8,8,12,12,12,12,12],
            "hub_sizes" : [80,80,80,80,80,120,120,120,120,120],
            "infection_costs" : [3,3,3,3,3,3,3,3,3,3],
            "infection_cost_key" : "constant",
            "starting_vaccination_rate" : 0.15,
            "number_of_seasons" :  25,
            "vax_choice_key" : "logit_normal",
            "vax_choice_params" : {"beta_mean": beta_tuple[0], "beta_sigma": beta_tuple[1]},
            "log_time_period_data" : False }
    configs_list.append(config)

if __name__ == '__main__': # this line of code is needed to make concurrent.futures work on Windows
    run(configs_list,number_of_runs)