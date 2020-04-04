#!/usr/bin/env python

'''
Behavior Tree Reward Return 
(Skeleton code for future simulation-generated reward)
Emily Scheide
Oregon State University
March 2020
'''

import rospy
import rospkg
import yaml
from std_msgs.msg import String

from cfg import Word, Character
from simulator.robot import Robot, RobotController
from simulator.world import World

import random


class UnderwaterSimulator():
    def __init__(self):
        self.create_worlds()

    def create_worlds(self):

        # Get the config file etc
        rospack = rospkg.RosPack()
        filepath = rospack.get_path('simulator') + "/config/" + rospy.get_param('~config')
        with open(filepath, 'r') as stream:
            self.config = yaml.safe_load(stream)
        self.robot_id = rospy.get_param('~robot_id')
        self.num_robots = rospy.get_param('~num_robots')
        # seed = rospy.get_param('~seed')
        self.seed = 0 #random.randint(0,20) # random environment

        # Create the world
        self.world = World(self.config)
        do_test = True # don't error check graph

        self.world.init_world(self.seed, do_test)

    def generateReward(self, word, max_iterations):

        try:
            '''
            character_list = [Character('?'),Character('('), Character('->'),Character('('),\
            Character('(target_found_90)'),Character('?'),Character('('),Character('(in_comms)'),\
            Character('[go_to_comms]'),Character(')'),Character(')'),Character('[shortest_path]'),Character(')')]
            word = Word(character_list)
            '''

            # Create BT object from terminal BT CFG
            bt_root, bt = word.createBT()

            robot = Robot(self.config, self.robot_id, self.num_robots, self.seed, bt, max_iterations, self.world)
            # cProfile.run('RobotController(config, robot)')
            robot_controller = RobotController(self.config, robot)
            score = robot_controller.run()
            #print('Score: ', score)
            return score

        except rospy.ROSInterruptException: pass






if __name__ == "__main__":

    rospy.init_node('underwater_simulator')

    character_list = [Character('?'),Character('('), Character('->'),Character('('),\
    Character('(target_found_90)'),Character('?'),Character('('),Character('(in_comms)'),\
    Character('[go_to_comms]'),Character(')'),Character(')'),Character('[shortest_path]'),Character(')')]
    word = Word(character_list)
    
    sim = UnderwaterSimulator()

    reward = sim.generateReward(word, 1000)

    print(reward)
