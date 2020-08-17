# Calls MCTS in a loop, with periodic restarts
# Some information is passed over to future MCTS

from mcts import *
import copy

from action import Action, printActionSequence
from plot_cfg_tree import plot_cfg_tree
from plot_cfg_dag import plot_cfg_dag
import time, sys
from cfg import Word, Character, CFG

from sim_anneal import SimulatedAnnealing
from state import State

import rospy
import rospkg
import yaml


def mcts_sim_anneal_switching(cfg, budget, max_mcts_iterations, exploration_exploitation_parameter, max_sim_iterations, underwater_simulator, use_dag, config):


    num_rounds = 15
    iterations_per_round = 1000

    shortcut_words = []

    # cfg.grammar = cfg.generateGrammarGuidedStructureGroupsOneSequence()

    #cfg_shortcuts_only = CFG()
    #cfg_shortcuts_only.grammar = cfg_shortcuts_only.generateGrammarShortcutsOnly()

    # Initialize mcts_sa_output.txt
    f = open("mcts_sa_output.txt","w+")
    print(f.read())

    # Do the rounds
    for round in xrange(num_rounds):

        f.write("+++++++++++++++++++++++++\n")
        f.write("Results for round %d\n" % round)
        f.write("+++++++++++++++++++++++++\n")

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
        #if round in range(1):
        #if round in range(5): #do mcts first half, do sa second half (5 rounds each)
        if round in range(10) or round >= 10 and round%2==0: #ex. run mcts for first 5 rounds then SA/MCTS alternating i.e. mcts = (0,1,2,3,4,6,8), sa = (5,7,9)
        #if round%2==0 or len(shortcut_words) == 0: #alternating rounds
            f.write("MCTS...\n")
            print("Running MCTS round: ", round)
            cfg_copy = copy.deepcopy(cfg)
            shortcut_words_copy = copy.deepcopy(shortcut_words)
            [solution, best_rollout, root, list_of_all_nodes, winner, best_rollout_node, best_nodes_dict] = mcts( cfg_copy, budget, max_mcts_iterations, exploration_exploitation_parameter, max_sim_iterations, underwater_simulator, use_dag, config, shortcut_words_copy )
            f.write("Best rollout: ")
            f.write(best_rollout.toString())
            f.write("\n")

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
            # shortcut_words = [] # comment this out to keep the previous words
            subtree_words = []

            for best_node in best_nodes_dict.values():

                if best_node.average_evaluation_score > 0.0:

                    for best_rollout_active_word in best_node.best_rollout_active_words:
                        extracted_subtrees = extract_subtrees(best_rollout_active_word)
                        subtree_words.extend(extracted_subtrees)

                    # For each subtree of node
                    for subtree_word in subtree_words:

                        subtree_word_already_shortcut = False
                        for shortcut_word in shortcut_words:
                            if shortcut_word.equal(subtree_word):
                                subtree_word_already_shortcut = True
                                break

                        if not subtree_word_already_shortcut:

                            # Create a new production rule (done in mcts.py given shortcut_words)
                            shortcut_words.append(subtree_word)

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
            f.write("Shortcut words:\n")
            for word in shortcut_words:
                f.write(word.toString())
                f.write("\n")

        else:
            print("Running SA round: ", round)
            f.write("Simulated annealing...\n")
            initial_state_list = []
            initial_state = State(initial_state_list, shortcut_words)

            # Initialize state_list with best tree word, in list form, from mcts
            mcts_best_word = best_node.best_rollout_active_words[-1] #last best tree word
            initial_state.initial_state_list = initial_state.wordToList(mcts_best_word)

            initial_temperature = 1000
            k_max = 1000
            sim_anneal = SimulatedAnnealing(initial_state, initial_temperature, k_max, round)
            sim_anneal_best_word, score, sim_anneal_best_words, scores = sim_anneal.run()
            print("++++++++++++++++++++++")
            print("Sim anneal best words: " + str(sim_anneal_best_words) + "len = " + str(len(sim_anneal_best_words)))
            print("Associated scores: " + str(scores) + "len = " + str(len(scores)))
            print("++++++++++++++++++++++")
            f.write("Best word: ")
            f.write(sim_anneal_best_word.toString())
            f.write("\n")

            # Extract information to pass to the next round
            shortcut_words = [] # comment this out to keep the previous words
            subtree_words = []

            for i in range(len(sim_anneal_best_words)):
                sa_best_word = sim_anneal_best_words[i]
                score = scores[i]

                if score > 0.0:
                    
                    extracted_subtrees = extract_subtrees(sa_best_word)
                    subtree_words.extend(extracted_subtrees)

                    # For each subtree of node
                    for subtree_word in subtree_words:

                        subtree_word_already_shortcut = False
                        for shortcut_word in shortcut_words:
                            if shortcut_word.equal(subtree_word):
                                subtree_word_already_shortcut = True
                                break

                        if not subtree_word_already_shortcut:

                            # Create a new production rule (done in mcts.py given shortcut_words)
                            shortcut_words.append(subtree_word)

            f.write("Shortcut words:\n")
            for word in shortcut_words:
                f.write(word.toString())
                f.write("\n")
        
        

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

        
    f.close()
    return [solution, best_rollout, root, list_of_all_nodes, winner, best_rollout_node, best_nodes_dict, sim_anneal_best_word]
