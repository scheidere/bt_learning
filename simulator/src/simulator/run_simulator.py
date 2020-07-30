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

from cfg import Word, Character, createWord
from robot import Robot, RobotController, TargetBelief
from world import World
from sensor_model import SensorModel

import random
import copy


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
        self.randomize_targets = self.config['randomize_targets']
        # seed = rospy.get_param('~seed')
        self.seed = 0 #random.randint(0,20) # random environment

        # Create the world
        self.world = World(self.config)
        do_test = True # don't error check graph

        self.world.init_world(self.seed, do_test)

    def update_worlds(self):

        self.world.randomize_targets() 

    def generateReward(self, word, max_iterations):

        try:
            '''
            character_list = [Character('?'),Character('('), Character('->'),Character('('),\
            Character('(target_found_90)'),Character('?'),Character('('),Character('(in_comms)'),\
            Character('[go_to_comms]'),Character(')'),Character(')'),Character('[shortest_path]'),Character(')')]
            word = Word(character_list)
            '''

            #print('classes_y',self.world.classes_y)

            # Re-randomize the worlds
            if self.randomize_targets:
                self.update_worlds()

            # Create BT object from terminal BT CFG
            bt_root, bt = word.createBT()

            print("run_simulator")
            word.printWord()
            #print("len(bt.nodes)", len(bt.nodes))

            robot = Robot(self.config, self.robot_id, self.num_robots, self.seed, bt, max_iterations, self.world)
            # cProfile.run('RobotController(config, robot)')
            robot_controller = RobotController(self.config, robot)
            score, target_reported, belief_distance = robot_controller.run()
            #print('Score: ', score)

            # Get the Word of all active parts of the BT
            active_word = robot.bt_interface.generateActiveCFGWord()

            return score, target_reported, belief_distance, active_word

        except rospy.ROSInterruptException: pass






if __name__ == "__main__":


    # Run with roslaunch mcts sim_test.launch

    rospy.init_node('underwater_simulator')

    '''
    character_list = [Character('?'),Character('('), Character('->'),Character('('),\
    Character('(target_found_90)'),Character('?'),Character('('),Character('(in_comms)'),\
    Character('[go_to_comms]'),Character(')'),Character(')'),Character('[shortest_path]'),Character(')')]
    word = Word(character_list)
    '''

    # Below used to test and compare different trees on the same sim map/set of targets

    word_manual = createWord('? ( -> ( (wildlife_found) ? ( (in_comms) [go_to_comms] ) [report] ) -> ( (mine_found) ? ( <!> ( (is_armed) ) [disarm] ) ) -> ( ? ( <!> ( (carrying_benign) ) [take_to_drop_off] ) (benign_object_found) [pick_up] ) -> ( (likely_target_found) [go_to_likely_target] ) -> ( [random_walk] ) )')
    word_no_likelytarget = createWord('? ( -> ( (wildlife_found) ? ( (in_comms) [go_to_comms] ) [report] ) -> ( (mine_found) ? ( <!> ( (is_armed) ) [disarm] ) ) -> ( ? ( <!> ( (carrying_benign) ) [take_to_drop_off] ) (benign_object_found) [pick_up] ) -> ( [random_walk] ) )')
    word_even_test = createWord('? ( -> ( ? ( <!> ( (carrying_benign) ) [take_to_drop_off] ) (benign_object_found) [pick_up] )  -> ( (mine_found) ? ( <!> ( (is_armed) ) [disarm] ) ) -> ( (wildlife_found) ? ( (in_comms) [go_to_comms] ) [report] ) -> ( [random_walk] ) )')
    word_report = createWord('? ( -> ( (wildlife_found) ? ( (in_comms) [go_to_comms] ) [report] ) -> ( [random_walk] ) )')
    word_pickdrop = createWord('? ( -> ( ? ( <!> ( (carrying_benign) ) [take_to_drop_off] ) (benign_object_found) [pick_up] ) -> ( [random_walk] ) )')
    sim = UnderwaterSimulator()
    original_target_locations = copy.copy(sim.world.classes_y)

    score, target_reported, belief_distance, active_word = sim.generateReward(word_manual, 200)
    print('1',sim.world.classes_y)
    '''
    print(original_target_locations == sim.world.classes_y)
    sim.world.classes_y = copy.copy(original_target_locations)
    score2, target_reported2, belief_distance2, active_word2 = sim.generateReward(word_report, 2000)
    print('orig', original_target_locations)
    print('2',sim.world.classes_y)
    print(original_target_locations == sim.world.classes_y)
    '''
    print('manual with target_belief:')
    print(score, target_reported, belief_distance, active_word)
    #print('manual without target_belief')
    #print(score2, target_reported2, belief_distance2, active_word2)
