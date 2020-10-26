#!/usr/bin/env python

# Generate a box plot show final tree performance for all methods (not manual)
# Normalize all scores wrt manual tree score on world at hand before plotting

# Box plot 1
# Performance on same world trained on (same seed)

# Box plot 2
# Performance on different worlds, all normalized wrt manual so they can be compared

# NOTE: may not include all methods, but set it up so you can

import numpy as np 
import matplotlib.pyplot as plt 
import matplotlib.cm
from cfg import createWord
from simulator.run_simulator import UnderwaterSimulator

from os import listdir
from os.path import isfile, join

import rospy
import copy
import json

import re


from scipy import stats

def initialize_data_array_list():#initalize_data_arrays():

    data = []

    for i in range(len(data_labels)):
        data.append(np.array(()))

    print('data init', data)

    return data

    '''
    final_data = np.array(())
    no_sa_data = np.array(())
    no_sa_no_restarts_data = np.array(())
    no_dag_data = np.array(())
    no_groups_data = np.array(())
    no_groups_no_structure_data = np.array(())
    no_cheat_data = np.array(())

    data_arrays = [final_data, no_sa_data, no_sa_no_restarts_data, no_dag_data, no_groups_data, no_groups_no_structure_data, no_cheat_data]
    
    return data_arrays
    '''

def normalize_reward(manual_reward, reward):
    print('reward', reward)
    print('manual_reward', manual_reward)
    norm_reward = float(reward)/float(manual_reward)
    print('in function norm_reward', norm_reward)
    return norm_reward

def get_method_type(file_name):

    #print('in method function')
    #print('file name', file_name)
    for label in data_labels:
        #print('label loop test', label)
        if label in file_name:
            #print('label', label)
            return label


    '''
    if 'final' in file_name:
        return 'final'
    elif 'no_sa' in file_name:
        return 'no_sa'
    elif 'no_sa_no_restarts' in file_name:
        return 'no_sa_no_restarts'
    elif 'no_dag' in file_name:
        return 'no_dag'
    elif 'no_groups' in file_name:
        return 'no_groups'
    elif 'no_groups_no_structure' in file_name:
        return 'no_groups_no_structure'
    elif 'no_cheat' in file_name:
        return 'no_cheat'
    else:
        return None
    '''

def update_data_array_list(data, method, norm_reward): #final_data, no_sa_data, no_sa_no_restarts_data, no_dag_data, no_groups_data, no_groups_no_structure_data, no_cheat_data):

    print('method for update', method)
    for element in range(len(data_labels)):
        if method == data_labels[element]:
            data[element] = np.append(data[element], norm_reward)

    print('data update',data)

    '''
    if method == 'final':
        final_data = np.append(final_data, norm_reward)
    if method == 'no_sa':
        no_sa_data = np.append(no_sa_data, norm_reward)
    if method == 'no_sa_no_restarts':
        no_sa_no_restarts_data = np.append(no_sa_no_restarts_data, norm_reward)
    if method == 'no_dag':
        no_dag = np.append(no_dag_data, norm_reward)
    if method == 'no_groups':
        no_groups_data = np.append(no_groups_data, norm_reward)
    if method == 'no_groups_no_structure':
        no_groups_no_structure_data = np.append(no_groups_no_structure_data, norm_reward)
    if method == 'no_cheat':
        no_cheat_data = np.append(no_cheat_data, norm_reward)


    data_arrays = [final_data, no_sa_data, no_sa_no_restarts_data, no_dag_data, no_groups_data, no_groups_no_structure_data, no_cheat_data]

    return data_arrays
    '''

'''
def update_world(new_seed, underwater_simulator):

    # THIS IS WRONG

    # Update seed
    underwater_simulator.seed = new_seed

    # Create the world
    world = World(self.config)
    do_test = True # don't error check graph

    world.init_world(new_seed, do_test)
'''

def extract_BT_string(path,file):
    open_file = open(path + '/' + file, 'r')
    lines = open_file.readlines()
    temp = lines[3] 

    # Remove '\n'
    return temp[:-1]


