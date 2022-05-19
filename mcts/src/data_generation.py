# Runs MCTS and saves BT and reward at each node
# Emily Scheide, Spring 2022

from data_gen_mcts import mcts
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


def generate_data():

	# Initialize ros node for MCDAGS called mcts
	rospy.init_node('mcts')

	# Create CFG object
    cfg = CFG()
    cfg_copy = copy.deepcopy(cfg)

	# Get config file
    config_filename = rospy.get_param('~config')
    rospack = rospkg.RosPack()
    filepath = rospack.get_path('mcts') + "/config/" + rospy.get_param('~config')
    with open(filepath, 'r') as stream:
        config = yaml.safe_load(stream)

    # Get parameters
    budget = config["budget"]
    max_mcts_iterations = config["max_mcts_iterations"]
    exploration_exploitation_parameter = config["exploration_exploitation_parameter"]
    max_sim_iterations = config["max_sim_iterations"]
    use_dag = config["use_dag"]
    shortcut_words = []

    # Get seed
    seed = rospy.get_param('~seed')

    # Run mcts
	[solution, best_rollout, root, list_of_all_nodes, winner, best_rollout_node, best_nodes_dict] = mcts( cfg_copy, budget, max_mcts_iterations, exploration_exploitation_parameter, max_sim_iterations, underwater_simulator, use_dag, config, shortcut_words_copy )
        



if __name__ == '__main__':

	start_time = time.time()
	generate_data()

