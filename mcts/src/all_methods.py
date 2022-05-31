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

class AllMethods():

    def __init__(self, config):
            
        self.num_rounds = config['num_rounds']
        self.iterations_per_round = config['iterations_per_round']
        self.consecutive_initial_rounds = config['consecutive_initial_rounds']

        self.min_reward = config['min_reward']
        self.max_reward = config['max_reward']

        self.use_dag = config['use_dag']
        self.use_cheat = config['use_cheat']
        self.use_groups = config['use_groups']
        self.use_structure = config['use_structure']
        self.use_restarts = config['use_restarts']
        self.use_sa = config['use_sa']
        self.best_reward_per_round_list = []

        self.generate_data = config['generate_data']

    #def run(self, cfg, budget, max_mcts_iterations, exploration_exploitation_parameter, max_sim_iterations, underwater_simulator, use_dag, config):
    def run(self, cfg, budget, exploration_exploitation_parameter, max_sim_iterations, underwater_simulator, use_dag, config):

        shortcut_words = []

        overall_best_word_score = 0
        overall_best_word = None
        total_time_to_best = 0
        num_rounds_to_best = 0

        # Make it run one long round
        if not self.use_restarts:
            self.iterations_per_round = self.iterations_per_round*self.num_rounds
            self.num_rounds = 1

        start_time = int(time.time()*1000) #milliseconds

        # Neural network data generation
        if self.generate_data:
            # Initialize file for saving data
            num_examples = self.num_rounds*self.iterations_per_round
            data_gen_path = "/home/scheidee/Desktop/neural_mcdags_output/DATA/" + str(num_examples) + "examples" + str(start_time) + ".txt"
            d = open(data_gen_path ,"w+")


        config_filename = rospy.get_param('~config')
        garbage_string = "_parameters.yaml"
        if garbage_string in config_filename:
            current_method = config_filename.replace(garbage_string, '')

        # Initialize mcts_sa_output.txt
        f = open("/home/scheidee/Desktop/neural_mcdags_output/RESULTS/2022_05_28/intermediate/" + str(start_time) + current_method + "_output.txt","w+") #overall output file, can't load while running
        #print(f.read())

        # Do the rounds
        for round in xrange(self.num_rounds):

            f1 = open("/home/scheidee/Desktop/neural_mcdags_output/RESULTS/2022_05_28/intermediate/" + str(start_time) + current_method + "_output_thru_round" + str(round) + ".txt","w+")

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

            max_mcts_iterations = self.iterations_per_round
            #if round in range(1):
            #if round in range(5): #do mcts first half, do sa second half (5 rounds each)
            if not self.use_sa or (round  < self.consecutive_initial_rounds or round > self.consecutive_initial_rounds and round%2!=0 or len(shortcut_words) == 0): #ex. run mcts for first 5 rounds then SA/MCTS alternating i.e. mcts = (0,1,2,3,4,6,8), sa = (5,7,9)
            #if round%2==0 or len(shortcut_words) == 0: #alternating rounds
                f.write("MCTS...\n")
                f1.write("MCTS...\n")
                print("Running MCTS round: ", round)
                cfg_copy = copy.deepcopy(cfg)
                shortcut_words_copy = copy.deepcopy(shortcut_words)
                [solution, best_rollout, root, list_of_all_nodes, winner, best_rollout_node, best_nodes_dict, best_reward] = mcts( cfg_copy, budget, max_mcts_iterations, exploration_exploitation_parameter, max_sim_iterations, underwater_simulator, use_dag, config, shortcut_words_copy, generate_data = self.generate_data, data_gen_file_path = data_gen_path)
                

                # # Write example: tree word, reward int to data file, d
                # if self.generate_data:
                #     d.write(best_rollout.toString())
                #     d.write(',' + str(best_reward) + '\n')

                f.write("Best rollout: ")
                if best_rollout:
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
                        #active_best_rollout = best_rollout_active_word

                    print('sequence at best_rollout_node:')
                    for soln in best_rollout_node.sequence:
                        soln.printWord()

                    print('best_rollout at best_rollout_node:')    
                    best_rollout_node.best_rollout.printWord()

                    print('best_rollout_active_words at best_rollout_node:')
                    for best_rollout_active_word in best_rollout_node.best_rollout_active_words:
                        best_rollout_active_word.printWord()
                        active_best_rollout = best_rollout_active_word

                    print('best_reward from best_rollout: %s' % best_reward )
                    

                    prev_round_best_word = active_best_rollout
                    best_reward = float(best_reward*(self.max_reward - self.min_reward)) + float(self.min_reward) # reverse normalization, to match sa scale
                    intermediate_best_word_score = best_reward
                else:
                    print('Not printing results because best_rollout is None')
                    prev_round_best_word = None
                    intermediate_best_word_score = 0


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
                    total_time_to_best = int(time.time()) - start_time/1000 #total time in seconds, that it took to reach the overall best word
                    num_rounds_to_best = round
                    print("CURRENT OVERALL BEST WORD (active parts only): ")
                    overall_best_word.printWord()
                    print("OVERALL BEST WORD REWARD: %s" % overall_best_word_score)
                    
                    f.write("CURRENT OVERALL BEST WORD (active parts only): ")
                    f1.write("CURRENT OVERALL BEST WORD (active parts only): ")
                    if overall_best_word:
                        f.write(overall_best_word.toString())
                        f.write("\n")
                        f1.write(overall_best_word.toString())
                        f1.write("\n")
                    else:
                        f.write('None\n')
                        f1.write('None\n')

                    f.write("OVERALL BEST WORD REWARD: %s" % overall_best_word_score)
                    f.write("\n")
                    f1.write("OVERALL BEST WORD REWARD: %s" % overall_best_word_score)
                    f1.write("\n")
                    

                # Extract information to pass to the next round
                # shortcut_words = [] # comment this out to keep the previous words
                subtree_words = []

                # Add the subtrees from the overall_best_word
                if overall_best_word_score > 0:

                    extracted_subtrees = extract_subtrees(overall_best_word)
                    subtree_words.extend(extracted_subtrees)

                '''
                #COMMENTING THIS OUT BECAUSE SHORTCUTS WERE EMPTY AFTER ROUND 20
                # Reset shortcut_words after a certain number of rounds
                if round > initial_round_threshold and round%initial_round_threshold == 0:
                    f.write("Resetting shortcut_words\n")
                    shortcut_words = []
                '''

                # Add overall_best_word so that those subtrees become shortcuts and you can initialize SA round with overall_best_word
                #if overall_best_word_score > 0:
                    #best_nodes_dict['overall_best_word'] = overall_best_word
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
                
                # The subtrees found in this round of mcts should be in subtree_words regardless of frequency of appearance
                f.write("Subtrees extracted from all best trees in this round of mcts\n")
                f1.write("Subtrees extracted from all best trees in this round of mcts\n")
                for word in subtree_words:
                    f.write(word.toString())
                    f.write("\n")
                    f1.write(word.toString())
                    f1.write("\n")
                f.write("Not all of these will be added to shortcut_words if there is redundancy\n")
                f1.write("Not all of these will be added to shortcut_words if there is redundancy\n")

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
                f1.write("TESTING TESTING TESTING - prev_round_best_word\n")
                print("TESTING TESTING TESTING - prev_round_best_word\n")
                if prev_round_best_word:
                    f.write(prev_round_best_word.toString())
                    f.write("\n")
                    f1.write(prev_round_best_word.toString())
                    f1.write("\n")
                    print(prev_round_best_word.toString())
                else:
                    f.write('None\n')
                    f1.write('None\n')
                
                
                
                if overall_best_word_score > 0:
                    print('Initializing SA with overall best word...')
                    print('Overall best word: ', overall_best_word.toString())
                    initial_state.state_list = initial_state.wordToList(overall_best_word)
                print('initial_state.state_list',initial_state.state_list)
                f.write("Test to see if SA gets current best word as starting point...\n")
                f1.write("Test to see if SA gets current best word as starting point...\n")
                initial_word = initial_state.stateToFulltreeWord()
                if initial_word:
                    f.write("Initial SA state word (checking for test): %s\n" % initial_word.toString())
                    f1.write("Initial SA state word (checking for test): %s\n" % initial_word.toString())
                else:
                    f.write("Initial SA state word (checking for test): None\n")
                    f1.write("Initial SA state word (checking for test): None\n")

                initial_temperature = self.iterations_per_round
                k_max = 1000
                sim_anneal = SimulatedAnnealing(initial_state, initial_temperature, k_max, round, underwater_simulator, self.use_cheat)
                sim_anneal_best_word, score, iteration_best_was_found, sim_anneal_best_words, scores = sim_anneal.run()
                print("++++++++++++++++++++++")
                print("Sim anneal best words: " + str(sim_anneal_best_words) + "len = " + str(len(sim_anneal_best_words)))
                print("Associated scores: " + str(scores) + "len = " + str(len(scores)))
                print("++++++++++++++++++++++")
                
                f.write("Best word: ")
                f1.write("Best word: ")
                if sim_anneal_best_word:
                    f.write(sim_anneal_best_word.toString())
                    f.write("\n")
                    f1.write(sim_anneal_best_word.toString())
                    f1.write("\n")
                else:
                    f.write('None\n')
                    f1.write('None\n')
                
                f.write("Best word score: %d\n" % score)
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
                    total_time_to_best = int(time.time()) - start_time/1000 #total time in seconds, that it took to reach the overall best word
                    num_rounds_to_best = round
                    print("CURRENT OVERALL BEST WORD (active parts only): ")
                    f.write("CURRENT OVERALL BEST WORD (active parts only): ")
                    f1.write("CURRENT OVERALL BEST WORD (active parts only): ")
                    if overall_best_word:
                        overall_best_word.printWord()
                        f.write(overall_best_word.toString())
                        f.write("\n")
                        f1.write(overall_best_word.toString())
                        f1.write("\n")
                    else:
                        print('None')
                        f.write('None\n')
                        f1.wrote('None\n')

                    print("OVERALL BEST WORD REWARD: %s" % overall_best_word_score)
                    f.write("OVERALL BEST WORD REWARD: %s" % overall_best_word_score)
                    f.write("\n")
                    f1.write("OVERALL BEST WORD REWARD: %s" % overall_best_word_score)
                    f1.write("\n")
                    

                # Extract information to pass to the next round
                #shortcut_words = [] # comment this out to keep the previous words
                subtree_words = []

                '''
                #COMMENTING THIS OUT BECAUSE SHORTCUTS WERE EMPTY AFTER ROUND 20
                # Reset shortcut_words after a certain number of rounds
                if round > initial_round_threshold and round%initial_round_threshold == 0:
                    f.write("Resetting shortcut_words\n")
                    shortcut_words = []
                '''

                # Include overall_best_word to make sure the associated subtrees are shortcuts
                if overall_best_word_score > 0:
                    sim_anneal_best_words.append(overall_best_word)
                    scores.append(overall_best_word_score)
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

                
                # The subtrees found in this round of mcts should be in subtree_words regardless of frequency of appearance
                f.write("Subtrees extracted from all best trees in this round of mcts\n")
                f1.write("Subtrees extracted from all best trees in this round of mcts\n")
                for word in subtree_words:
                    f.write(word.toString())
                    f.write("\n")
                    f1.write(word.toString())
                    f1.write("\n")
                f.write("Not all of these will be added to shortcut_words if there is redundancy\n")
                f1.write("Not all of these will be added to shortcut_words if there is redundancy\n")

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
                if word:
                    word.printWord()
                else:
                    print('None')


            # Append best word from last round to overall list
            self.best_reward_per_round_list.append(overall_best_word_score)

            
            f1.write("===========================\n")    
            f1.write("OVERALL_BEST_WORD: \n")
            if overall_best_word != None:
                f1.write(overall_best_word.toString()+'\n')
            else:
                f1.write("None\n")
            f1.write("OVERALL_BEST_WORD_SCORE: %s\n" % overall_best_word_score)
            f1.write("===========================\n")
            f1.close()
            

        total_time_for_run = int(time.time()) - start_time/1000

        
        f.write("===========================\n")    
        f.write("OVERALL_BEST_WORD: \n")
        if overall_best_word: #meaning overall best word is not None
            f.write(overall_best_word.toString()+'\n')
        else:
            f.write('None\n')
        f.write("OVERALL_BEST_WORD_SCORE: %s\n" % overall_best_word_score)
        f.write("===========================\n")    
        

        # Need to fix MCTS iteration check when best is found first
        #f.write("RUNTIME: --- %s seconds ---" % (total_time_to_best)+'\n')
        #f.write("RUNTIME: --- %s minutes ---" % str((total_time)/60.0)+'\n')
        #f.write("RUNTIME: --- %s hours ---" % str((total_time)/3600.0)+'\n')
        f.close()
        #return [solution, best_rollout, root, list_of_all_nodes, winner, best_rollout_node, best_nodes_dict, sim_anneal_best_word]
        return overall_best_word, overall_best_word_score, total_time_to_best, num_rounds_to_best, total_time_for_run,  self.best_reward_per_round_list
        #return [solution, best_rollout, root, list_of_all_nodes, winner, best_rollout_node, best_nodes_dict, best_reward]
