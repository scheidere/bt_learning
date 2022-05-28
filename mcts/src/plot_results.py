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
from cfg import createWord
from simulator.run_simulator import UnderwaterSimulator

from os import listdir
from os.path import isfile, join

import rospy
import copy
import json

import scipy.stats as stats

import re

import rospkg
import yaml





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

def update_data_array_list(data, method, norm_reward): #final_data, no_sa_data, no_sa_no_restarts_data, no_dag_data, no_groups_data, no_groups_no_structure_data, no_cheat_data):

    print('method for update', method)
    for element in range(len(data_labels)):
        if method == data_labels[element]:
            data[element] = np.append(data[element], norm_reward)

    print('data update',data)


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
    plt.xticks([1, 2, 3, 4, 5], data_labels_no_underscore, rotation=45, ha='right')


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
            #to_be_summed_list[element].append(json.loads(reward_list)) # if reward_list is '[1,2,3]' format not [1,2,3]
            to_be_summed_list[element].append(reward_list)

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


def generate_reward_list(path_to_intermediates, timestamp, do_skips_for_testing, num_rounds):

    '''
    for all files with given timestamp
        get best tree from almost last line in that file
        generateReward on particular world that stays the same
        add that reward to new_reward_list
    do until all done so new_reward_list has 50 elements all specific to that world
    '''

    seed = rospy.get_param('~seed')

    files = [f for f in listdir(path_to_intermediates)]

    # new_reward_list = [None]*50
    new_reward_list = [None]*num_rounds

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
                print('final best tree string', final_best_tree_string)
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


def generate_all_reward_lists(path_to_intermediates, to_be_summed_list, do_skips_for_testing, num_rounds):
    # Given the path to the output directory
    files = [f for f in listdir(path_to_intermediates)]

    for file_name in files:

        if 'round' not in file_name:
            timestamp = file_name[:13]
            method = get_method_type(file_name)
            new_reward_list = generate_reward_list(path_to_intermediates, timestamp, do_skips_for_testing, num_rounds)
            accumulate_method_lists(method, to_be_summed_list, new_reward_list)

    return to_be_summed_list

def update_convergence_plot(path, path_to_intermediates, do_skips_for_testing, num_rounds):
    # Given the path to the output directory
    files = [f for f in listdir(path)]
    #print(files)

    to_be_summed_list = initialize_convergence_data_lists() #each element of this list will be a list of lists
    convergence_data_list_list = initialize_convergence_data_lists() #each element will be a list of average best rewards for the element-specific method]

    # Generate rewards for each rounds best tree on same world, normalized wrt manual tree performance
    to_be_summed_list = generate_all_reward_lists(path_to_intermediates, to_be_summed_list, do_skips_for_testing, num_rounds)

    print('to_be_summed_list', to_be_summed_list)

    # Average best rewards for each round of all 50-round runs
    for i in range(len(to_be_summed_list)): # for each method
        element = to_be_summed_list[i]
        averaging_num = len(element)
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
    # plt.title('Average Best Reward')
    for i in range(len(convergence_data_list_list)):
        method_rewards = convergence_data_list_list[i]
        # plt.plot(method_rewards, label = data_labels_no_underscore[i])
        col = 'C' + str(data_labels_cmap_indices[i])
        method_error = convergence_errors[i]
        plt.errorbar(range(0,len(method_rewards)),method_rewards,method_error, color = col, label = data_labels_no_underscore[i], errorevery = 10, capsize = 3)
    plt.legend()
    plt.show()


if __name__ == '__main__':

    rospy.init_node('plot_results')

    # Get the config file etc
    rospack = rospkg.RosPack()
    filepath = rospack.get_path('mcts') + "/config/" + rospy.get_param('~config')
    with open(filepath, 'r') as stream:
        config = yaml.safe_load(stream)

    num_rounds = config['num_rounds']
    print('num rounds', num_rounds)

    do_skips_for_testing = False

    #num_worlds = input('For convergence plot, enter 0. For box plot, enter 1 for training world, and otherwise specify number of new worlds to test on: ')
    num_worlds = 0 # Always want convergence plot right now (For AI 535 Project)

    if num_worlds == 0:
        # data_labels_cmap_indices = [1,5,2,3,6,4] # order of colors setup to match the version of this code on graeme's branch
        data_labels_no_underscore = ['MCDAGS']#,'MCDAGS+NN']
        data_labels = ['no_sa']
        data_labels_cmap_indices = [3]
    else: # final tree comparison
        data_labels_no_underscore = ['MCDAGS+SA', 'No Default', 'MCTS+SA', 'MCDAGS', 'No Groups','No Structure','No Restarts']
        data_labels = ['final', 'no_cheat', 'no_dag', 'no_sa', 'no_groups', 'no_groups_no_structure', 'no_sa_no_restarts']


    # Specify path to all output files
    path = "/home/scheidee/Desktop/neural_mcdags_output/RESULTS/2022_05_28/plot_final"
    path_to_intermediates = "/home/scheidee/Desktop/neural_mcdags_output/RESULTS/2022_05_28/plot_intermediate"

    manual_word = createWord('? ( -> ( (wildlife_found) ? ( (in_comms) [go_to_comms] ) [report] ) -> ( (mine_found) ? ( <!> ( (is_armed) ) [disarm] ) ) -> ( ? ( <!> ( (carrying_benign) ) [take_to_drop_off] ) (benign_object_found) [pick_up] ) -> ( (likely_target_found) [go_to_likely_target] ) -> ( [coverage] ) )')

    if num_worlds != 0:
        update_box_plot(path,num_worlds,manual_word)
    else:
        update_convergence_plot(path, path_to_intermediates, do_skips_for_testing, num_rounds)

 