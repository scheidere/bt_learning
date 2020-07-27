#!/usr/bin/env python
# Calls mcts for one round, given the even round subtree-combining production rules

from mcts import *
import copy

from action import Action, printActionSequence
from plot_cfg_tree import plot_cfg_tree
from plot_cfg_dag import plot_cfg_dag
import time, sys
from cfg import Word, Character, CFG, createWord

import rospy
import rospkg
import yaml

from tree_node import countNodes

import cProfile
import pstats

from run_simulator import UnderwaterSimulator

def mcts_subtree_combo_round(cfg, budget, max_mcts_iterations, exploration_exploitation_parameter, max_sim_iterations, underwater_simulator, use_dag, config):
    
    iterations_per_round = 1000

    manual_subtree_report = createWord('-> ( (wildlife_found) ? ( (in_comms) [go_to_comms] ) [report] )')
    manual_subtree_disarm = createWord('-> ( (mine_found) ? ( <!> ( (is_armed) ) [disarm] ) )')
    manual_subtree_pickplace = createWord('-> ( ? ( <!> ( (carrying_benign) ) [take_to_drop_off] ) (benign_found) [pick_up] )')
    manual_subtree_likelytarget = createWord('-> ( (likely_target_found) [go_to_likely_target] )')
    manual_subtree_randomwalk = createWord('-> ( [random_walk] )')
    shortcut_words = [manual_subtree_report, manual_subtree_disarm, manual_subtree_pickplace, manual_subtree_likelytarget, manual_subtree_randomwalk]

    cfg.grammar = cfg.generateGrammarShortcutsOnly()

    [solution, best_rollout, root, list_of_all_nodes, winner, best_rollout_node, best_nodes_dict] = mcts( cfg, budget, max_mcts_iterations, exploration_exploitation_parameter, max_sim_iterations, underwater_simulator, use_dag, config, shortcut_words)

    # Print all shortcut words
    print("All shortcut words:")
    for word in shortcut_words:
        word.printWord()

    return [solution, best_rollout, root, list_of_all_nodes, winner, best_rollout_node, best_nodes_dict]


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
    
    [solution, best_rollout, root, list_of_all_nodes, winner, best_rollout_node, best_nodes_dict] = mcts_subtree_combo_round( cfg, budget, max_mcts_iterations, exploration_exploitation_parameter, max_sim_iterations, underwater_simulator, use_dag, config )
    

    # Display the tree
    ###printActionSequence(solution) #this is not set up for words instead of sequences for actions
    
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
    

if __name__ == "__main__":
    run()

