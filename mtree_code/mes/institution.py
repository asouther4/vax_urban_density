"""
SEIR Matching Insitution,
featuring complex network structures

Programmer: Andrew Souther
Date: December 2020

"""

from mTree.microeconomic_system.institution import Institution
from mTree.microeconomic_system.directive_decorators import *
from mTree.microeconomic_system.message import Message
import logging
import random
from datetime import datetime

EXPERIMENT = 25


@directive_enabled_class
class BasicInstitution(Institution):
    def __init__(self):
        self.number_of_agents = None #int, number of agents in the simulation
        self.rate_of_infection_per_contact = None #float, probability between 0 and 1 that you are infected if exposed
        self.time_period = 0 #int, keeps track of t in the SIS simiulation, starts with 0. restarts at next season
        self.season = 0  #TODO: season system still a work in progress
        self.address_list = None #list of agent addresses, sent by the environment
        self.registered_agents = [] #list of mTree address objects for all the registered agents
        self.time_period_data = [] #list of lists of dictionaries of dictionaries, first index is a season, second is a time period
                                #each time period looks like this:
                                #[ {'address': {'starting_state': string, 
                                #               'exposed': True/False } 
                                #   } , ... ] 
                                #TODO: season system still a work in progress
        self.network_structure = {} #dictionary where each key is a str(agent_address), 
                                       #entries are sub_dictionaries with structure {"hub": int, 
                                       #                                             "needed_matches: int",
                                       #                                             "neighbors": list}
        self.inst_unique_id = None #str, a unique_id for this inst
        self.number_of_hubs = None #int, number of hubs to assing agents
        self.degree_of_homophily = None #float, probability that an agent is matched with a neighbor from their own hub
        self.dict_of_hubs = {} #dict where each key is a hub number (int), entries are sub_dict with structure:
                               #                                         {"agents": list, "number_of_connections": int}
        self.eligible_agents = None #list, used in the generate_network function to keep track of matched agents
        self.hub_densities = None #list, list of number of contacts per hub
        self.hub_sizes = None #list, number of agents per hub
        self.number_of_infected = 0 #keeps track of number of agents in state 'In.' Whenever this is 0, end a season 
        self.probability_vacc_choice = None #float, probability that an agent can get vaccinated at the start of a new season
        self.number_of_seasons = None #int, number of seasons to run the SEIR simulation, with vaccination decisions made each time
        self.log_time_period_data= None #bool, tells the institution whether or not to log SEIR data for each time period
        self.cost_of_infection = None #float, some number between 0 or 1. the cost to an agent of getting vaccinated
        self.incubation_period = None #int, on average, how many an agent stays exposed before becoming infectious
        self.recovery_rate = None #float, the probability that an infected agent will recover in a given time period
        self.debug = False

        
    @directive_decorator("init_institution")
    def init_institution(self, message:Message):
        """
        Receives the simulation data from the environment.
        """
        if self.debug:
            logging.log(EXPERIMENT, 'institution entered init_institution')

        #save data about the SEIR simulation
        self.number_of_agents = message.get_payload()["number_of_agents"]
        self.rate_of_infection_per_contact = message.get_payload()["rate_of_infection_per_contact"]
        self.address_list = message.get_payload()["address_list"]
        self.recovery_rate = message.get_payload()["recovery_rate"]
        self.number_of_hubs = message.get_payload()["number_of_hubs"]
        self.degree_of_homophily = message.get_payload()["degree_of_homophily"]
        self.inst_unique_id = 'I' + str(datetime.now()) + str(random.randrange(0,100000000))
        self.hub_densities = message.get_payload()["hub_densities"]
        self.hub_sizes = message.get_payload()["hub_sizes"]
        self.probability_vacc_choice = message.get_payload()["probability_vacc_choice"]
        self.number_of_seasons = message.get_payload()["number_of_seasons"]
        self.cost_of_infection = message.get_payload()["cost_of_infection"]
        self.incubation_period = message.get_payload()["incubation_period"]
        self.log_time_period_data = message.get_payload()["log_time_period_data"]
        self.recovery_rate = message.get_payload()["recovery_rate"] 
        
        #initialize the dictionary for storing hub data
        for i in range(self.number_of_hubs):
            self.dict_of_hubs[i] = {}
            self.dict_of_hubs[i]['agents'] = []
            self.dict_of_hubs[i]['number_of_connections'] = self.hub_densities[i]

        #initiaize the list of lists to store data for each season
        for i in range(self.number_of_seasons):
            self.time_period_data.append([])

        if self.debug:
            logging.log(EXPERIMENT, 'institution exited init_institution')
    
    @directive_decorator("register")
    def register(self, message:Message):
        """
        Receives registration from each agent and compiles a list of registered agents. 
        When the length of that list matches self.number_of_agents, start time_period 0.
        """
        if self.debug:
            logging.log(EXPERIMENT, "institution entered register")


        #save the address, current_state, and group of the registering agent
        agent_address = message.get_sender().myAddress
        current_state = message.get_payload()["current_state"] 
        agent_hub = message.get_payload()["hub"]
        
        #if this is the first agent to be registered in this time period, initialize a new dictionary
        if len(self.time_period_data[self.season]) == self.time_period:
            self.time_period_data[self.season].append({})

        #add this agent to the record for the time period
        self.time_period_data[self.season][self.time_period][f"{agent_address}"] = {}

        #start a record of all registered agents: 
        self.registered_agents.append(agent_address)

        #add the agent to the list for its hub
        self.dict_of_hubs[agent_hub]['agents'].append(agent_address)

        if self.time_period == 0 and self.season == 0:
            #generate the agent's entry in the network structure dictionary
            self.network_structure[f"{agent_address}"] = {}
            self.network_structure[f"{agent_address}"]["hub"] = agent_hub 
            self.network_structure[f"{agent_address}"]["neighbors"] = []
            self.network_structure[f"{agent_address}"]["number_of_connections"] = self.dict_of_hubs[agent_hub]["number_of_connections"]

        if self.debug:
            logging.log(EXPERIMENT, f"INSTITUTION: registered agent = {agent_address} from hub = {agent_hub}")

        #we need to calculate the number of infected agents. When this number is 0, end this season. 
        if current_state == 'In':
            self.number_of_infected += 1

        #find out whether the agent is currently susceptible, exposed, infectious, or recovered 
        self.time_period_data[self.season][self.time_period][f"{agent_address}"]["starting_state"] = current_state
        
        
        #log the number of registered agents so far
        if self.debug:
            logging.log(EXPERIMENT, f"INSTITUTION: registered_agents = {len(self.registered_agents)}, number of agents = {self.number_of_agents}, number of infected = {self.number_of_infected}")

        #when the number of registered agents matches the total number of agents, start the simulation
        #also check that there are still any infected agents
        if len(self.registered_agents) == self.number_of_agents and self.number_of_infected > 0:

            #in the first time_period of the first season, generate a random network structure
            if self.time_period == 0 and self.season == 0:
                self.generate_heterogeneous_network()

            #in all time periods, process one round of the simulation and notify agents of exposure status    
            self.run_basic_simulation()
            self.notify_agents()
            self.time_period += 1 #move to the next time period
            self.registered_agents = [] #reinitialize the registered_agents list for the next time period
            self.number_of_infected = 0 #reinitialize the number of infected for the next time period 
                
        elif len(self.registered_agents) == self.number_of_agents and self.number_of_infected == 0:
            self.start_new_season()
            self.registered_agents = [] #reinitialize the registered_agents list for the next time period
            self.number_of_infected = 0 #reinitialize the number of infected for the next time period 

            self.registered_agents = [] #reinitialize the registered_agents list for the next time period
            self.number_of_infected = 0 #reinitialize the number of infected for the next time period 

        if self.debug:
            logging.log(EXPERIMENT, "institution exited register")
    
    def generate_heterogeneous_network(self):
        """
        This function matches agents into a fixed network during the first time period. 
        This network will be referenced in each time period following. 
        """
        if self.debug:
            logging.log(EXPERIMENT, "Institution entered generate_heterogeneous_network")

        random.shuffle(self.registered_agents)
        self.eligible_agents = self.registered_agents.copy()
        

        #iterate through the list of registered_agents
        for agent in self.registered_agents:
            
            agent_hub = self.network_structure[f"{agent}"]["hub"] #save the hub of the agent in question
            number_of_connections = self.network_structure[f"{agent}"]["number_of_connections"]
            existing_connections = len(self.network_structure[f"{agent}"]["neighbors"])

            #calculate how many remaining matches the agent needs
            remaining_matches = number_of_connections - existing_connections
            if self.debug:
                logging.log(EXPERIMENT, f"Institution: agent {agent}has {existing_connections} exisiting connections,"
                                    f"{number_of_connections} needed, and {remaining_matches} remaining." )

            #check to see if the agent is still available for matching
            if agent in self.eligible_agents:
                
                self.eligible_agents.remove(agent) #this agent is no longer eligible!

                #match the agent that many times
                for i in range(remaining_matches):
                    
                    agent_matching_list = self.eligible_agents.copy() #create a new copy of eligible agents to manipulate

                    #remove all previous matches from the agent_matching_list (if they have any)
                    for past_match in self.network_structure[f"{agent}"]["neighbors"]: 
                        if past_match in agent_matching_list:
                            agent_matching_list.remove(past_match)

                    #create a new list of potential matches inside of the agent's hub and one for outside
                    inside_hub = [potential_match for potential_match in agent_matching_list if potential_match in self.dict_of_hubs[agent_hub]['agents']]
                    outside_hub = [potential_match for potential_match in agent_matching_list if potential_match not in self.dict_of_hubs[agent_hub]['agents']]

                    #if both lists are non-empty, decide randomly where to draw the match, based on the degree_of_homophily
                    if len(inside_hub)>0 and len(outside_hub)>0:
                        homophily_lottery = random.random()
                        if homophily_lottery <= self.degree_of_homophily: #if the lottery is less than the parameter, match within hub
                            random_neighbor = random.choice(inside_hub) 
                        else: #if the lottery exceeds the probability, match outside of hub
                            random_neighbor = random.choice(outside_hub)
                        self.match(agent, random_neighbor)

                    #if only inside_hub is non-empty, match from that list
                    elif len(inside_hub)>0 and len(outside_hub)==0:
                        random_neighbor = random.choice(inside_hub) 
                        self.match(agent, random_neighbor)

                    #if only outside_hub is non_empty, match from that list
                    elif len(inside_hub)==0 and len(outside_hub)>0:
                        random_neighbor = random.choice(outside_hub) 
                        self.match(agent, random_neighbor)

                    else: #if an agent cannot find a valid match, report what agent has been left unmatched
                        logging.log(EXPERIMENT, f"Institution: agent {agent} could not find a valid match when assigning neighbors")

                #at the end of everything, if the agent has too few matches, add them back to the eligble_agents list
                if len(self.network_structure[f"{agent}"]["neighbors"]) < \
                    self.network_structure[f"{agent}"]["number_of_connections"]:
                    self.eligible_agents.append(agent)
                    
        #matching is complete! Let's compute some basic info about the network.
        computed_hub_sizes = [len(self.dict_of_hubs[hub_number]['agents']) for hub_number in self.dict_of_hubs.keys()] 
        total_hub_matches = [0 for i in range(len(self.hub_densities))]  #compute density of each hub
        inside_hub_matches = total_hub_matches.copy()
        total_neighbors = 0 #compute total number of interactions
        neighbors_inside_hub = 0 #compute number of interactions within hub

        for agent in self.registered_agents:
            #if the agent has a weird number of matches, log it
            if len(self.network_structure[f'{agent}']['neighbors']) != self.network_structure[f'{agent}']['number_of_connections']:
                logging.log(EXPERIMENT,  f"Institution: Agent {agent} has {len(self.network_structure[f'{agent}']['neighbors'])} neighbors, wanted {self.network_structure[f'{agent}']['number_of_connections']}")
            else: 
                if self.debug:
                    logging.log(EXPERIMENT, f"Institution: Agent {agent} has the correct number of matches!")
            agent_hub = self.network_structure[f"{agent}"]["hub"]
            total_hub_matches[agent_hub] += len(self.network_structure[f"{agent}"]["neighbors"])
            total_neighbors += len(self.network_structure[f"{agent}"]["neighbors"])  
            for neighbor in self.network_structure[f"{agent}"]["neighbors"]: 
                if neighbor in self.dict_of_hubs[agent_hub]['agents']:
                    neighbors_inside_hub +=1
                    inside_hub_matches[agent_hub] +=1

        #for each hub, density  is the total number of matches divided by the size
        computed_hub_densities = [ ]
        for total, size in zip(total_hub_matches, computed_hub_sizes):
            computed_hub_densities.append(total/size)

        #for each hub, the level of homophily is the number of matches inside-hub divided by the total number of matches
        computed_hub_homophilies = []  
        for inside_total, total in zip(inside_hub_matches, total_hub_matches):
            computed_hub_homophilies.append(inside_total/total)

        #this is the overall homophily of the network
        proportion_inside_hub = neighbors_inside_hub / total_neighbors
            
        logging.log(EXPERIMENT, "INSTITUTION: NETWORK GENERATED! Here is some information: \n" 
                                f"actual list of hub densities = {computed_hub_densities} \n"
                                f"expected list of hub densities = {self.hub_densities}"
                                f"actual list of hub sizes = {computed_hub_sizes} \n"
                                f"expected list of hub sizes = {self.hub_sizes} \n"
                                f"proportion of neighbors inside hub, by hub = {computed_hub_homophilies} \n"
                                f"total proportion of neighbors inside one's hub = {proportion_inside_hub}, expected = {self.degree_of_homophily}")


        #Testing Urban vs. Rural homophily. TODO: maybe make this code more general somehow?
        avg_rural_homophily = 0
        avg_urban_homophily  = 0
        for i in range(self.number_of_hubs):
            if self.hub_densities[i]==4:
                avg_rural_homophily += computed_hub_homophilies[i]
            elif self.hub_densities[i]==7:
                avg_urban_homophily += computed_hub_homophilies[i]
        avg_rural_homophily = avg_rural_homophily/5
        avg_urban_homophily = avg_urban_homophily/5    

        # #logging the different averages
        # self.log_experiment_data({"avg_rural_homophily": avg_rural_homophily,
        #                           "avg_urban_homophily": avg_urban_homophily,
        #                           "data_flag": "homophily"})
        
        # #log some data about network structure
        # for agent in self.registered_agents:
        #     for neighbor in self.network_structure[f"{agent}"]["neighbors"]:
        #         self.log_experiment_data({"source": agent,
        #                                   "target": neighbor,
        #                                   "data_flag": "network"})
        #     #then log some data about agent hubs, #TODO: adjust this depending on the urban-rural contact rates
        #     if len(self.network_structure[f"{agent}"]["neighbors"]) <= 8:
        #         city_type = 'rural'
        #     else: 
        #         city_type = 'urban'
        #     self.log_experiment_data({"agent": agent,
        #                               "hub": self.network_structure[f"{agent}"]["hub"],
        #                               "type": city_type,
        #                               "data_flag": "hub"})
    
    def match(self, agent, neighbor):
        """
        This simple function "matches" two agents into a symmetric relationship. It enters each agent in the other's list of neighbors.
        If the random neighbor reaches their  
        """

        self.network_structure[f"{agent}"]["neighbors"].append(neighbor)
        self.network_structure[f"{neighbor}"]["neighbors"].append(agent)

        #figure out whether the random_neighbor has now reached its max number of matches
        if len(self.network_structure[f"{neighbor}"]["neighbors"]) == \
            self.network_structure[f"{neighbor}"]["number_of_connections"]:
            self.eligible_agents.remove(neighbor)

    def run_basic_simulation(self):
        """
        Runs the SIS simulation for one time period. At the end of this function, the time period is ticked up by 1.  
        """
        if self.debug:
            logging.log(EXPERIMENT, "institution entered run_basic_simulation")
        
        for agent in self.registered_agents:
            self.time_period_data[self.season][self.time_period][f"{agent}"]["exposed"] = False #the default state for this is False, unless they get infected later
               
        new_exposures = 0
        #find out which agent has been matched with an infectious person in this time period
        for key in self.network_structure.keys(): #iterate through all the agents
                if self.debug:
                    logging.log(EXPERIMENT, f"INSTITUTION: agent {key} currently looking for exposure in time period {self.time_period}")
                infectious_neighbors = 0
                if self.debug:
                    logging.log(EXPERIMENT, f"INSTITUTION: agent {key} has these neighbors: {self.network_structure[key]['neighbors']}")
                for neighbor in self.network_structure[key]["neighbors"]: #then iterate through each neighbor they contacted
                    #then check if the agent was susceptible and they came in contact with an infectious neighbor
                    if (self.time_period_data[self.season][self.time_period][f"{neighbor}"]['starting_state'] == 'In') and (self.time_period_data[self.season][self.time_period][f"{key}"]['starting_state'] == 'S'):
                            infectious_neighbors +=1 #keep count of how many infectious neighbors an agent encountered
                #after iterating through each neighbor, calculate the probability that our agent is exposed
                #see Chang and Tassier (2019), A.2 for the following equation
                exposure_probability = 1 - ((1-self.rate_of_infection_per_contact)**infectious_neighbors)
                exposure_lottery = random.random() #randomly draw whether the agent was exposed
                if exposure_lottery <= exposure_probability: 
                    self.time_period_data[self.season][self.time_period][f"{key}"]['exposed'] = True #if the infection lottery passes, that agent is now infected
                    new_exposures += 1 #keep count of how susceptible many agents are exposed                     

        current_recovered = 0
        #count how many infected agents were recovered before this round -- only after time period 0
        if self.time_period > 0:
            for key in self.time_period_data[self.season][self.time_period].keys(): #iterate through all the agents
                if self.time_period_data[self.season][self.time_period][key]["starting_state"] == 'R':
                    current_recovered += 1

        current_infections = 0
        #then count how many agents entered the round infectious
        for key in self.time_period_data[self.season][self.time_period].keys():
            if self.time_period_data[self.season][self.time_period][key]['starting_state'] == 'In': 
                current_infections += 1

        current_exposed = 0
        #now count how many agents are currently exposed
        for key in self.time_period_data[self.season][self.time_period].keys():
            #first, count how many agents entered the round exposed
            if self.time_period_data[self.season][self.time_period][key]['starting_state'] == 'Ex': 
                current_exposed += 1
            #else if the agent was exposed this round, count them too
            elif self.time_period_data[self.season][self.time_period][key]['exposed'] == True:
                current_exposed +=1


        current_vaccinated = 0
        #finally, count how many agents were vaccinated this round
        for key in self.time_period_data[self.season][self.time_period].keys():
            if self.time_period_data[self.season][self.time_period][key]['starting_state'] == 'V': 
                current_vaccinated += 1

        current_susceptible = self.number_of_agents - \
                              current_vaccinated - current_recovered - current_infections - current_exposed
        
        if self.log_time_period_data:
            self.log_experiment_data({"time_period": self.time_period,
                                      "season": self.season,
                                      "current_recovered": current_recovered,
                                      "new_exposures": new_exposures,
                                      "current_infections": current_infections,
                                      "current_exposed": current_exposed,
                                      "current_vaccinated": current_vaccinated,
                                      "current_susceptible": current_susceptible,
                                      "data_flag": 'infection'
                                     })

        if self.debug:
            logging.log(EXPERIMENT, "institution exited run_basic_simulation")
    
    def start_new_season(self):
        """This helper function starts a new season """

        self.time_period = 0 #reset the time period to 0 for the next season
        self.season += 1 #start the next time period

        if self.debug:
            logging.log(EXPERIMENT, f"Institution: Time period data at the end of the last season: {self.time_period_data[(self.season)-1][-1]}")


        #TODO: delete this
        #put all the unvaccinated agents into a list
        #unvaccinated_list = [agent for agent in self.address_list if self.time_period_data[(self.season)-1][-1][f"{agent}"]['starting_state'] != 'V'] 

        #randomly pick ten agents to seed the infection for the next season
        seed_list = random.sample(self.address_list, 10)

        #calculate the number of recovered and the number unvaccinated in each hub
        number_recovered = [0 for i in range(len(self.hub_densities))]
        number_unvaccinated = number_recovered.copy()
        for agent in self.address_list:
            hub = self.network_structure[f"{agent}"]["hub"]   
            if self.time_period_data[(self.season)-1][-1][f"{agent}"]['starting_state'] == 'R':
                number_recovered[hub] += 1
            if self.time_period_data[(self.season)-1][-1][f"{agent}"]['starting_state'] != 'V':
                number_unvaccinated[hub] += 1

        #calculate the probability of infection for each hub. that's the num recovered / num unvaccinated
        probabilities_of_infection = []
        for rec, unvac in zip(number_recovered, number_unvaccinated):
            probabilities_of_infection.append(rec/unvac)
        
        for agent in self.address_list:
            hub = self.network_structure[f"{agent}"]["hub"]   

            #if the agent finished the last season vaccinated, they start the new one vaccinated by default 
            if self.time_period_data[(self.season)-1][-1][f"{agent}"]['starting_state'] == 'V':
                new_season_state = 'V'
            
            else: #if the agent finished the last season unvaccinated, they will start Susceptible by default
                new_season_state = 'S'

            
            #next, we determine whether this agent will serve as a seed of the infection
            if agent in seed_list:
                seed = True
            else:
                seed = False

            #finally, we determine whether the agent will have a vaccination choice in the upcoming season
            vacc_choice_lottery = random.random()
            if vacc_choice_lottery <= self.probability_vacc_choice:
                choice = True
            else: 
                choice = False


            #as long as there is still one more season left to run, notify agents of the new start 
            if self.season < self.number_of_seasons:
                #send a message to the agent notifying them with this information for the new season
                payload = {"choice": choice, 
                           "seed": seed,
                           "new_season_state": new_season_state, 
                           "prob_of_infection": probabilities_of_infection[hub]}
                directive = 'new_season'
                receiver = agent
                self.send_message(payload,directive,receiver)

        #log seasonal data for each hub
        for i in range(self.number_of_hubs):

            self.log_experiment_data({"hub": i,
                                      "hub_size": self.hub_sizes[i],
                                      "hub_density": self.hub_densities[i],
                                      "recovered": number_recovered[i],
                                      "unvaccinated": number_unvaccinated[i],
                                      "season": (self.season) - 1,
                                      "transmission_rate": self.rate_of_infection_per_contact,
                                      "homophily": self.degree_of_homophily,
                                      "prob_vacc_choice": self.probability_vacc_choice,
                                      "recovery_rate": self.recovery_rate,
                                      "incubation_period": self.incubation_period,
                                      "cost_of_infection": self.cost_of_infection,
                                      "inst_unique_id": self.inst_unique_id,
                                      "data_flag": 'seasonal_data'})
        

    def notify_agents(self):
        """This helper function notifies all agents of the most recent round of the SIS simulation"""
    
        for address in self.address_list:
            payload = {"exposed": self.time_period_data[self.season][self.time_period][f"{address}"]['exposed'],
                       "time_period_completed": self.time_period}
            directive = 'notify'
            receiver = address
            self.send_message(payload,directive,receiver)
    
    def send_message(self, payload, directive, receiver):
        """
        This simple helper function sends an mTree message 
        using three inputs.
        """
        new_message = Message()
        new_message.set_sender(self)
        new_message.set_payload(payload)
        new_message.set_directive(directive)
        self.send(receiver,new_message)
        
        if self.debug:
            logging.log(EXPERIMENT, f"message sent by institution, "
                                f"payload = {payload}, "
                                f"directive = {directive}, "
                                f"receiver = {receiver}")
        



