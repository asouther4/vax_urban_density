import logging
import random
import jsonlines
from datetime import datetime

logging.basicConfig(filename='test.log', level=logging.DEBUG)

class VaxAgent:
    def __init__(self, unique_id, model):
        self.unique_id = unique_id
        self.model = model
        self.current_state = None
        self.hub = None
        self.neighbors = None 
        self.number_of_connections = None
        self.time_infected = 0
        self.time_exposed = 0 
        self.debug = False

    def error_log(self, string):
        """
        This helper function builds an error logging statement with a uniform structure. 
        As an input, it accepts a string with some kind of specialized message for the log. 
        """
        logging.debug("ERROR: " + string + f"unique_id = {self.unique_id}") 


    def update_state(self, exposed, time_period):
        """
        In this method, the agent receives information about the previous round from the institution, 
        and it keeps track of its own S/E/I/R status. 
        """

        if self.debug:
            logging.debug(f'agent {self.unique_id} entered notify')
        
        #keep count of how many time periods each agent has spent infected
        if self.current_state == 'In':
            self.time_infected += 1

            #also check whether the agent randomly recovers (with probability equal to self.recovery_rate)
            recovery_lottery = random.random()
            if recovery_lottery <= self.model.recovery_rate:
                if self.debug:
                    logging.debug(f"Agent {self.unique_id} has recovered after spending {self.time_infected} time periods infected!")
                self.current_state = 'R'

        elif self.current_state == 'Ex':
            self.time_exposed +=1
            #check whether the agent will randomly transition from Exposed to Infected
            incubation_lottery = random.random()
            transition_rate = (1 / self.model.incubation_period) #the probability of transition is 1/incubation_period
            if incubation_lottery <= transition_rate:
                if self.debug:
                    logging.debug(f"Agent {self.unique_id} has become infectious after spending {self.time_exposed} time periods infected!")
                self.current_state = 'In'
        
        #TEST: only a Susceptible agent can be infected
        if (exposed == True) and (self.current_state != 'S'): 
            self.error_log(f"A non-Susceptible agent has been exposed, current_state = {self.current_state}")

        #change the agent's current state to exposed before the next round
        if exposed == True:  
            self.current_state = 'Ex'
    

    def new_season(self, seed, new_season_state, probabilities_of_infection):
        """
        Receives information about the start of the new epidemic season, whenever a new season starts. 
        """

        if self.debug:
            logging.debug(f'agent {self.unique_id} entered new_season')

        #agents who were vaccinated in the previous season should remain vaccinated
        if self.current_state == 'V' and new_season_state != 'V':
            logging.debug(f"ERROR: Agent {self.unique_id} somehow lost vaccination at the beginning of a new season")

        #update your current state for the new season
        self.current_state = new_season_state

        #decide whether or not this agent will start the season vaccinated
        self.vax_choice(probabilities_of_infection)
        
        #finally, consider whether this agent is a seed of the infection
        if seed:
            if self.current_state != 'V': #if a seed agent is not vaccinated, they start the season Infected
                self.current_state = 'In'

        if self.debug:
            logging.debug(f"Agent {self.unique_id} is facing probabilities_of_infection of {probabilities_of_infection}"
                          f"in hub {self.hub}, along with a cost_of_infection of {self.model.cost_of_infection}.")

        if self.debug:
            logging.debug(f'agent {self.unique_id} exited new_season')

    def vax_choice(self,probabilities_of_infection):
        """
        This helper method determines whether the agent will get vaccinated in the upcoming season. 
        The particular algorithm used depends on the 'vax_choice_key' passed in the config file, 
        along with the 'vax_choice_params'. 

        Possible vax choice keys: 

        - simple_probability,
            Parameters: probability_choice
            Description: by default, each agent keeps same state as last season. 
                However, with probability = probability_choice, agents change their vaccine status. 
                If probability of infection from their own region last season was greater than
                1/cost_of_infection, the agent decides to get vaccinated. Otherwise not. 
        
        - neighbors, 
            Parameters: None
            Description: each agent looks at how many unvaccinated neighbors were 
                infected in the previous season. Each agent calculates a simple probability of infection
                equal to num_infected / num_unvaccinated, including their own data. 
                If this probability of infection is greater than 1/cost_of_infection, the agent decides 
                to get vaccinated. Otherwise not. 
        """
        vax_choice_key = self.model.vax_choice_key #retrieve the vax_choice_key from the model
        vax_choice_params = self.model.vax_choice_params #retrieve parameters for vax_choice algorithm from model

        if vax_choice_key == "simple_probability":
            probability_choice = vax_choice_params["probability_choice"]
            vax_choice_lottery = random.random() #take a random draw between (0,1)
            if vax_choice_lottery <= probability_choice: #if the draw is less than probability_choice, update_state
                prob_of_infection = probabilities_of_infection[self.hub] # find out the probability of infection from your own hub
                if prob_of_infection >= (1/self.model.cost_of_infection): #get vaccinated if the probability of infection is high in your region
                    self.current_state = 'V'
                    if self.debug: 
                        logging.debug(f"Agent {self} chose to get vaccinated at the end of season {self.model.season}")
                else: 
                    self.current_state = 'S'
        
        elif vax_choice_key == "neighbors":
            num_infected = 0
            num_unvaccinated = 0
            observations = self.neighbors.copy() + [self] # the agent looks at her own data long with her neighbors

            # if an agent finished recovered, they were infected at some point last season. 
            # If they finished vax'ed, they were always vax'ed that season. 
            for agent in observations: 
                if self.model.time_period_data[self.model.season][-1][f"{agent}"]['starting_state'] == 'R':
                    num_infected +=1 
                if self.model.time_period_data[self.model.season][-1][f"{agent}"]['starting_state'] != 'V':
                    num_unvaccinated +=1     

            if self.debug: 
                logging.debug(f"Agent {self} had {num_infected} infected contacts"
                            f"and {num_unvaccinated} unvaccinated contacts after season {self.model.season} (including self)." )
            
            if num_unvaccinated > 0: #if any of your neighbors were unvaccinated, make a vaccine choice
                prob_of_infection = num_infected / num_unvaccinated # risk is the fraction of infected unvaccinated 
                if prob_of_infection >= (1/self.model.cost_of_infection): #get vaccinated if the probability of infection is high in your region
                    self.current_state = 'V'
                    #if self.debug: TODO: put back inside debug conditional
                    logging.debug(f"Agent {self} chose to get vaccinated at the end of season {self.model.season}/")
                else: 
                    self.current_state = 'S'
            else: 
                self.current_state = 'S'

        else: 
            self.error_log(f"Agent received unexpected value for vax_choice_key = {self.vax_choice_key}")

