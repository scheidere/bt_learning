#!/usr/bin/env python
'''
Basic MCTS implementation
Graeme Best
Oregon State University
Jan 2020
'''

from mcts import mcts
from mcts_restarts import mcts_restarts
from mcts_restarts_with_simulated_annealing import mcts_sim_anneal_switching
from action import Action, printActionSequence
from tree_node import countNodes
# from plot_tree import plotTree
from plot_cfg_tree import plot_cfg_tree
from plot_cfg_dag import plot_cfg_dag
import time, sys
from cfg import Word, Character, CFG

import rospy
import rospkg
import yaml

import cProfile
import pstats

from simulator.run_simulator import UnderwaterSimulator

import time


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
    use_dag = config["use_dag"]
    
    #[solution, best_rollout, root, list_of_all_nodes, winner, best_rollout_node, best_nodes_dict] = mcts_restarts( cfg, budget, max_mcts_iterations, exploration_exploitation_parameter, max_sim_iterations, underwater_simulator, use_dag, config )    
    final_best_word, final_best_word_score = mcts_sim_anneal_switching( cfg, budget, max_mcts_iterations, exploration_exploitation_parameter, max_sim_iterations, underwater_simulator, use_dag, config )    

    # Display the tree
    ###printActionSequence(solution) #this is not set up for words instead of sequences for actions
    
    print('Final best word:')
    if final_best_word:
        final_best_word.printWord()
    else:
        print(final_best_word) #should be None in this case (to account for when no trees have score > 0 in a round)

    '''
    print('sequence at best node:')
    for soln in solution:
        soln.printWord()
    
    print('best_rollout at best node:')
    best_rollout.printWord()

    print('best_rollout_active_words at best node:')
    for best_rollout_active_word in winner.best_rollout_active_words:
        best_rollout_active_word.printWord()

    print('sequence at best_rollout_node:')
    for soln in best_rollout_node.sequence:
        soln.printWord()

    print('best_rollout at best_rollout_node:')    
    best_rollout_node.best_rollout.printWord()

    print('best_rollout_active_words at best_rollout_node:')
    for best_rollout_active_word in best_rollout_node.best_rollout_active_words:
        best_rollout_active_word.printWord()
    '''

    # OLD plotting function -- does not work for these cfg trees
    #plotTree(list_of_all_nodes, winner, action_set, False, budget, 1, exploration_exploitation_parameter)
    #plotTree(list_of_all_nodes, winner, action_set, True, budget, 2, exploration_exploitation_parameter)
    plot_search_tree = config["plot_search_tree"]
    if plot_search_tree:

        # new plotting function
        use_uct = False # True case doesn't currently work
        max_height = 1000
        # plot_cfg_tree(list_of_all_nodes, winner, use_uct, max_height, exploration_exploitation_parameter)

        print_text = False
        filename='dag.gv'
        plot_cfg_dag(list_of_all_nodes, winner, use_uct, max_height, exploration_exploitation_parameter, print_text, filename)

        print_text = True
        filename='dag_text.gv'
        plot_cfg_dag(list_of_all_nodes, winner, use_uct, max_height, exploration_exploitation_parameter, print_text, filename)

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
    start_time = time.time()
    run()
    total_time = time.time() - start_time
    print("RUNTIME: --- %s seconds ---" % (total_time))
    print("RUNTIME: --- %s minutes ---" % str((total_time)/60.0))
    print("RUNTIME: --- %s hours ---" % str((total_time)/360.0))
    # run_profiler()
    
    
