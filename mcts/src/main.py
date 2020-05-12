#!/usr/bin/env python
'''
Basic MCTS implementation
Graeme Best
Oregon State University
Jan 2020
'''

from mcts import mcts
from action import Action, printActionSequence
from tree_node import countNodes
# from plot_tree import plotTree
from plot_cfg_tree import plot_cfg_tree
import time, sys
from cfg import Word, Character, CFG

import rospy
import rospkg
import yaml

import cProfile
import pstats

from run_simulator import UnderwaterSimulator


def run():

    rospy.init_node('mcts')

    # Create CFG object
    cfg = CFG()

    '''
    # Setup the problem
    num_actions = 3
    action_set = []
    for i in range(num_actions):
        id = i
        action_set.append(Action(id,i))
    '''

    # Create a simulator
    underwater_simulator = UnderwaterSimulator()
    
    # Get the config file etc
    rospack = rospkg.RosPack()
    filepath = rospack.get_path('mcts') + "/config/" + rospy.get_param('~config')
    with open(filepath, 'r') as stream:
        config = yaml.safe_load(stream)
    #budget = rospy.get_param('~budget')???
    budget = config["budget"]

    exploration_exploitation_parameter = config["exploration_exploitation_parameter"]
    max_mcts_iterations = config["max_mcts_iterations"]
    max_sim_iterations = config["max_sim_iterations"]
    
    '''
    budget = 8
    

    # Solve it with MCTS
    exploration_exploitation_parameter = 1.0 # =1.0 is recommended. <1.0 more exploitation. >1.0 more exploration. 
    max_mcts_iterations = 10000 #change name to max_mcts_iterations ##you change this to make it run longer
    max_sim_iterations = 100 #iterations robot allows to move for before it gives up
    '''
    [solution, best_rollout, root, list_of_all_nodes, winner] = mcts( cfg, budget, max_mcts_iterations, exploration_exploitation_parameter, max_sim_iterations, underwater_simulator, config )
    

    # Display the tree
    ###printActionSequence(solution) #this is not set up for words instead of sequences for actions
    
    print('sequence at best node:')
    for soln in solution:
        soln.printWord()
    
    print('best_rollout at best node:')
    best_rollout.printWord()

    # OLD plotting function -- does not work for these cfg trees
    #plotTree(list_of_all_nodes, winner, action_set, False, budget, 1, exploration_exploitation_parameter)
    #plotTree(list_of_all_nodes, winner, action_set, True, budget, 2, exploration_exploitation_parameter)
    plot_search_tree = config["plot_search_tree"]
    if plot_search_tree:

        # new plotting function
        use_uct = False # True case doesn't currently work
        max_height = 4
        plot_cfg_tree(list_of_all_nodes, winner, use_uct, max_height, exploration_exploitation_parameter)

        # Wait for Ctrl+C
        while True:
            try:
                time.sleep(.1)
            except KeyboardInterrupt:
                sys.exit()
    


def run_profiler():
    cProfile.run('run()', 'profile_stats')
    p = pstats.Stats('profile_stats')
    p.sort_stats("cumulative").print_stats(50)

if __name__ == "__main__":
    run()
    # run_profiler()
    
    
