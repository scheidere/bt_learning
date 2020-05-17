# Calls MCTS in a loop, with periodic restarts
# Some information is passed over to future MCTS

from mcts import *
import copy

from action import Action, printActionSequence
from plot_cfg_tree import plot_cfg_tree
from plot_cfg_dag import plot_cfg_dag
import time, sys
from cfg import Word, Character, CFG

import rospy
import rospkg
import yaml

def mcts_restarts(cfg, budget, max_mcts_iterations, exploration_exploitation_parameter, max_sim_iterations, underwater_simulator, use_dag, config):


    num_rounds = 10
    iterations_per_round = 1000

    shortcut_words = []

    cfg_shortcuts_only = CFG()
    cfg_shortcuts_only.generateGrammarShortcutsOnly()

    # Do the rounds
    for round in xrange(num_rounds):

        print("====================================")
        print("====================================")
        print("====================================")
        print("====================================")
        print("round", round)
        print("====================================")
        print("====================================")
        print("====================================")
        print("====================================")

        if rospy.is_shutdown():
            break

        max_mcts_iterations = iterations_per_round
        if round%2==0 or len(shortcut_words) == 0:
            cfg_copy = copy.deepcopy(cfg)
        else:
            cfg_copy = copy.deepcopy(cfg_shortcuts_only)
        shortcut_words_copy = copy.deepcopy(shortcut_words)
        
        [solution, best_rollout, root, list_of_all_nodes, winner, best_rollout_node, best_nodes_dict] = mcts( cfg_copy, budget, max_mcts_iterations, exploration_exploitation_parameter, max_sim_iterations, underwater_simulator, use_dag, config, shortcut_words_copy )
        

        # Print results
        
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

        # Extract information to pass to the next round
        shortcut_words = [] # comment this out to keep the previous words
        subtree_words = []
        for best_node in best_nodes_dict.values():

            if best_node.average_evaluation_score > 0.0:
                
                for best_rollout_active_word in best_node.best_rollout_active_words:
                    subtree_words.extend(extract_subtrees(best_rollout_active_word))

                # For each subtree of node
                for subtree_word in subtree_words:

                    subtree_word_already_shortcut = False
                    for shortcut_word in shortcut_words:
                        if shortcut_word.equal(subtree_word):
                            subtree_word_already_shortcut = True
                            break

                    if not subtree_word_already_shortcut:

                        # Create a new production rule
                        shortcut_words.append(subtree_word)
                        input_word = createWord("sequence")
                        output_word = subtree_word
                        production_rule = ProductionRule(input_word, output_word)

        '''
        if best_rollout_node.average_evaluation_score > 0.0:
            subtree_words = []
            for best_rollout_active_word in best_rollout_node.best_rollout_active_words:
                subtree_words.extend(extract_subtrees(best_rollout_active_word))

            # For each subtree of node
            for subtree_word in subtree_words:

                subtree_word_already_shortcut = False
                for shortcut_word in shortcut_words:
                    if shortcut_word.equal(subtree_word):
                        subtree_word_already_shortcut = True
                        break

                if not subtree_word_already_shortcut:

                    # Create a new production rule
                    shortcut_words.append(subtree_word)
                    input_word = createWord("sequence")
                    output_word = subtree_word
                    production_rule = ProductionRule(input_word, output_word)
        '''

        # Print all shortcut words
        print("All shortcut words:")
        for word in shortcut_words:
            word.printWord()

        # Plot it
        plot_search_tree = config["plot_search_tree"]
        if plot_search_tree:

            # new plotting function
            use_uct = False # True case doesn't currently work
            max_height = 1000
            # plot_cfg_tree(list_of_all_nodes, winner, use_uct, max_height, exploration_exploitation_parameter)

            print_text = False
            filename='dag' + str(round) + '.gv'
            plot_cfg_dag(list_of_all_nodes, winner, use_uct, max_height, exploration_exploitation_parameter, print_text, filename)

            print_text = True
            filename='dag_text' + str(round) + '.gv'
            plot_cfg_dag(list_of_all_nodes, winner, use_uct, max_height, exploration_exploitation_parameter, print_text, filename)

            '''
            # Wait for Ctrl+C
            while True:
                if rospy.is_shutdown():
                    break
                time.sleep(.1)
            '''

    return [solution, best_rollout, root, list_of_all_nodes, winner, best_rollout_node, best_nodes_dict]