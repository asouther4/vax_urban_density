import time
from parallel_run import run

start_time = time.time() # time the beginning of the simulation

configs_list = []    
number_of_runs = 25 #define the number of replications to run each configuration
mean_list = [1,2,3,4,5]
sd_list = [0.25,0.5,0.75,1]
cost_list = []

for mean in mean_list: 
    for sd in sd_list:
        cost_dict = {"mean": mean, "sd": sd}
        cost_list.append(cost_dict)

for cost_dict in cost_list:
    config = {"number_of_agents" : 1000, 
            "rate_of_infection_per_contact" : 0.03,
            "recovery_rate" : 0.08,
            "incubation_period" : 3,
            "number_of_hubs" : 10,
            "degree_of_homophily" : 0.89,
            "hub_densities" : [8,8,8,8,8,12,12,12,12,12],
            "hub_sizes" : [80,80,80,80,80,120,120,120,120,120],
            "infection_costs" : [cost_dict] * 10,
            "infection_cost_key" : "normal",
            "starting_vaccination_rate" : 0.15,
            "number_of_seasons" :  25,
            "vax_choice_key" : "seasonal_learning",
            "vax_choice_params" : {"discount_factor": 0.9},
            "log_time_period_data" : False }
    configs_list.append(config)

if __name__ == '__main__': # this line of code is needed to make concurrent.futures work on Windows
    run(configs_list,number_of_runs)