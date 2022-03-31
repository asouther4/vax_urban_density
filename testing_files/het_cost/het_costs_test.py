import time
from parallel_run import run

start_time = time.time() # time the beginning of the simulation

configs_list = []    
number_of_runs = 50 #define the number of replications to run each configuration

rural_low_cost = [2,2,2,2,2,4,4,4,4,4]
equal_cost = [3,3,3,3,3,3,3,3,3,3]
rural_high_cost = [4,4,4,4,4,2,2,2,2,2]

infection_costs_list = [rural_low_cost, equal_cost, rural_high_cost]

for infection_costs in infection_costs_list:

    config = {"number_of_agents" : 1000, 
            "rate_of_infection_per_contact" : 0.03,
            "recovery_rate" : 0.08,
            "incubation_period" : 3,
            "number_of_hubs" : 10,
            "degree_of_homophily" : 0.89,
            "hub_densities" : [8,8,8,8,8,12,12,12,12,12],
            "hub_sizes" : [80,80,80,80,80,120,120,120,120,120],
            "infection_costs" : infection_costs,
            "infection_cost_key" : "constant",
            "starting_vaccination_rate" : 0.15,
            "number_of_seasons" :  25,
            "vax_choice_key" : "simple_probability",
            "vax_choice_params" : {"probability_choice": 0.1},
            "log_time_period_data" : False }

    configs_list.append(config)

if __name__ == '__main__': # this line of code is needed to make concurrent.futures work on Windows
    run(configs_list,number_of_runs)