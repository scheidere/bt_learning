#!/usr/bin/env python

import numpy as np 
from state import Neighbors
from simulator.run_simulator import UnderwaterSimulator
from cfg import createWord
from state import State


import random
import math

import rospy

import sys

class SimulatedAnnealing():
    def __init__(self, initial_state, initial_temperature, k_max):
        self.initial_state = initial_state
        self.initial_state_list = self.initial_state.state_list
        self.known_subtree_words = self.initial_state.known_subtree_words
        self.initial_temperature = initial_temperature
        self.k_max = k_max

        self.tiny_num = 0.001

    def temperature(self, k): #needs to take in (k-1)/k_max
        # temp should start at max t and end at 0
        # need to scale it
        # CHANGE this to fix scale

        if k == 0:
            self.T = self.initial_temperature
        else:
            step = (float(k) + 1.0)/self.k_max
            #if step == 0: #kept getting an error b/c small numbers round to 0
            #    step = self.tiny_num
            self.T -= step
        return self.T

    def energy(self, state):
        '''
        Goal function: lower energy is better
        Generate reward using simulator, reverse sign b/c lower energy is better
        '''
        #print('state',state)
        state_word = state.stateToFulltreeWord()        

        # Check if tree is empty
        if state_word == None:
            return 0

        sim = UnderwaterSimulator()
        score, target_reported, belief_distance, active_word = sim.generateReward(state_word, 200)  
        print("Score: " + str(score))
        return -score

    def probability(self, current_state, neighbor_state, temperature):
        '''
        Acceptance probability function:
        Probability of moving to new state given current state
        '''
        print("Generate current state energy")
        energy_current = self.energy(current_state)
        print("Generate neighbor state energy")
        energy_neighbor = self.energy(neighbor_state)

        if energy_neighbor < energy_current:
            # New state is better, so pick it always
            return 1
        else:
            return math.exp(-(energy_neighbor - energy_current)/temperature)


    def run(self):


        print("running simulated annealing...")
        self.current_state = self.initial_state

        for k in range(k_max):

            if rospy.is_shutdown(): 
                # Return solution before closing
                break
            
            print('Iteration: ' + str(k))

            # Get temperature
            self.T = self.temperature(k)
            print('T: ' + str(self.T))

            # Generate neighbors of current state
            neighbors = Neighbors(self.current_state)
            list_of_neighbor_lists = neighbors.getAllNeighbors() # List of lists

            # Pick a random neighbor
            neighbor_list = random.choice(list_of_neighbor_lists)
            self.neighbor_state = State(neighbor_list, self.known_subtree_words)

            # Calculate probability of picking neighbor state
            P = self.probability(self.current_state, self.neighbor_state, self.T)
            print("Probability: " + str(P))

            # Determine which state to pick, based on P
            if P >= random.random():
                print("Picking neighbor state...")
                self.current_state = self.neighbor_state

            #CHANGE: retain best solution and return that when you quit always

        print("finished simulated annealing...")
        print("Final state: " + self.current_state.state_list)
        print("Final state word: " + self.current_state.stateToFulltreeWord())
        return self.current_state
        
                




if __name__ == "__main__":

    rospy.init_node("sim_anneal")

    # Initialize
    manual_subtree_report = createWord('-> ( (wildlife_found) ? ( (in_comms) [go_to_comms] ) [report] )')
    manual_subtree_disarm = createWord('-> ( (mine_found) ? ( <!> ( (is_armed) ) [disarm] ) )')
    manual_subtree_pickplace = createWord('-> ( ? ( <!> ( (carrying_benign) ) [take_to_drop_off] ) (benign_found) [pick_up] )')
    manual_subtree_likelytarget = createWord('-> ( (likely_target_found) [go_to_likely_target] )')
    manual_subtree_randomwalk = createWord('-> ( [random_walk] )')
    #known_subtree_words = [manual_subtree_report, manual_subtree_disarm, manual_subtree_pickplace, manual_subtree_likelytarget, manual_subtree_randomwalk]
    known_subtree_words = [manual_subtree_disarm, manual_subtree_randomwalk]
    initial_state_list = []
    initial_state = State(initial_state_list, known_subtree_words)
    initial_temperature = 1000
    k_max = 1000

    simulated_annealing = SimulatedAnnealing(initial_state, initial_temperature, k_max)

    simulated_annealing.run()