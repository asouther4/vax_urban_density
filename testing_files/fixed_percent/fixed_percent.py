import time
from parallel_run import run

start_time = time.time() # time the beginning of the simulation

configs_list = []    
number_of_runs = 10 #define the number of replications to run each configuration

percent_choices = [(i+1)/20 for i in range(20)]

for percent_choice in percent_choices:

    config = {"number_of_agents" : 1000, 
            "rate_of_infection_per_contact" : 0.03,
            "recovery_rate" : 0.08,
            "incubation_period" : 3,
            "number_of_hubs" : 10,
            "degree_of_homophily" : 0.89,
            "hub_densities" : [8,8,8,8,8,12,12,12,12,12],
            "hub_sizes" : [80,80,80,80,80,120,120,120,120,120],
            "vax_costs" : [1,1,1,1,1,1,1,1,1,1],
            "vax_cost_key" : "constant",
            "starting_vaccination_rate" : 0.15,
            "cost_of_infection" : 3,
            "number_of_seasons" :  25,
            "vax_choice_key" : "fixed_percent",
            "vax_choice_params" : {"percent_choice": percent_choice},
            "log_time_period_data" : False }

    configs_list.append(config)

if __name__ == '__main__': # this line of code is needed to make concurrent.futures work on Windows
    run(configs_list,number_of_runs)