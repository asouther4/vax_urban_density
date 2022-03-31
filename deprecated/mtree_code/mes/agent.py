"""
Agent Code for an SEIR Simulation,
featuring endogenous vaccine decisions

Programmer: Andrew Souther
Date: December 2020

"""

from mTree.microeconomic_system.directive_decorators import *
from mTree.microeconomic_system.message import Message
from mTree.microeconomic_system.agent import Agent
import logging
import random
from datetime import datetime
import math
from sympy import symbols, Eq, solve

EXPERIMENT = 25


@directive_enabled_class
class BasicAgent(Agent):
    def __init__(self):
        self.susceptible = None #boolean, if True, the agent is Susceptible to disease.
                                         #if False, the agent is currently Infected. #TODO: delete susceptible, replace with "state"
        self.institution_address = None #mTree address object for the institution
        self.environment_address = None #mTree address object for the environment
        self.number_of_agents = None #int, number of agents in the simulation
        self.rate_of_infection_per_contact = None #float, probability between 0 and 1 that you are infected if exposed
        self.time_infected = 0 #int, keeps count of how much time an agent has spent infected
        self.time_exposed = 0 #int, keeps count of how long an agent spent exposed (before transitioning to infectious)
        self.incubation_period = None #int, on average, how many an agent stays exposed before becoming infectious
        self.recovery_rate = None #float, the probability that an infected agent will recover in a given time period
        self.current_state = None #string, either 'S' for Susceptible, 'E' for exposed, 'In' for infected, 'R' for recovered, 'V' for vaccinated
        self.unique_id = None #str, a unique_id for this agent
        self.hub = None #int, keeps track of what hub this agent belongs to
        self.cost_of_infection = None #float, some number between 0 or 1. the cost to an agent of getting vaccinated
        self.debug = False

    @directive_decorator("init_agents")
    def init_agents(self, message:Message):
        """
        Receives the initial state of the agent from the environment,
        either susceptible or infected.
        """
        if self.debug:
            logging.log(EXPERIMENT, f'agent {self.unique_id} entered init_agents')
        
        #save the agent's current SIS state from the environment, plus the institution's address
        self.current_state = message.get_payload()["current_state"]
        self.hub = message.get_payload()["hub"]
        self.institution_address = message.get_payload()["institution_address"]
        self.environment_address = message.get_sender().myAddress

        #save data about the SEIR simulation
        self.number_of_agents = message.get_payload()["number_of_agents"]
        self.rate_of_infection_per_contact = message.get_payload()["rate_of_infection_per_contact"]
        self.recovery_rate = message.get_payload()["recovery_rate"]
        self.incubation_period = message.get_payload()["incubation_period"]
        self.cost_of_infection = message.get_payload()["cost_of_infection"]

        #create a unique_id for this agent
        self.unique_id = 'A' + str(datetime.now()) + str(random.randrange(0,100000000))

        #register with the matching institution for the first time
        self.start_registration()

        if self.debug:
            logging.log(EXPERIMENT, f'agent {self.unique_id} exited init_agents')
    
    @directive_decorator("notify")
    def notify(self, message:Message):
        """
        In this method, the agent receives information about the previous round from the institution, 
        and it keeps track of its own S/I status. 
        """

        if self.debug:
            logging.log(EXPERIMENT, f'agent {self.unique_id} entered notify')
        
        #keep count of how many time periods each agent has spent infected
        if self.current_state == 'In':
            self.time_infected += 1

            #also check whether the agent randomly recovers (with probability equal to self.recovery_rate)
            recovery_lottery = random.random()
            if recovery_lottery <= self.recovery_rate:
                if self.debug:
                    logging.log(EXPERIMENT, f"Agent {self.unique_id} has recovered after spending {self.time_infected} time periods infected!")
                self.current_state = 'R'

        elif self.current_state == 'Ex':
            self.time_exposed +=1
            #check whether the agent will randomly transition from Exposed to Infected
            incubation_lottery = random.random()
            transition_rate = (1 / self.incubation_period) #the probability of transition is 1/incubation_period
            if incubation_lottery <= transition_rate:
                if self.debug:
                    logging.log(EXPERIMENT, f"Agent {self.unique_id} has become infectious after spending {self.time_exposed} time periods infected!")
                self.current_state = 'In'

        #learn from the institution whether this agent was exposed during the matching process
        exposed = message.get_payload()["exposed"]
        
        #TEST: only a Susceptible agent can be infected
        if (exposed == True) and (self.current_state != 'S'): 
            self.error_log(f"A non-Susceptible agent has been exposed, current_state = {self.current_state}")

        #change the agent's current state to exposed before the next round
        if exposed == True:  
            self.current_state = 'Ex'

        #register with the insitution again. The institution will figure out whether/how the simulation should proceed
        self.start_registration()

        if self.debug:
            logging.log(EXPERIMENT, f'agent {self.unique_id} exited notify')
    
    @directive_decorator("new_season")
    def new_season(self, message:Message):
        """
        Receives information about the start of the new epidemic season, whenever a new season starts. 
        """

        if self.debug:
            logging.log(EXPERIMENT, f'agent {self.unique_id} entered new_season')

        choice = message.get_payload()["choice"]
        seed = message.get_payload()["seed"]
        new_season_state = message.get_payload()["new_season_state"]
        prob_of_infection = message.get_payload()["prob_of_infection"]

        #agents who were vaccinated in the previous season should remain vaccinated
        if self.current_state == 'V' and new_season_state != 'V':
            logging.log(EXPERIMENT, f"ERROR: Agent {self.unique_id} somehow lost vaccination at the beginning of a new season")

        #update your current state for the new season
        self.current_state = new_season_state

        #if the agent was offered a choice, decide whether or not to get vaccinated
        if choice:
            if prob_of_infection >= (1/self.cost_of_infection): #get vaccinated if the probability of infection is high in your region
                self.current_state = 'V'
            else: #if the probability of infection is not so high, start the season susceptible
                self.current_state = 'S'
        

        #finally, consider whether this agent is a seed of the infection
        if seed:
            if self.current_state != 'V': #if a seed agent is not vaccinated, they start the season Infected
                self.current_state = 'In'

        if self.debug:
            logging.log(EXPERIMENT, f"Agent {self.unique_id} is facing a prob_of_infection of {prob_of_infection} "
                                    f"in hub {self.hub}, along with a cost_of_infection of {self.cost_of_infection}.")

        #register with the insitution again. The institution will figure out whether/how the simulation should proceed
        self.start_registration()

        if self.debug:
            logging.log(EXPERIMENT, f'agent {self.unique_id} exited new_season')


    def start_registration(self):
        """
        This simple helper function starts registrtion with the SEIR matching institution.
        """
        #send a registration message to the institution
        payload = {"current_state": self.current_state,
                   "hub": self.hub}
        directive = 'register'
        receiver = self.institution_address
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
            logging.log(EXPERIMENT, f"message sent by agent {self.unique_id}, "
                                f"payload = {payload}, "
                                f"directive = {directive}, "
                                f"receiver = {receiver}")
    
    def error_log(self, string):
        """
        This helper function builds an error logging statement with a uniform structure. 
        As an input, it accepts a string with some kind of specialized message for the log. 
        """
        logging.log(EXPERIMENT, "ERROR: " + string + f"unique_id = {self.unique_id}") 