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

import matplotlib.pyplot as plt

import time

class SimulatedAnnealing():
    def __init__(self, initial_state, initial_temperature, k_max, round_num):
        self.initial_state = initial_state
        self.initial_state_list = self.initial_state.state_list
        self.known_subtree_words = self.initial_state.known_subtree_words
        self.initial_temperature = initial_temperature
        self.k_max = k_max
        self.round_num = round_num #for plotting

        self.best_state = initial_state #initially
        self.best_score = -self.energy(self.best_state)
        self.probabilities = [] #for plotting
        self.iterations = [] #for plotting
        self.best_scores = []
        self.scores = []
        self.avg_scores = []
        self.stagnant_best_score_count = 0
        self.super_stagnant_best_score_count = 0
        self.best_state_updated = True


        # Create a single instance of the simulator so that you do not continuously recreate the world
        # To randomize targets, go to parameters.yaml in simulator
        self.underwater_simulator = UnderwaterSimulator()

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
            self.T = -self.initial_temperature*step + self.initial_temperature
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

        self.score, target_reported, belief_distance, active_word, active_subtree_indices = self.underwater_simulator.generateReward(state_word, 200)  
        print("Score: " + str(self.score))
        print("active_word: ")
        active_word.printWord()
        #active_chars_pre = active_word.list
        #print(active_chars_pre)

        print('active_subtree_indices: ' + str(active_subtree_indices))
        print('Pre-update state list: ' + str(state.state_list))
        # Prune inactive subtrees, updating current state
        state.activeIndicesToNewState(active_subtree_indices)
        print('Updated state list, after pruning: ' + str(state.state_list))

        # If the score is zero, the order might just be wrong
        # Remove the inactive subtrees to allow for neighbors to be added potentially in the correct order
        #if score == 0:
        #    self.state_list = state.subtreeWordToNum()

        print("Best Score: " + str(self.best_score))
        if self.score > self.best_score:
            self.best_state = state #this might be wrong, not giving correct num at end
            self.best_score = self.score
            self.best_state_updated = True
        else:
            self.best_state_updated = False

        return -self.score

    def probability(self, current_state, neighbor_state, temperature):
        '''
        Acceptance probability function:
        Probability of moving to new state given current state
        '''
        print("Generate current state energy")
        energy_current = self.energy(current_state)
        print("current energy: ", energy_current)
        print("Generate neighbor state energy")
        energy_neighbor = self.energy(neighbor_state)
        print("neighbor energy: ", energy_neighbor)

        if energy_neighbor < energy_current:
            # New state is better, so pick it always
            return 1
        else:
            if temperature == 0:
                temperature = 0.001
            P = math.exp(-(energy_neighbor - energy_current)/temperature)
            print("In function P: ", P)
    
        return P

    def findInactiveSubtrees(self, state):

        pass

    def run(self):

        avg_score = 0

        print("Running simulated annealing...")
        self.current_state = self.initial_state

        '''
        # Plot method that should work based on: https://stackoverflow.com/questions/12822762/pylab-ion-in-python-2-matplotlib-1-1-1-and-updating-of-the-plot-while-the-pro/12826273
        # but doesn't because I need to suffer :D
        fig = plt.figure()
        ax = fig.add_subplot(111)
        h1, = ax.plot(self.probabilities)
        ax.set_xlim([0,self.k_max])
        plt.ion()
        #plt.show()
        '''

        # Slow way that works
        #plt.ion()

        # MCTS way that should work
        fig = plt.figure(100+self.round_num)
        plt.clf()
        ax = fig.add_subplot(111)
        first_plot = True
        fig2 = plt.figure(101+self.round_num)
        plt.clf()
        ax2 = fig2.add_subplot(111)

        for k in range(self.k_max):

            if rospy.is_shutdown(): 
                # Return solution before closing
                break

            print("+++++++++++++++++++++++++++")
            print('Iteration: ' + str(k))

            # Get temperature
            self.T = self.temperature(k)
            print('T: ' + str(self.T))
            print("+++++++++++++++++++++++++++")

            # Generate neighbors of current state
            neighbors = Neighbors(self.current_state)
            list_of_neighbor_lists = neighbors.getAllNeighbors() # List of lists
            print('Current state list: ', self.current_state.state_list)
            print('Neighbors: ', list_of_neighbor_lists)

            # Pick a random neighbor
            neighbor_list = random.choice(list_of_neighbor_lists)
            #print('Neighbor: ', neighbor_list)
            self.neighbor_state = State(neighbor_list, self.known_subtree_words)

            # Calculate probability of picking neighbor state
            P = self.probability(self.current_state, self.neighbor_state, self.T)
            print("Probability: " + str(P))
            self.probabilities.append(P)
            print(self.probabilities)

            self.best_scores.append(self.best_score)

            self.scores.append(self.score)

            avg_score = float(avg_score*len(self.scores)+self.score) / float(len(self.scores) + 1)
            # avg_rollout_rewards.append(sum(rollout_rewards)/len(rollout_rewards))
            self.avg_scores.append(avg_score)
            
            
            self.best_state_word = self.best_state.stateToFulltreeWord()
            #plot score
            if first_plot:
                first_plot = False

                # Probability plot
                plt.figure(100+self.round_num)
                line1, = ax.plot(range(k+1),self.probabilities,label = 'probability')
                plt.xlabel('SA Iterations')
                plt.ylabel('Probability')
                plt.legend(loc='best')
                plt.show(block=False)

                # Score plot
                plt.figure(101+self.round_num)
                line21, = ax2.plot(range(k+1),self.best_scores,label = 'best reward') #plot
                line22, = ax2.plot(range(k+1),self.avg_scores,label = 'average reward')
                line23, = ax2.plot(range(k+1),self.scores,label = 'current reward')
                plt.xlabel('SA Iterations')
                plt.ylabel('Score')
                title_string = ""
                if self.best_state_word: # as long as word is not None
                    title_string = self.best_state_word.toString()
                fig_text = fig2.text(0.5, 0.9, title_string, ha='center',wrap=True)
                
                plt.legend(loc='best')
                plt.show(block=False)
                
            else:

                # Probability plot
                plt.figure(100+self.round_num)
                line1.set_xdata(range(k+1))
                line1.set_ydata(self.probabilities)
                plt.xlim(0,k+1)
                plt.ylim(0,1.1)

                fig.canvas.draw()
                fig.canvas.flush_events()

                # Score plot
                plt.figure(101+self.round_num)
                line21.set_xdata(range(k+1))
                line22.set_xdata(range(k+1))
                line23.set_xdata(range(k+1))
                line21.set_ydata(self.best_scores)
                line22.set_ydata(self.avg_scores)
                line23.set_ydata(self.scores)
                plt.xlim(0,k+1)
                plt.ylim(0,self.best_scores[-1]*1.1)
                title_string = ""
                if self.best_state_word: # as long as word is not None
                    title_string = self.best_state_word.toString()
                fig_text.set_text(title_string)

                fig2.canvas.draw()
                fig2.canvas.flush_events()
                
            

            # Slow way that works
            '''
            plt.clf()
            plt.plot(range(len(self.probabilities)),self.probabilities)
            plt.pause(0.1)
            '''

            '''
            h1.set_ydata(self.probabilities)
            print(h1.get_ydata())
            h1.set_xdata(range(len(self.probabilities)))
            print(h1.get_xdata())
            plt.pause(1)
            '''

            # these are not needed if you use plt.ion()
            #plt.draw()
            #plt.show(block=False)
            
            #ax.plot(range(len(self.probabilities)),self.probabilities,label = 'Probability')
            #plt.show()
            #plt.pause(3)
            #plt.draw()

            # See if we are stuck, and reset to best if so
            if self.best_score > 0 and self.is_stagnant():
                self.current_state = self.best_state
            # If we are not stuck, determine which state to pick, based on P
            elif P >= random.random():
                print("Picking neighbor state...")
                self.current_state = self.neighbor_state
            # Otherwise the current state stays the same

            '''
            # Commenting out because when SA is killed it replaces shortcut_words with only the ones in its current tree
            # This removes good subtrees too often from the shortcut_words list that the MCTS rounds learn
            if self.is_super_stagnant():
                break #no point continuing if subtrees sucking is stopping it from being productive
            '''

        print("Finished simulated annealing...")
        print("Best state list: " + str(self.best_state.state_list))
        #self.best_state_word = self.best_state.stateToFulltreeWord()
        print("Best state word: ")
        self.best_state_word.printWord()
        print("Best state score: " + str(self.best_score))
        #print("Plot probability")
        #fig = plt.figure()
        #ax = fig.add_subplot(111)
        #line1, = ax.plot(range(len(self.probabilities)+1),self.probabilities,label = 'Probability')
        return self.best_state.stateToFulltreeWord(), self.best_score #return best word 

    def is_stagnant(self):

        if not self.best_state_updated: #self.best_scores[-1] == self.best_scores[-2]:
            self.stagnant_best_score_count += 1

        else:
            self.stagnant_best_score_count = 0

        if self.stagnant_best_score_count >= 20:
            print('Resetting current state to best state due to stagnance')
            self.stagnant_best_score_count = 0
            return True

        return False

    def is_super_stagnant(self):

        if not self.best_state_updated: #self.best_scores[-1] == self.best_scores[-2]:
            self.super_stagnant_best_score_count += 1

        else:
            self.super_stagnant_best_score_count = 0

        if self.super_stagnant_best_score_count >= 200:
            print('Stopping due to lack of progress')
            self.super_stagnant_best_score_count = 0
            return True

        return False