def update_box_plot(path, num_worlds, manual_word):

    seed = rospy.get_param('~seed')

    # Given the path to the output directory
    files = [f for f in listdir(path)]
    print(files)

    data = initialize_data_array_list()

    for world_num in range(num_worlds):

        if num_worlds != 1:
            # change world by changing seed
            seed = world_num + 100

        # Create a simulator
        underwater_simulator = UnderwaterSimulator(seed = seed)

        # Reset seed for repeatability
        underwater_simulator.world.reset_seed()

        # Generate manual tree reward
        manual_reward, robot_reported2, distance2, active_word2, active_subtree_indices2 = underwater_simulator.generateReward(manual_word,200)

        # Use data from all files in output directory to update the appropriate data arrays
        for file_name in files:

            # Extract method
            method = get_method_type(file_name)

            #if not method:
                #break # because method is None, i.e. file is named weirdly

            # Extract final tree string
            BT_string = extract_BT_string(path, file_name)
            print(BT_string)

            # Create final tree word
            BT_word = createWord(BT_string)

            #if new_seeds: # new worlds
                #for new_seed in new_seeds:

            # Reset seed for repeatability
            underwater_simulator.world.reset_seed()

            # Generate raw reward
            reward, robot_reported, distance, active_word, active_subtree_indices = underwater_simulator.generateReward(BT_word,200)

            # Normalize raw reward wrt manual tree
            norm_reward = normalize_reward(manual_reward, reward)
            print('norm_reward',norm_reward)

            # Add normalized reward to appropriate dataset
            update_data_array_list(data, method, norm_reward) # final_data, no_sa_data, no_sa_no_restarts_data, no_dag_data, no_groups_data, no_groups_no_structure_data, no_cheat_data)



    # Having added all data from files to appropriate data array, combine into one array
    #data = [ final_data, no_sa_data, no_sa_no_restarts_data, no_dag_data, no_groups_data, no_groups_no_structure_data, no_cheat_data]
    #print('final_data', final_data)
    #print('no_dag_data', no_dag_data)
    #print('no_sa_data', no_sa_data)

    # This is just for visualization so the labels are correct, won't be needed once we have all the results
    for i in range(len(data)):
        array = data[i]
        if array.size == 0:
            data[i] = np.array([0])

    fig, ax = plt.subplots()
    ax.set_title('Behavior Tree Performance')
    ax.boxplot(data)
    ax.set_xlabel('Method')
    ax.set_ylabel('Reward (normalized)')

    xs = range(1,len(data_labels)+1)

    plt.xticks(xs, data_labels_no_underscore, rotation=45, ha='right')


    plt.show()

def initialize_convergence_data_lists():

    convergence_data_list_list = []

    for i in range(len(data_labels)):
        convergence_data_list_list.append([])

    return convergence_data_list_list


def accumulate_method_lists(method, to_be_summed_list, reward_list):
    # Group a given extracted reward list with others for that method so they can be consolidated after sorting

    for element in range(len(data_labels)):
        if method == data_labels[element]:
            to_be_summed_list[element].append(json.loads(reward_list)) # if reward_list is '[1,2,3]' format not [1,2,3]
            # to_be_summed_list[element].append(reward_list)

def extract_reward_list(path,file):
    open_file = open(path + '/' + file, 'r')
    lines = open_file.readlines()
    temp = lines[6] 

    # Remove '\n'
    return temp[:-1]

def extract_final_tree(path,file):
    open_file = open(path + '/' + file, 'r')
    lines = open_file.readlines()
    temp = lines[-3] 

    # Remove '\n'
    return temp[:-1]


def generate_reward_list(path_to_intermediates, timestamp, do_skips_for_testing):

    '''
    for all files with given timestamp
        get best tree from almost last line in that file
        generateReward on particular world that stays the same
        add that reward to new_reward_list
    do until all done so new_reward_list has 50 elements all specific to that world
    '''

    seed = rospy.get_param('~seed')

    files = [f for f in listdir(path_to_intermediates)]

    new_reward_list = [None]*50

    # Create a simulator
    underwater_simulator = UnderwaterSimulator(seed = seed)

    # Reset seed for repeatability
    underwater_simulator.world.reset_seed()

    # Generate manual tree reward
    manual_reward, robot_reported2, distance2, active_word2, active_subtree_indices2 = underwater_simulator.generateReward(manual_word,200)

    #round_count = 0
    for file_name in files:
        if rospy.is_shutdown():
            break

        if 'round' in file_name and timestamp in file_name:
        
            #round_count += 1
            indices_of_round_in_name = re.search(r'round', file_name)
            round = int(file_name[indices_of_round_in_name.end():-4])
            print('round',round)

            if do_skips_for_testing and not (round == 0 or (round+1)%10 == 0):
                continue
            else:

                final_best_tree_string = extract_final_tree(path_to_intermediates,file_name)
                print('current filename: ', file_name)
                if final_best_tree_string == 'overall_best_word is None':
                    final_best_tree_string = ''
                    norm_reward = 0
                    print('final_best_tree_string: ', final_best_tree_string)
                else:

                    # Create final tree word
                    BT_word = createWord(final_best_tree_string)

                    # Reset seed for repeatability
                    underwater_simulator.world.reset_seed()

                    # Generate raw reward
                    reward, robot_reported, distance, active_word, active_subtree_indices = underwater_simulator.generateReward(BT_word,200)

                    # Normalize raw reward wrt manual tree
                    norm_reward = normalize_reward(manual_reward, reward)


            new_reward_list[round]= norm_reward

    print('new_reward_list: ', new_reward_list)
    return new_reward_list


