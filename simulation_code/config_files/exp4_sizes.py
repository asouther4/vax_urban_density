import time
from parallel_run import run

start_time = time.time() # time the beginning of the simulation

configs_list = []    
first_density = [6]*5 + [14]*5
second_density = [8]*5 + [12]*5
third_density = [10]*10
hub_densities_list = [first_density, second_density, third_density]

first_size = [60]*5 + [140]*5
second_size = [100]*10
hub_sizes_list = [first_size,second_size]
number_of_runs = 200

for hub_densities in hub_densities_list:
    for hub_sizes in hub_sizes_list:
        config = {"number_of_agents" : 1000, 
                "rate_of_infection_per_contact" : 0.03,
                "recovery_rate" : 0.08,
                "incubation_period" : 3,
                "number_of_hubs" : 10,
                "degree_of_homophily" : 0.89,
                "hub_densities" : hub_densities,
                "hub_sizes" : hub_sizes,
                "infection_costs" : [[2,4]] * 10,
                "infection_cost_key" : "uniform",
                "starting_vaccination_rate" : 0.15,
                "number_of_seasons" :  25,
                "vax_choice_key" : "seasonal_learning",
                "vax_choice_params" : {"discount_factor": 0.9},
                "log_time_period_data" : False }
        configs_list.append(config)

if __name__ == '__main__': # this line of code is needed to make concurrent.futures work on Windows
    run(configs_list,number_of_runs)