if __name__ == "__main__":

    rospy.init_node("sim_anneal")

    # Initialize
    manual_subtree_report = createWord('-> ( (wildlife_found) ? ( (in_comms) [go_to_comms] ) [report] )')
    manual_subtree_disarm = createWord('-> ( (mine_found) ? ( <!> ( (is_armed) ) [disarm] ) )')
    manual_subtree_pickplace = createWord('-> ( ? ( <!> ( (carrying_benign) ) [take_to_drop_off] ) (benign_found) [pick_up] )')
    manual_subtree_likelytarget = createWord('-> ( (likely_target_found) [go_to_likely_target] )')
    manual_subtree_randomwalk = createWord('-> ( [random_walk] )')
    known_subtree_words = [manual_subtree_report, manual_subtree_disarm, manual_subtree_pickplace, manual_subtree_likelytarget, manual_subtree_randomwalk]
    ##known_subtree_words = [manual_subtree_disarm, manual_subtree_randomwalk]
    initial_state_list = []
    initial_state = State(initial_state_list, known_subtree_words)
    initial_temperature = 10
    k_max = 1000
    round_num = 0

    simulated_annealing = SimulatedAnnealing(initial_state, initial_temperature, k_max, round_num)

    simulated_annealing.run()

    probs = simulated_annealing.probabilities
