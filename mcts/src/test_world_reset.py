#!/usr/bin/env python

import numpy as np 
import matplotlib.pyplot as plt 
from cfg import createWord
from simulator.run_simulator import UnderwaterSimulator
from simulator.world import World
from os import listdir
from os.path import isfile, join

import rospy
import rospkg
import copy
import yaml



def run(config, seed):

	# create world
	world = World(config)
	do_test = True # don't error check graph
	world.init_world(seed, do_test)

	# print targets, i.e classes_y
	print('targets', world.classes_y)
	print(len(world.classes_y))

	# call reset
	world.reset_world()

	# print targets again
	print('targets', world.classes_y)
	print(len(world.classes_y))

if __name__ == '__main__':

	rospy.init_node('test_world_reset')

	# get config file
	rospack = rospkg.RosPack()
	filepath = rospack.get_path('simulator') + "/config/" + rospy.get_param('~sim_config')
	with open(filepath, 'r') as stream:
	    config = yaml.safe_load(stream)

	# get seed
	seed = rospy.get_param('~seed')
	print('SEED', seed)

	print("RUN 1")
	run(config, seed)
	print("RUN 2")
	run(config, seed)
