"""
Environment Code, 
for initializing Agent-Based Sim

Programmer: Andrew Souther
Date: September 2020

"""


from mTree.microeconomic_system.environment import Environment
from mTree.microeconomic_system.directive_decorators import *
from mTree.microeconomic_system.message import Message
import logging
import random
from datetime import datetime

EXPERIMENT = 25

@directive_enabled_class
class BasicEnvironment(Environment):
    def __init__(self):
        self.number_of_agents = None #int, number of agents in the simulation
        self.rate_of_infection_per_contact = None #float, probability between 0 and 1 that you are infected if exposed
        self.incubation_period = None #int, on average, how many an agent stays exposed before becoming infectious
        self.recovery_rate = None #float, the probability that an infected agent will recover in a given time period
        self.address_list = [] #list, contains all the agent addresses for the institution
        self.total_time_infected = 0 #int, total time periods that all agents spent infected
        self.num_reported_agents = 0 #int, the number of agents who report their final status
        self.total_welfare = 0 #float, used to calculate total welfare among all agents
        self.env_unique_id = None #str, a unique_id for this environment
        self.number_of_hubs = None #int, number of "hubs" for matching agents into groups
        self.degree_of_homophily = None #float, probability (from 0-1) that an agent is matched with a neighbor from their own hub
        self.hub_densities = None #list, length equal to the number_of_hubs, containing density of each hub
        self.hub_sizes = None #list, length equal to number_of_hubs, total number of agents must equal to number_of_agents
        self.starting_vaccination_rate = None #float, the chance that an agent will start off the simualtion vaccinated
        self.cost_of_infection = None #float, some number between 0 or 1. the cost to an agent of getting vaccinated
        self.probability_vacc_choice = None #float, probability that an agent can get vaccinated at the start of a new season
        self.number_of_seasons = None #int, number of seasons to run the SEIR simulation, with vaccination decisions made each time
        self.log_time_period_data= None #bool, tells the institution whether or not to log SEIR data for each time period
        self.debug = False

    @directive_decorator("start_environment")
    def start_environment(self,message:Message):
        """
        This method retrieves all the simulation's variables from the config file, then initializes institution and agents.
        """
        if self.debug:
            logging.log(EXPERIMENT, "environment entered start_environment")

        self.number_of_agents = self.get_property("number_of_agents")
        self.rate_of_infection_per_contact = self.get_property("rate_of_infection_per_contact")
        self.recovery_rate = self.get_property("recovery_rate")
        self.incubation_period = self.get_property("incubation_period")
        self.number_of_hubs = self.get_property("number_of_hubs")
        self.degree_of_homophily = self.get_property("degree_of_homophily")
        self.hub_densities = self.get_property("hub_densities")
        self.hub_sizes = self.get_property("hub_sizes")
        self.starting_vaccination_rate = self.get_property("starting_vaccination_rate")
        self.cost_of_infection = self.get_property("cost_of_infection")
        self.probability_vacc_choice = self.get_property("probability_vacc_choice")
        self.number_of_seasons = self.get_property("number_of_seasons")
        self.log_time_period_data= self.get_property("log_time_period_data")
        self.env_unique_id = 'E' + str(datetime.now()) + str(random.randrange(0,100000000))

        #SANITY CHECK 1
        if (len(self.hub_sizes) != len(self.hub_densities)) or \
           (len(self.hub_sizes) != self.number_of_hubs) or \
           (len(self.hub_densities) != self.number_of_hubs):
           logging.log(EXPERIMENT, "ERROR: there is something wrong with the length of the hub lists")
        
        #SANITY CHECK 2
        alleged_number_of_agents = 0
        for number in self.hub_sizes:
            alleged_number_of_agents+=number
        if alleged_number_of_agents != self.number_of_agents:
            logging.log(EXPERIMENT, "ERROR: there is something wrong with the hub_sizes list or the number of agents")
           
        #initialize the list of agent addresses for the institution
        for agent in self.agents:
            self.address_list.append(agent[0])

        self.initialize_institution()
        self.initialize_agents()

        if self.debug:
            logging.log(EXPERIMENT, "environment exited start_environment, "
                                f"number_of_agents = {self.number_of_agents}, "
                                f"rate_of_infection_per_contact = {self.rate_of_infection_per_contact}, "
                                f"incubation_period = {self.incubation_period}",
                                f"number_of_hubs = {self.number_of_hubs}",
                                f"degree_of_homophily = {self.degree_of_homophily}")

    def initialize_institution(self):
        """
        Opens up the institution for the SIS simulation.
        """

        payload = {"number_of_agents": self.number_of_agents,
                   "rate_of_infection_per_contact": self.rate_of_infection_per_contact,
                   "address_list": self.address_list,
                   "recovery_rate": self.recovery_rate,
                   "number_of_hubs": self.number_of_hubs,
                   "degree_of_homophily": self.degree_of_homophily,
                   "hub_densities": self.hub_densities,
                   "hub_sizes": self.hub_sizes,
                   "probability_vacc_choice": self.probability_vacc_choice,
                   "number_of_seasons": self.number_of_seasons,
                   "log_time_period_data": self.log_time_period_data,
                   "incubation_period" : self.incubation_period,
                   "cost_of_infection": self.cost_of_infection,
                   "recovery_rate": self.recovery_rate}

        directive = 'init_institution'
        receiver = self.institutions[0]
        self.send_message(payload,directive,receiver)

    def initialize_agents(self):
        """
        Intializes all agents for the SIS simulation. Also determines whether each agent will start the simulation as
        Susceptible or Infected.
        """

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

            payload = {"number_of_agents": self.number_of_agents,
                       "rate_of_infection_per_contact": self.rate_of_infection_per_contact,
                       "incubation_period": self.incubation_period,
                       "recovery_rate": self.recovery_rate,
                       "current_state": current_state,
                       "institution_address": self.institutions[0],
                       "hub": current_hub,
                       "cost_of_infection": self.cost_of_infection}
            directive = 'init_agents'
            receiver = agent[0]
            self.send_message(payload, directive, receiver)

            #after notifying the agent of their hub, prepare to assign the next agent to the next hub
            if current_agent < self.hub_sizes[current_hub] - 1: #if this hub isn't full, keep going
                current_agent+=1
            elif current_agent == self.hub_sizes[current_hub] - 1: #if this hub is full, move to the next one
                current_hub+=1
                current_agent = 0

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
            logging.log(EXPERIMENT, f"message sent by environment, "
                                f"payload = {payload}, "
                                f"directive = {directive}, "
                                f"receiver = {receiver}")