class VaxModel:
    """A model with some number of agents."""
    def __init__(self, config):
        self.number_of_agents = config["number_of_agents"]
        self.rate_of_infection_per_contact = config["rate_of_infection_per_contact"]
        self.recovery_rate = config["recovery_rate"]
        self.incubation_period = config["incubation_period"]
        self.number_of_hubs = config["number_of_hubs"]
        self.degree_of_homophily = config["degree_of_homophily"]
        self.hub_densities = config["hub_densities"]
        self.hub_sizes = config["hub_sizes"]
        self.starting_vaccination_rate = config["starting_vaccination_rate"]
        self.cost_of_infection = config["cost_of_infection"]
        self.probability_vacc_choice = config["probability_vacc_choice"]
        self.number_of_seasons =  config["number_of_seasons"]
        self.log_time_period_data = config["log_time_period_data"]
        self.vax_choice_key = config["vax_choice_key"]
        self.vax_choice_params = config["vax_choice_params"]
        self.agents = []
        self.dict_of_hubs = {} 
        self.eligible_agents = None
        self.network_structure = {} 
        self.time_period_data = []
        self.debug = False
        self.season = 0
        self.time_period = 0
        self.number_infected = None
        self.seasonal_hub_data = {}
        self.seasonal_hub_data["observations"] = []
        self.inst_unique_id = 'I' + str(datetime.now()) + str(random.randrange(0,100000000)) #TODO: fix this

    def init_simulation(self):
        """Initializes each agent with a starting state and a hub"""
        #SANITY CHECK 1
        if (len(self.hub_sizes) != len(self.hub_densities)) or \
           (len(self.hub_sizes) != self.number_of_hubs) or \
           (len(self.hub_densities) != self.number_of_hubs):
           logging.debug("ERROR: there is something wrong with the length of the hub lists")
        
        #SANITY CHECK 2
        alleged_number_of_agents = 0
        for number in self.hub_sizes:
            alleged_number_of_agents+=number
        if alleged_number_of_agents != self.number_of_agents:
            logging.debug("ERROR: there is something wrong with the hub_sizes list or the number of agents")

        #initialize the dictionary for storing hub data
        for i in range(self.number_of_hubs):
            self.dict_of_hubs[i] = {}
            self.dict_of_hubs[i]['agent_ids'] = []
            self.dict_of_hubs[i]['number_of_connections'] = self.hub_densities[i]

        #initiaize the list of lists to store data for each season
        for i in range(self.number_of_seasons):
            self.time_period_data.append([])

        #initialize the agents with a unique id
        for i in range(self.number_of_agents):
            agent = VaxAgent(i, self)
            self.agents.append(agent)
                
        current_hub = 0 #the first agent will be assigned to group 1
        current_agent = 0

        #decide which 10 agents will start as the "seeds" of the infection
        seed_agents = random.sample(self.agents, 10) #TODO: implement a number_of_seeds parameter in the config file

        for agent in self.agents: #iterate through the list of agents

            #first decide whether the agent starts infected, susceptible, or vaccinated
            if agent in seed_agents:
                current_state = 'In'
            else: #if the agent is not a seed agent, randomly draw whether they start vaccinated or susceptible
                random_draw = random.random() #pick a random float between 0 and 1
                if random_draw <= self.starting_vaccination_rate: #if the random draw is at most the vacc rate, vaccinate
                    current_state = 'V' 
                else: #if the random draw is higher, the agent starts off susceptible
                    current_state = 'S' 

            agent.current_state = current_state
            agent.hub = current_hub
            agent.neighbors = []
            agent.number_of_connections = self.dict_of_hubs[agent.hub]["number_of_connections"]
            self.dict_of_hubs[agent.hub]['agent_ids'].append(agent.unique_id) 

            #after notifying the agent of their hub, prepare to assign the next agent to the next hub
            if current_agent < self.hub_sizes[current_hub] - 1: #if this hub isn't full, keep going
                current_agent+=1
            elif current_agent == self.hub_sizes[current_hub] - 1: #if this hub is full, move to the next one
                current_hub+=1
                current_agent = 0

    def generate_network(self):

        random.shuffle(self.agents)
        self.eligible_agents = self.agents.copy()
        
        #iterate through the list of registered_agents
        for agent in self.agents:
            
            #agent_hub = self.network_structure[f"{agent}"]["hub"] #save the hub of the agent in question
            #number_of_connections = self.network_structure[f"{agent}"]["number_of_connections"]
            
            existing_connections = len(agent.neighbors)

            #calculate how many remaining matches the agent needs
            remaining_matches = agent.number_of_connections - existing_connections
            if self.debug:
                logging.debug(f"Institution: agent {agent} has {existing_connections} exisiting connections,"
                              f"{agent.number_of_connections} needed, and {remaining_matches} remaining." )

            #check to see if the agent is still available for matching
            if agent in self.eligible_agents:
                
                self.eligible_agents.remove(agent) #this agent is no longer eligible!

                #match the agent that many times
                for i in range(remaining_matches):
                    
                    agent_matching_list = self.eligible_agents.copy() #create a new copy of eligible agents to manipulate

                    #remove all previous matches from the agent_matching_list (if they have any)
                    for past_match in agent.neighbors: 
                        if past_match in agent_matching_list:
                            agent_matching_list.remove(past_match)

                    #create a new list of potential matches inside of the agent's hub and one for outside
                    inside_hub = [potential_match for potential_match in agent_matching_list if potential_match.unique_id in self.dict_of_hubs[agent.hub]['agent_ids']]
                    outside_hub = [potential_match for potential_match in agent_matching_list if potential_match.unique_id not in self.dict_of_hubs[agent.hub]['agent_ids']]

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
                        logging.debug(f"Institution: agent {agent} could not find a valid match when assigning neighbors")

                #at the end of everything, if the agent has too few matches, add them back to the eligble_agents list
                if len(agent.neighbors) < \
                    agent.number_of_connections:
                    self.eligible_agents.append(agent)
                    
        #matching is complete! Let's compute some basic info about the network.
        computed_hub_sizes = [len(self.dict_of_hubs[hub_number]['agent_ids']) for hub_number in self.dict_of_hubs.keys()] 
        total_hub_matches = [0 for i in range(len(self.hub_densities))]  #compute density of each hub
        inside_hub_matches = total_hub_matches.copy()
        total_neighbors = 0 #compute total number of interactions
        neighbors_inside_hub = 0 #compute number of interactions within hub

        for agent in self.agents:
            #if the agent has a weird number of matches, log it
            if len(agent.neighbors) != agent.number_of_connections:
                logging.debug(f"Institution: Agent {agent} has {len(agent.neighbors)} neighbors, wanted {agent.number_of_connections}")
            else: 
                if self.debug:
                    logging.debug(f"Institution: Agent {agent} has the correct number of matches!")
            total_hub_matches[agent.hub] += len(agent.neighbors)
            total_neighbors += len(agent.neighbors)  
            for neighbor in agent.neighbors: 
                if neighbor.unique_id in self.dict_of_hubs[agent.hub]['agent_ids']:
                    neighbors_inside_hub +=1
                    inside_hub_matches[agent.hub] +=1

        #for each hub, density is the total number of matches divided by the size
        computed_hub_densities = [ ]
        for total, size in zip(total_hub_matches, computed_hub_sizes):
            computed_hub_densities.append(total/size)

        #for each hub, the level of homophily is the number of matches inside-hub divided by the total number of matches
        computed_hub_homophilies = []  
        for inside_total, total in zip(inside_hub_matches, total_hub_matches):
            computed_hub_homophilies.append(inside_total/total)

        #this is the overall homophily of the network
        proportion_inside_hub = neighbors_inside_hub / total_neighbors
            
        logging.debug("INSTITUTION: NETWORK GENERATED! Here is some information: \n" 
                      f"actual list of hub densities = {computed_hub_densities} \n"
                      f"expected list of hub densities = {self.hub_densities} \n"
                      f"actual list of hub sizes = {computed_hub_sizes} \n"
                      f"expected list of hub sizes = {self.hub_sizes} \n"
                      f"proportion of neighbors inside hub, by hub = {computed_hub_homophilies} \n"
                      f"total proportion of neighbors inside one's hub = {proportion_inside_hub}, expected = {self.degree_of_homophily}")

        #Testing Urban vs. Rural homophily. TODO: this code seems to be broken. make it more general somehow?? 
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

        (agent.neighbors).append(neighbor)
        (neighbor.neighbors).append(agent)

        #figure out whether the random_neighbor has now reached its max number of matches
        if len(neighbor.neighbors) == \
            neighbor.number_of_connections:
            self.eligible_agents.remove(neighbor)

    def run_full_simulation(self):
        
        for season in range(self.number_of_seasons): 
            self.season = season

            #count the number of infected agents at the start of the season
            self.number_infected = sum([1 for agent in self.agents if agent.current_state == 'In'])
            self.number_vaccinated = sum([1 for agent in self.agents if agent.current_state == 'V'])

            #if self.debug: TODO: put back inside debug conditional
            logging.debug(f"Institution: Entered loop for new season = {self.season} inside run_full_simulation "
                              f"with {self.number_infected} infected agents and {self.number_vaccinated} vaccinated agents to begin.")

            # if no agents started infected, then all seed agents were vaxed, and no epidemic takes place
            if self.number_infected == 0:
                logging.debug(f"Institution: All seed agents were vaccinated in season {self.season} so no epidemic took place.")
                
                #log time period data such that all agents were not exposed
                self.time_period_data[self.season].append({})
                for agent in self.agents:
                    self.time_period_data[self.season][self.time_period][f"{agent}"] = {} #add this agent to the record for the time period
                    self.time_period_data[self.season][self.time_period][f"{agent}"]["exposed"] = False #the default state for this is False, unless they get infected later
                    self.time_period_data[self.season][self.time_period][f"{agent}"]["starting_state"] = agent.current_state

            #repeat the simulation until the number of infected equals zero        
            while self.number_infected > 0:
                self.run_one_time_period()

                for agent in self.agents: #notify agents of their exposure status, allow them to change state
                    exposed = self.time_period_data[self.season][self.time_period][f"{agent}"]['exposed']
                    agent.update_state(exposed, self.time_period)

                self.time_period += 1 #move to the next time period
                self.number_infected = sum([1 for agent in self.agents if agent.current_state == 'In'])
            
            #whenever the infection dies out, end the season
            self.end_season(season)

        
    def run_one_time_period(self):
        """
        Runs the SEIR simulation for one time period. At the end of this function, the time period is ticked up by 1.  
        """
        if self.debug:
            logging.debug(f"Institution entered run_one_time_period, time_period = {self.time_period}, season = {self.season}")
        
        self.time_period_data[self.season].append({})

        for agent in self.agents:
            self.time_period_data[self.season][self.time_period][f"{agent}"] = {} #add this agent to the record for the time period
            self.time_period_data[self.season][self.time_period][f"{agent}"]["exposed"] = False #the default state for this is False, unless they get infected later
            self.time_period_data[self.season][self.time_period][f"{agent}"]["starting_state"] = agent.current_state

        if self.debug:
            logging.debug(f"Institution: initialized time_period_data in time period = {self.time_period}, season = {self.season}, "
                          f"time_period_data = {self.time_period_data[self.season][self.time_period]}")

        new_exposures = 0
        #find out which agent has been matched with an infectious person in this time period
        for agent in self.agents: #iterate through all the agents
                if self.debug:
                    logging.debug(f"INSTITUTION: agent {agent} currently looking for exposure in time period {self.time_period}")
                infectious_neighbors = 0
                if self.debug:
                    logging.debug(f"INSTITUTION: agent {agent} has these neighbors: {agent.neighbors}")
                for neighbor in agent.neighbors: #then iterate through each neighbor they contacted
                    #then check if the agent was susceptible and they came in contact with an infectious neighbor
                    if (self.time_period_data[self.season][self.time_period][f"{neighbor}"]['starting_state'] == 'In') and (self.time_period_data[self.season][self.time_period][f"{agent}"]['starting_state'] == 'S'):
                            infectious_neighbors +=1 #keep count of how many infectious neighbors an agent encountered
                #after iterating through each neighbor, calculate the probability that our agent is exposed
                #see Chang and Tassier (2019), A.2 for the following equation
                exposure_probability = 1 - ((1-self.rate_of_infection_per_contact)**infectious_neighbors)
                exposure_lottery = random.random() #randomly draw whether the agent was exposed
                if exposure_lottery <= exposure_probability: 
                    self.time_period_data[self.season][self.time_period][f"{agent}"]['exposed'] = True #if the infection lottery passes, that agent is now infected
                    new_exposures += 1 #keep count of how susceptible many agents are exposed                     

        current_recovered = 0
        #count how many infected agents were recovered before this round -- only after time period 0
        if self.time_period > 0:
            for agent in self.agents: ###self.time_period_data[self.season][self.time_period].keys(): #iterate through all the agents
                if self.time_period_data[self.season][self.time_period][f"{agent}"]["starting_state"] == 'R':
                    current_recovered += 1

        current_infections = 0
        #then count how many agents entered the round infectious
        for agent in self.agents: #self.time_period_data[self.season][self.time_period].keys():
            if self.time_period_data[self.season][self.time_period][f"{agent}"]['starting_state'] == 'In': 
                current_infections += 1

        current_exposed = 0
        #now count how many agents are currently exposed
        for agent in  self.agents: #self.time_period_data[self.season][self.time_period].keys():
            #first, count how many agents entered the round exposed
            if self.time_period_data[self.season][self.time_period][f"{agent}"]['starting_state'] == 'Ex': 
                current_exposed += 1
            #else if the agent was exposed this round, count them too
            elif self.time_period_data[self.season][self.time_period][f"{agent}"]['exposed'] == True:
                current_exposed +=1

        current_vaccinated = 0
        #finally, count how many agents were vaccinated this round
        for agent in self.agents: #self.time_period_data[self.season][self.time_period].keys():
            if self.time_period_data[self.season][self.time_period][f"{agent}"]['starting_state'] == 'V': 
                current_vaccinated += 1

        current_susceptible = self.number_of_agents - \
                              current_vaccinated - current_recovered - current_infections - current_exposed
        
        if self.log_time_period_data:
             logging.debug({"time_period": self.time_period,
                           "season": self.season,
                           "current_recovered": current_recovered,
                           "new_exposures": new_exposures,
                           "current_infections": current_infections,
                           "current_exposed": current_exposed,
                           "current_vaccinated": current_vaccinated,
                           "current_susceptible": current_susceptible,
                           "data_flag": 'infection'})

        if self.debug:
            logging.debug("institution exited run_basic_simulation")
    
    def end_season(self, season):
        """This helper function starts a new season """
        if self.debug:
            logging.debug(f"Institution: Entered end_season at the end of season {self.season}.")

        self.time_period = 0 #reset the time period to 0 for the next season

        if self.debug:
            logging.debug(f"Institution: Time period data at the end of season {self.season}: {self.time_period_data[self.season][-1]}")

        #TODO: delete this
        #put all the unvaccinated agents into a list
        #unvaccinated_list = [agent for agent in self.address_list if self.time_period_data[(self.season)-1][-1][f"{agent}"]['starting_state'] != 'V'] 

        #randomly pick ten agents to seed the infection for the next season
        seed_list = random.sample(self.agents, 10)

        #calculate the number of recovered and the number unvaccinated in each hub
        number_recovered = [0 for i in range(len(self.hub_densities))]
        number_unvaccinated = number_recovered.copy()

        for agent in self.agents:
            
            #TODO: delete
            #logging.debug(f"line 531: len(time_period_data) = {len(self.time_period_data)}, "
            #              f"season = {self.season}")

            if self.time_period_data[self.season][-1][f"{agent}"]['starting_state'] == 'R':
                number_recovered[agent.hub] += 1
            if self.time_period_data[self.season][-1][f"{agent}"]['starting_state'] != 'V':
                number_unvaccinated[agent.hub] += 1

        #calculate the probability of infection for each hub. that's the num recovered / num unvaccinated
        probabilities_of_infection = []
        for rec, unvac in zip(number_recovered, number_unvaccinated):
            if unvac == 0: 
                probabilities_of_infection.append(0) #if everyone is vaccinated, the prob of infection is 0
            else: 
                probabilities_of_infection.append(rec/unvac)
        
        for agent in self.agents:

            #if the agent finished the last season vaccinated, they start the new one vaccinated by default 
            if self.time_period_data[self.season][-1][f"{agent}"]['starting_state'] == 'V':
                new_season_state = 'V'
            
            else: #if the agent finished the last season unvaccinated, they will start Susceptible by default
                new_season_state = 'S'
            
            #next, we determine whether this agent will serve as a seed of the infection
            if agent in seed_list:
                seed = True
            else:
                seed = False

            #as long as there is still one more season left to run, notify agents of the new start 
            if self.season + 1 < self.number_of_seasons:
                #send a message to the agent notifying them with this information for the new season
                agent.new_season(seed, new_season_state, probabilities_of_infection)

        #log seasonal data for each hub
        for i in range(self.number_of_hubs):

            hub_dict =   {"hub": i,
                          "hub_size": self.hub_sizes[i],
                          "hub_density": self.hub_densities[i],
                          "recovered": number_recovered[i],
                          "unvaccinated": number_unvaccinated[i],
                          "season": self.season,
                          "transmission_rate": self.rate_of_infection_per_contact,
                          "homophily": self.degree_of_homophily,
                          "prob_vacc_choice": self.probability_vacc_choice,
                          "recovery_rate": self.recovery_rate,
                          "incubation_period": self.incubation_period,
                          "cost_of_infection": self.cost_of_infection,
                          "inst_unique_id"   : self.inst_unique_id,
                          "data_flag": 'seasonal_data'}

            with jsonlines.open('experiment_data.log', mode='a') as writer:
                writer.write(hub_dict)