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

#data_labels_no_underscore = ['final', 'no sa', 'no sa\nno restarts', 'no dag','no groups','no groups\nno structure','no cheat']
#data_labels = ['final', 'no_sa', 'no_sa_no_restarts', 'no_dag','no_groups','no_groups_no_structure','no_cheat']
#data_labels_no_underscore = ['final', 'no sa', 'no dag','no groups','no cheat']
#data_labels = ['final', 'no_sa', 'no_dag','no_groups','no_cheat']
data_labels_no_underscore = ['final', 'no cheat', 'no dag', 'no sa', 'no groups']
data_labels = ['final', 'no_cheat', 'no_dag', 'no_sa', 'no_groups']


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
			print('label', label)
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
			to_be_summed_list[element].append(json.loads(reward_list))

def extract_reward_list(path,file):
	open_file = open(path + '/' + file, 'r')
	lines = open_file.readlines()
	temp = lines[6] 

	# Remove '\n'
	return temp[:-1]



def update_convergence_plot(path):
	# Given the path to the output directory
	files = [f for f in listdir(path)]
	#print(files)

	to_be_summed_list = initialize_convergence_data_lists() #each element of this list will be a list of lists
	convergence_data_list_list = initialize_convergence_data_lists() #each element will be a list of average best rewards for the element-specific method]

	for file_name in files:

		# Extract method
		method = get_method_type(file_name)

		# Extract reward list (one best reward per round so length of 50)
		reward_list = extract_reward_list(path, file_name)


		# Sort reward_list into correct method element in to_be_summed_list
		accumulate_method_lists(method, to_be_summed_list, reward_list)


	print('to_be_summed_list', to_be_summed_list)
	#for i in range(len(to_be_summed_list)):
	#	print('test',len(el))
	#	for i in range(len(el)):
	#		el2 = el[i]
	#		print('test2', el2)
	#		print('len', len(el2))

	# Average best rewards for each round of all 50-round runs
	for i in range(len(to_be_summed_list)): # for each method
		element = to_be_summed_list[i]
		averaging_num = len(element)
		for j in range(len(element)): # for each 50-round run, i.e. each reward list
			reward_list = to_be_summed_list[i][j]
			for k in range(len(reward_list)): #for each best reward (per round)
				if len(convergence_data_list_list[i]) < k+1:
					convergence_data_list_list[i].append(0)
				print('reward_list[k]', reward_list[k])
				convergence_data_list_list[i][k] += reward_list[k] #sum with other nums for that specific round and method

		# Once a method is completely summed from all 50-round runs, get average
		for a in range(len(convergence_data_list_list[i])):
			convergence_data_list_list[i][a] = convergence_data_list_list[i][a]/averaging_num


	# Plot each method
	x = range(len(reward_list)) #len=50
	y = convergence_data_list_list
	plt.xlabel('Rounds')
	plt.ylabel('Reward')
	plt.title('Average Best Reward')
	for i in range(len(convergence_data_list_list)):
		method_rewards = convergence_data_list_list[i]
		plt.plot(method_rewards, label = data_labels[i])
	plt.legend()
	plt.show()


if __name__ == '__main__':

	rospy.init_node('plot_results')

	num_worlds = input('Enter 1 for training world, and otherwise specify number of new worlds to test on: ')
	print('test')
	# Specify path to all output files
	path = "/home/scheidee/Desktop/bt_learning_output/plottable_output"

	manual_word = createWord('? ( -> ( (wildlife_found) ? ( (in_comms) [go_to_comms] ) [report] ) -> ( (mine_found) ? ( <!> ( (is_armed) ) [disarm] ) ) -> ( ? ( <!> ( (carrying_benign) ) [take_to_drop_off] ) (benign_object_found) [pick_up] ) -> ( (likely_target_found) [go_to_likely_target] ) -> ( [coverage] ) )')

	if num_worlds != 0:
		update_box_plot(path,num_worlds,manual_word)
	else:
		update_convergence_plot(path)

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