def generate_all_reward_lists(path_to_intermediates, to_be_summed_list, do_skips_for_testing):
    # Given the path to the output directory
    files = [f for f in listdir(path_to_intermediates)]

    for file_name in files:

        if 'round' not in file_name:
            timestamp = file_name[:13]
            method = get_method_type(file_name)
            new_reward_list = generate_reward_list(path_to_intermediates, timestamp, do_skips_for_testing)
            accumulate_method_lists(method, to_be_summed_list, new_reward_list)

    return to_be_summed_list

def update_convergence_plot(path, path_to_intermediates, do_skips_for_testing):
    # Given the path to the output directory
    files = [f for f in listdir(path)]
    #print(files)

    to_be_summed_list = initialize_convergence_data_lists() #each element of this list will be a list of lists
    convergence_data_list_list = initialize_convergence_data_lists() #each element will be a list of average best rewards for the element-specific method]

    # Generate rewards for each rounds best tree on same world, normalized wrt manual tree performance
    # Graeme commented this out
    # to_be_summed_list = generate_all_reward_lists(path_to_intermediates, to_be_summed_list, do_skips_for_testing)

    for filename in files:
    	method = get_method_type(filename)
    	reward_list = extract_reward_list(path,filename)
    	accumulate_method_lists(method, to_be_summed_list, reward_list)

    # Average best rewards for each round of all 50-round runs
    for i in range(len(to_be_summed_list)): # for each method
        element = to_be_summed_list[i]
        averaging_num = len(element)

        print('method',data_labels_no_underscore[i])
        print('num trials:',averaging_num)

        for j in range(len(element)): # for each 50-round run, i.e. each reward list
            reward_list = to_be_summed_list[i][j]
            for k in range(len(reward_list)): #for each best reward (per round)
                if len(convergence_data_list_list[i]) < k+1:
                    convergence_data_list_list[i].append(0)
                convergence_data_list_list[i][k] += reward_list[k] #sum with other nums for that specific round and method

        # Once a method is completely summed from all 50-round runs, get average
        for a in range(len(convergence_data_list_list[i])):
            convergence_data_list_list[i][a] = convergence_data_list_list[i][a]/averaging_num

    # GRAEME added
    # Compute errors for errorbars
    convergence_error_list_list_list = []
    for i in range(len(to_be_summed_list)):
        element = to_be_summed_list[i]
        convergence_error_list_list_list.append([])
        for j in range(len(element)):

            reward_list = to_be_summed_list[i][j]
            for k in range(len(reward_list)): #for each best reward (per round)
                if len(convergence_error_list_list_list[i]) < k+1:
                    convergence_error_list_list_list[i].append([])
                current_score = reward_list[k] #convergence_data_list_list[i][k] += reward_list[k]
                convergence_error_list_list_list[i][k].append(current_score)

    convergence_errors = []
    for i in range(len(to_be_summed_list)):
        convergence_errors.append([])
        for k in range(len(convergence_error_list_list_list[i])):

            # standard error of the mean
            reward_list = convergence_error_list_list_list[i][k]
            convergence_errors[i].append( stats.sem(reward_list) )

    # Plot each method
    plt.figure(figsize = (5,4))
    x = range(len(reward_list)) #len=50
    y = convergence_data_list_list
    if not do_skips_for_testing:
        plt.xlabel('Rounds')
    else:
        plt.xlabel('Rounds/10')
    plt.ylabel('Reward (normalized)')
    # cmap = plt.get_cmap()
    # cmap = 'bgrcmyk'
    # plt.title('Average Best Reward')
    for i in range(len(convergence_data_list_list)):
        method_rewards = convergence_data_list_list[i]
        # plt.plot(method_rewards, label = data_labels_no_underscore[i])

        # col = cmap[data_labels_cmap_indices[i]]
        col = 'C' + str(data_labels_cmap_indices[i])
        print(col)

        method_error = convergence_errors[i]
        plt.errorbar(range(0,len(method_rewards)),method_rewards,method_error, color = col, label = data_labels_no_underscore[i], errorevery = 10, capsize = 3)
    plt.legend()
    plt.show()


