#!/usr/bin/env python
'''
Basic MCTS implementation
Graeme Best
Oregon State University
Jan 2020
'''

from mcts import mcts
#from mcts_restarts import mcts_restarts
#from mcts_restarts_with_simulated_annealing import mcts_sim_anneal_switching
from all_methods import AllMethods
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
import datetime


def run():

    rospy.init_node('mcts')

    config_filename = rospy.get_param('~config')
    param_string_us = "_parameters.yaml" # us: with underscore
    param_string = "parameters.yaml"
    if param_string_us in config_filename:
        current_method = config_filename.replace(param_string_us, '')
    elif param_string == config_filename:
        current_method = 'basic_test'

    now = datetime.datetime.now()
    start_time_milli = int(time.time()*1000) #milliseconds


    # Create output file (Change this path accordingly!)
    f = open("/home/scheidee/Desktop/neural_mcdags_output/RESULTS/2022_05_27/final_output_files/" + str(start_time_milli) + current_method + "_output.txt","w+") #overall output file, can't load while running

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

    # Get seed
    seed = rospy.get_param('~seed')

    # Create a simulator
    underwater_simulator = UnderwaterSimulator(seed=seed)
    
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
    use_sa = config["use_sa"]

    num_rounds = config["num_rounds"]
    iterations_per_round = config["iterations_per_round"]
    consecutive_initial_rounds = config["consecutive_initial_rounds"]
    

    # Create instance of class containing all methods
    all_methods = AllMethods(config)

    overall_best_word, overall_best_word_score, total_time_to_best, num_rounds_to_best, total_time_for_run, best_reward_per_round_list = all_methods.run(cfg, budget, exploration_exploitation_parameter, max_sim_iterations, underwater_simulator, use_dag, config)
    f.write("Results for " + current_method + " method: \n")
    f.write("Date and time: " + now.strftime("%Y-%m-%d %H:%M:%S")+ "\n")
    f.write("Overall best word: \n")
    if overall_best_word:
        f.write(overall_best_word.toString() + "\n")
    else:
        f.write('None\n')
    f.write("Overall best word score: " + str(overall_best_word_score) + "\n")
    f.write("All rounds best score list: \n")
    print(best_reward_per_round_list)  
    f.write(str(best_reward_per_round_list))
    f.write('\n')
    f.write(str(len(best_reward_per_round_list)))
    f.write('\n')
    f.write("Total time to best: " + str(total_time_to_best) + " seconds\n")
    f.write("Number of rounds to best: " + str(num_rounds_to_best) + "\n")
    f.write("Total time for run: " + str(total_time_for_run) + " seconds\n")


    '''
    if use_sa: # Run simulated annealing as subtree compilation rounds
        
        final_best_word, final_best_word_score = all_methods.monte_carlo_sim_anneal_switching( cfg, budget, max_mcts_iterations, exploration_exploitation_parameter, max_sim_iterations, underwater_simulator, use_dag, config )    
    
        print('Final best word:')
        if final_best_word:
            final_best_word.printWord()
        else:
            print(final_best_word) #should be None in this case (to account for when no trees have score > 0 in a round)
    
    else: # Run Monte Carlo method as subtree compilation rounds
        
        [solution, best_rollout, root, list_of_all_nodes, winner, best_rollout_node, best_nodes_dict, best_reward] = all_methods.monte_carlo_restarts( cfg, budget, max_mcts_iterations, exploration_exploitation_parameter, max_sim_iterations, underwater_simulator, use_dag, config )    

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

    '''

    f.write("Total number of rounds: " + str(num_rounds) + "\n")
    f.write("Iterations per round: " + str(iterations_per_round) + "\n")
    f.write("Consecutive initial rounds: " + str(consecutive_initial_rounds) + "\n")
    f.close()

def run_profiler():
    cProfile.run('run()', 'profile_stats')
    p = pstats.Stats('profile_stats')
    p.sort_stats("cumulative").print_stats(50)

if __name__ == "__main__":
    start_time = time.time()
    run()
    #f = open("/home/scheidee/mcts_sa_output/mcts_sa_output.txt","w+")
    total_time = time.time() - start_time
    print("RUNTIME: --- %s seconds ---" % (total_time))
    print("RUNTIME: --- %s minutes ---" % str((total_time)/60.0))
    print("RUNTIME: --- %s hours ---" % str((total_time)/3600.0))
    #f.write("RUNTIME: --- %s seconds ---\n" % (total_time))
    #f.write("RUNTIME: --- %s minutes ---\n" % str((total_time)/60.0))
    #f.write("RUNTIME: --- %s hours ---\n" % str((total_time)/3600.0))
    #f.close()
    # run_profiler()
    
    
