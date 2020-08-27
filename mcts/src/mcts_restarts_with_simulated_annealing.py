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

import time


def mcts_sim_anneal_switching(cfg, budget, max_mcts_iterations, exploration_exploitation_parameter, max_sim_iterations, underwater_simulator, use_dag, config):


    num_rounds = 15
    iterations_per_round = 200

    min_reward = config['min_reward']
    max_reward = config['max_reward']

    shortcut_words = []

    overall_best_word_score = 0
    overall_best_word = None

    # cfg.grammar = cfg.generateGrammarGuidedStructureGroupsOneSequence()

    #cfg_shortcuts_only = CFG()
    #cfg_shortcuts_only.grammar = cfg_shortcuts_only.generateGrammarShortcutsOnly()

    # Initialize mcts_sa_output.txt
    f = open("/home/scheidee/mcts_sa_output/mcts_sa_output.txt","w+") #overall output file, can't load while running
    print(f.read())

    # Do the rounds
    for round in xrange(num_rounds):

        f1 = open("/home/scheidee/mcts_sa_output/mcts_sa_output_thru_round" + str(round) + ".txt","w+")

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

        #overall_best_word_score = 0 #wrong place
        #overall_best_word = None

        max_mcts_iterations = iterations_per_round
        #if round in range(1):
        #if round in range(5): #do mcts first half, do sa second half (5 rounds each)
        if round in range(5) or round > 5 and round%2==0 or len(shortcut_words) == 0: #ex. run mcts for first 5 rounds then SA/MCTS alternating i.e. mcts = (0,1,2,3,4,6,8), sa = (5,7,9)
        #if round%2==0 or len(shortcut_words) == 0: #alternating rounds
            f.write("MCTS...\n")
            f1.write("MCTS...\n")
            print("Running MCTS round: ", round)
            cfg_copy = copy.deepcopy(cfg)
            shortcut_words_copy = copy.deepcopy(shortcut_words)
            [solution, best_rollout, root, list_of_all_nodes, winner, best_rollout_node, best_nodes_dict, best_reward] = mcts( cfg_copy, budget, max_mcts_iterations, exploration_exploitation_parameter, max_sim_iterations, underwater_simulator, use_dag, config, shortcut_words_copy )
            f.write("Best rollout: ")
            f.write(best_rollout.toString())
            f.write("\n")
            f1.write("Best rollout: ")
            f1.write(best_rollout.toString())
            f1.write("\n")

            print('sequence at best node:')
            for soln in solution:
                soln.printWord()
            
            print('best_rollout at best node:')
            best_rollout.printWord()

            print('best_rollout_active_words at best node:')
            for best_rollout_active_word in winner.best_rollout_active_words:
                best_rollout_active_word.printWord()
                active_best_rollout = best_rollout_active_word

            print('sequence at best_rollout_node:')
            for soln in best_rollout_node.sequence:
                soln.printWord()

            print('best_rollout at best_rollout_node:')    
            best_rollout_node.best_rollout.printWord()

            print('best_rollout_active_words at best_rollout_node:')
            for best_rollout_active_word in best_rollout_node.best_rollout_active_words:
                best_rollout_active_word.printWord()

            print('best_reward from best_rollout: %s' % best_reward )
            

            prev_round_best_word = active_best_rollout
            best_reward = float(best_reward*(max_reward - min_reward)) + float(min_reward) # reverse normalization, to match sa scale
            intermediate_best_word_score = best_reward
            print("++++++++++++++++++++++++++++++++++")
            print("intermediate_best_word_score: %s\n" % intermediate_best_word_score)
            f.write("intermediate_best_word_score: %s\n" % intermediate_best_word_score)
            print("++++++++++++++++++++++++++++++++++")
            print("overall_best_word_score before check: %s\n" % overall_best_word_score)
            f.write("overall_best_word_score before check: %s\n" % overall_best_word_score)
            print("++++++++++++++++++++++++++++++++++")

            # Keep track of current best tree (of the entire search)
            if intermediate_best_word_score > overall_best_word_score:
                overall_best_word = active_best_rollout # this is just the active part
                overall_best_word_score = intermediate_best_word_score
                print("CURRENT OVERALL BEST WORD (active parts only): ")
                overall_best_word.printWord()
                print("OVERALL BEST WORD REWARD: %s" % overall_best_word_score)
                f.write("CURRENT OVERALL BEST WORD (active parts only): ")
                f.write(overall_best_word.toString())
                f.write("\n")
                f.write("OVERALL BEST WORD REWARD: %s" % overall_best_word_score)
                f.write("\n")
                f1.write("CURRENT OVERALL BEST WORD (active parts only): ")
                f1.write(overall_best_word.toString())
                f1.write("\n")
                f1.write("OVERALL BEST WORD REWARD: %s" % overall_best_word_score)
                f1.write("\n")

            # Extract information to pass to the next round
            # shortcut_words = [] # comment this out to keep the previous words
            subtree_words = []

            # Reset shortcut_words after a certain number of rounds
            if round > 5 and round/5 == 0:
                f.write("Resetting shortcut_words")
                shortcut_words = []

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
            f1.write("Shortcut words:\n")
            for word in shortcut_words:
                f.write(word.toString())
                f.write("\n")
                f1.write(word.toString())
                f1.write("\n")

        else:
            print("Running SA round: ", round)
            f.write("Simulated annealing...\n")
            f1.write("Simulated annealing...\n")

            initial_state_list = []
            initial_state = State(initial_state_list, shortcut_words)

            # Initialize state_list with best tree word, in list form, from mcts
            #old way #mcts_best_word = best_node.best_rollout_active_words[-1] #last best tree word
            #initial_state.initial_state_list = initial_state.wordToList(mcts_best_word)
            f.write("TESTING TESTING TESTING - prev_round_best_word\n")
            f.write(prev_round_best_word.toString())
            f.write("\n")
            f1.write("TESTING TESTING TESTING - prev_round_best_word\n")
            f1.write(prev_round_best_word.toString())
            f1.write("\n")
            initial_state.state_list = initial_state.wordToList(prev_round_best_word)
            f.write("Test to see if SA gets current best word as starting point...\n")
            f1.write("Test to see if SA gets current best word as starting point...\n")
            initial_word = initial_state.stateToFulltreeWord()
            f.write("Initial SA state word (checking for test): %s\n" % initial_word.toString())
            f1.write("Initial SA state word (checking for test): %s\n" % initial_word.toString())

            initial_temperature = 1000
            k_max = 200
            sim_anneal = SimulatedAnnealing(initial_state, initial_temperature, k_max, round)
            sim_anneal_best_word, score, sim_anneal_best_words, scores = sim_anneal.run()
            print("++++++++++++++++++++++")
            print("Sim anneal best words: " + str(sim_anneal_best_words) + "len = " + str(len(sim_anneal_best_words)))
            print("Associated scores: " + str(scores) + "len = " + str(len(scores)))
            print("++++++++++++++++++++++")
            f.write("Best word: ")
            f.write(sim_anneal_best_word.toString())
            f.write("\n")
            f.write("Best word score: %d\n" % score)
            f1.write("Best word: ")
            f1.write(sim_anneal_best_word.toString())
            f1.write("\n")
            f1.write("Best word score: %d\n" % score)

            prev_round_best_word = sim_anneal_best_word # to give back to initialize consecutive SA rounds
            intermediate_best_word_score = score
            print("++++++++++++++++++++++++++++++++++")
            print("intermediate_best_word_score: %s\n" % intermediate_best_word_score)
            f.write("intermediate_best_word_score: %s\n" % intermediate_best_word_score)
            print("++++++++++++++++++++++++++++++++++")
            print("overall_best_word_score before check: %s\n" % overall_best_word_score)
            f.write("overall_best_word_score: %s\n" % overall_best_word_score)
            print("++++++++++++++++++++++++++++++++++")

            if intermediate_best_word_score > overall_best_word_score:
                # Keep track of current best tree (of the entire search)
                overall_best_word = sim_anneal_best_word # should already be active because active update happens in sim_anneal.energy()
                overall_best_word_score = intermediate_best_word_score
                print("CURRENT OVERALL BEST WORD (active parts only): ")
                overall_best_word.printWord()
                print("OVERALL BEST WORD REWARD: %s" % overall_best_word_score)
                f.write("CURRENT OVERALL BEST WORD (active parts only): ")
                f.write(overall_best_word.toString())
                f.write("\n")
                f.write("OVERALL BEST WORD REWARD: %s" % overall_best_word_score)
                f.write("\n")
                f1.write("CURRENT OVERALL BEST WORD (active parts only): ")
                f1.write(overall_best_word.toString())
                f1.write("\n")
                f1.write("OVERALL BEST WORD REWARD: %s" % overall_best_word_score)
                f1.write("\n")
            

            # Extract information to pass to the next round
            #shortcut_words = [] # comment this out to keep the previous words
            subtree_words = []

            # Reset shortcut_words after a certain number of rounds
            if round > 5 and round/5 == 0:
                f.write("Resetting shortcut_words")
                shortcut_words = []

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
            f1.write("Shortcut words:\n")
            for word in shortcut_words:
                f.write(word.toString())
                f.write("\n")
                f1.write(word.toString())
                f1.write("\n")
        
        

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

        f1.close()

        
    f.close()
    #return [solution, best_rollout, root, list_of_all_nodes, winner, best_rollout_node, best_nodes_dict, sim_anneal_best_word]
    return overall_best_word, overall_best_word_score