if __name__ == '__main__':

    rospy.init_node('plot_results')

    do_skips_for_testing = False

    # num_worlds = input('For convergence plot, enter 0. For box plot, enter 1 for training world, and otherwise specify number of new worlds to test on: ')

    num_worlds = None

    #data_labels_no_underscore = ['final', 'no sa', 'no sa\nno restarts', 'no dag','no groups','no groups\nno structure','no cheat']
    #data_labels = ['final', 'no_sa', 'no_sa_no_restarts', 'no_dag','no_groups','no_groups_no_structure','no_cheat']
    #data_labels_no_underscore = ['final', 'no sa', 'no dag','no groups','no cheat']
    #data_labels = ['final', 'no_sa', 'no_dag','no_groups','no_cheat']
    # if num_worlds == 0: # convergence comparisons (no sa no restart doesnt count b/c doesnt do 50 rounds)
    #    data_labels_no_underscore = ['final', 'no cheat', 'no dag', 'no sa', 'no groups','no groups\nno structure']
    #     data_labels = ['final', 'no_cheat', 'no_dag', 'no_sa', 'no_groups', 'no_groups_no_structure']
    # else: # final tree comparison
    #     data_labels_no_underscore = ['final', 'no cheat', 'no dag', 'no sa', 'no groups','no groups\nno structure','no sa\nno restarts']
    #     data_labels = ['final', 'no_cheat', 'no_dag', 'no_sa', 'no_groups', 'no_groups_no_structure', 'no_sa_no_restarts']

    data_labels = ['no_cheat', 'no_dag', 'no_sa', 'no_groups_no_structure']
    data_labels_no_underscore = ['MCDAGS+SA', 'MCTS+SA', 'MCDAGS', 'No Structure']
    data_labels_cmap_indices = [1,2,3,4] #[1,3,4,6]



    # Specify path to all output files
    path = "/home/graeme/Dropbox/emily_graeme_shared/results_from_graeme/simple/all_methods_output/n_3/"
    path_to_intermediates = ""
    #path_to_intermediates = "/home/scheidee/Desktop/bt_learning_output/RESULTS/old/test"

    manual_word = createWord('? ( -> ( (wildlife_found) ? ( (in_comms) [go_to_comms] ) [report] ) -> ( (mine_found) ? ( <!> ( (is_armed) ) [disarm] ) ) -> ( ? ( <!> ( (carrying_benign) ) [take_to_drop_off] ) (benign_object_found) [pick_up] ) -> ( (likely_target_found) [go_to_likely_target] ) -> ( [coverage] ) )')

    # if num_worlds != 0:
    #     update_box_plot(path,num_worlds,manual_word)
    # else:
    update_convergence_plot(path, path_to_intermediates, do_skips_for_testing)

    # Just testing box plot stuff
    '''
    # Fixing random state for reproducibility
    np.random.seed(19680801)

    # fake up some data
    spread = np.random.rand(50) * 100
    print('Spread: ' + str(spread))
    center = np.ones(25) * 50
    flier_high = np.random.rand(10) * 100 + 100
    flier_low = np.random.rand(10) * -100
    data = np.concatenate((spread, center, flier_high, flier_low))

    spread = np.random.rand(50) * 100
    center = np.ones(25) * 40
    flier_high = np.random.rand(10) * 100 + 100
    flier_low = np.random.rand(10) * -100
    d2 = np.concatenate((spread, center, flier_high, flier_low))

    data = [data, d2, d2[::2]]
    fig7, ax7 = plt.subplots()
    ax7.set_title('Multiple Samples with Different sizes')
    ax7.boxplot(data)

    #data = np.array((23,42,13,0,47))
    #fig7, ax7 = plt.subplots()
    #ax7.set_title('Multiple Samples with Different sizes')
    #ax7.boxplot(data)

    plt.show()

    '''

    #ALSO NEED TO DIFFERENTIATE BETWEEN SAME WORLD AND DIFFERENT WORLD PLOT GENERATION