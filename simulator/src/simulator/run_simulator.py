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

import statistics as stats


class UnderwaterSimulator():
    def __init__(self, seed):
        self.create_worlds(seed)

    def create_worlds(self, seed):

        # Get the config file etc
        rospack = rospkg.RosPack()
        filepath = rospack.get_path('simulator') + "/config/" + rospy.get_param('~sim_config')
        with open(filepath, 'r') as stream:
            self.config = yaml.safe_load(stream)
        self.robot_id = rospy.get_param('~robot_id')
        self.num_robots = rospy.get_param('~num_robots')
        self.randomize_targets = self.config['randomize_targets']
        # seed = rospy.get_param('~seed')
        if seed:
            self.seed = seed
        else:
            self.seed = 0 #random.randint(0,20) # random environment

        # Create the world
        self.world = World(self.config)
        do_test = True # don't error check graph

        self.world.init_world(self.seed, do_test)

    def update_worlds(self):

        self.world.randomize_targets() 

    def reset_worlds(self):

        self.world.reset_world()

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
                # Randomizes world with new targets, all three types included
                self.update_worlds()
            else:
                # Resets world with same targets as previous round
                self.reset_worlds()

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
            print("active_word", active_word)
            active_subtree_indices = robot.bt_interface.getActiveSubtreeIndices()
            print('active_subtree_indices', active_subtree_indices)

            #test = [score,target_reported,belief_distance,active_word,active_subtree_indices]
            print('generateReward output', score,target_reported,belief_distance,active_word,active_subtree_indices)
            #print('number of outputs from generateReward', len(test))
            return score, target_reported, belief_distance, active_word, active_subtree_indices

        except rospy.ROSInterruptException: pass



def compare(word1, word2, sim_iterations, seed):
    sim = UnderwaterSimulator(seed=seed)
    ##original_target_locations = copy.copy(sim.world.classes_y)

    #print("1 before",sim.world.classes_y)
    #print('orig', original_target_locations)
    score, target_reported, belief_distance, active_word, active_subtree_indices = sim.generateReward(word1, sim_iterations)
    #print('1',sim.world.classes_y)
    
    #print(original_target_locations == sim.world.classes_y)

    # Reset target locations (what's the better way?)
    ##sim.world.classes_y = copy.copy(original_target_locations)
    
    #print('2 before', sim.world.classes_y)
    #print('orig', original_target_locations)
    score2, target_reported2, belief_distance2, active_word2, active_subtree_indices2 = sim.generateReward(word2, sim_iterations)
    #print('orig', original_target_locations)
    #print('2',sim.world.classes_y)
    #print(original_target_locations == sim.world.classes_y)
    
    #print('manual with target_belief:')
    word1.printWord()
    print('Score 1: ', score)
    #print('manual without target_belief')
    word2.printWord()
    print('Score 2: ', score2)

    return score, score2

def test(word, sim_iterations, seed):
    sim = UnderwaterSimulator(seed=seed)
    score, target_reported, belief_distance, active_word, active_subtree_indices = sim.generateReward(word, sim_iterations)
    word.printWord()
    print(sim.world.classes_y)
    print('Score: ', score)


def getComparisonStatistics(word1, word2, num_sims, num_sim_iters,seed):

    word1_scores = []
    word2_scores = []

    for i in range(num_sims):

        if rospy.is_shutdown():
            break

        score, score2 = compare(word1, word2, num_sim_iters, seed)
        word1_scores.append(score)
        word2_scores.append(score2)

    print("+++++++++++++++++++++++++++++++++++++")
    print("Before normalization")
    print(word1_scores)
    print(word2_scores)
    for i in range(len(word1_scores)):
        word1_scores[i] = float(word1_scores[i])/float(word2_scores[i])
        word2_scores[i] = 1 #manual tree gets 100% of what it gets haha
    print("After normalization")
    print(word1_scores)
    print(word2_scores)
    print("+++++++++++++++++++++++++++++++++++++")

    average1 = sum(word1_scores)/len(word1_scores)
    std_dev1 = stats.pstdev(word1_scores)
    average2 = sum(word2_scores)/len(word2_scores)
    std_dev2 = stats.pstdev(word2_scores)

    return (average1, std_dev1), (average2, std_dev2)

if __name__ == "__main__":


    # Run with roslaunch mcts sim_test.launch

    rospy.init_node('underwater_simulator')
    seed = rospy.get_param('~seed')
    '''
    character_list = [Character('?'),Character('('), Character('->'),Character('('),\
    Character('(target_found_90)'),Character('?'),Character('('),Character('(in_comms)'),\
    Character('[go_to_comms]'),Character(')'),Character(')'),Character('[shortest_path]'),Character(')')]
    word = Word(character_list)
    '''

    # Below used to test and compare different trees on the same sim map/set of targets

    word_manual = createWord('? ( -> ( (wildlife_found) ? ( (in_comms) [go_to_comms] ) [report] ) -> ( (mine_found) ? ( <!> ( (is_armed) ) [disarm] ) ) -> ( ? ( <!> ( (carrying_benign) ) [take_to_drop_off] ) (benign_object_found) [pick_up] ) -> ( (likely_target_found) [go_to_likely_target] ) -> ( [shortest_path] ) )') #-> ( [shortest_path] ) )') #-> ( [random_walk] ) )')
    word_manual2 = createWord('? ( -> ( (wildlife_found) ? ( (in_comms) [go_to_comms] ) [report] ) -> ( (mine_found) ? ( <!> ( (is_armed) ) [disarm] ) ) -> ( ? ( <!> ( (carrying_benign) ) [take_to_drop_off] ) (benign_object_found) [pick_up] ) -> ( [go_to_likely_target] ) )') #-> ( [shortest_path] ) )') #-> ( [random_walk] ) )')
    word_manual3 = createWord('? ( -> ( (wildlife_found) ? ( (in_comms) [go_to_comms] ) [report] ) -> ( (mine_found) ? ( <!> ( (is_armed) ) [disarm] ) ) -> ( ? ( <!> ( (carrying_benign) ) [take_to_drop_off] ) (benign_object_found) [pick_up] ) -> ( [go_to_new_vertex] ) )') #-> ( [shortest_path] ) )') #-> ( [random_walk] ) )')
    word_manual4 = createWord('? ( -> ( (wildlife_found) ? ( (in_comms) [go_to_comms] ) [report] ) -> ( (mine_found) ? ( <!> ( (is_armed) ) [disarm] ) ) -> ( ? ( <!> ( (carrying_benign) ) [take_to_drop_off] ) (benign_object_found) [pick_up] ) -> ( [shortest_path] ) )') #-> ( [shortest_path] ) )') #-> ( [random_walk] ) )')
    word_manual5 = createWord('? ( -> ( (wildlife_found) ? ( (in_comms) [go_to_comms] ) [report] ) -> ( (mine_found) ? ( <!> ( (is_armed) ) [disarm] ) ) -> ( ? ( <!> ( (carrying_benign) ) [take_to_drop_off] ) (benign_object_found) [pick_up] ) -> ( [random_walk] ) )') #-> ( [shortest_path] ) )') #-> ( [random_walk] ) )')
    word_no_likelytarget = createWord('? ( -> ( (wildlife_found) ? ( (in_comms) [go_to_comms] ) [report] ) -> ( (mine_found) ? ( <!> ( (is_armed) ) [disarm] ) ) -> ( ? ( <!> ( (carrying_benign) ) [take_to_drop_off] ) (benign_object_found) [pick_up] ) -> ( [random_walk] ) )')
    word_even_test = createWord('? ( -> ( ? ( <!> ( (carrying_benign) ) [take_to_drop_off] ) (benign_object_found) [pick_up] )  -> ( (mine_found) ? ( <!> ( (is_armed) ) [disarm] ) ) -> ( (wildlife_found) ? ( (in_comms) [go_to_comms] ) [report] ) -> ( [random_walk] ) )')
    word_report = createWord('? ( -> ( (wildlife_found) ? ( (in_comms) [go_to_comms] ) [report] ) -> ( [random_walk] ) )')
    word_pickdrop = createWord('? ( -> ( ? ( <!> ( (carrying_benign) ) [take_to_drop_off] ) (benign_object_found) [pick_up] ) -> ( [random_walk] ) )')
    word_disarm_random = createWord('? ( -> ( (mine_found) ? ( <!> ( (is_armed) ) [disarm] ) ) -> ( [random_walk] ) )')

    #word = createWord('?  (  ->  (  [random_walk]  )  ->  (  (wildlife_found)  ?  (  (in_comms)  [go_to_comms]  )  [report]  )  ->  (  (likely_target_found)  [go_to_likely_target]  )  ->  (  ?  (  <!>  (  (carrying_benign)  )  [take_to_drop_off]  )  (benign_found)  [pick_up]  )  ) ')

    #word1 = createWord('? ( -> ( (mine_found) ? ( <!> ( (is_armed) ) [disarm] ) ) -> ( (wildlife_found) ? ( (in_comms) [go_to_comms] ) [report] ) -> ( [random_walk] ) )')
    #word2 = createWord('? ( -> ( (mine_found) ? ( <!> ( (is_armed) ) [disarm] ) ) -> ( (wildlife_found) ? ( (in_comms) [go_to_comms] ) [report] ) -> ( ? ( <!> ( (carrying_benign) ) [take_to_drop_off] ) (benign_object_found) [pick_up] ) -> ( [random_walk] ) )')
    
    word_rand_false_best = createWord('? ( -> ( ? ( <!> ( (carrying_benign) ) [take_to_drop_off] ) ? ( (benign_object_found) ) ? ( [pick_up] ) ) -> ( (wildlife_found) (at_surface) (in_comms) [report] ) -> ( (is_armed) [disarm] ) -> ( [go_to_new_vertex] ) )')
    word_rand_false_worst = createWord('? ( -> ( (is_armed) [disarm] ) -> ( (benign_object_found) ? ( (carrying_benign) [pick_up] ) [take_to_drop_off] ) -> ( ? ( [report] ) ? ( (in_comms) ) ) )')

    #final_method_best_word = createWord('? ( -> ( (is_armed) [disarm] ) -> ( <!> ( (likely_target_found) ) [go_to_likely_target] ) -> ( (benign_object_found) ? ( <!> ( (carrying_benign) ) [take_to_drop_off] ) ? ( [pick_up] ) ) -> ( (in_comms) ? ( <!> ( (at_surface) ) [report] ) ? ( [go_to_comms] ) ) -> ( ? ( <!> ( (at_surface) ) [report] ) (wildlife_found) [go_to_comms] ) )')

    word1 = word_manual3
    word2 = word_rand_false_best
    #word2 = createWord('? ( -> ( (wildlife_found) ? ( [report] ) ? ( [go_to_comms] ) ) -> ( ? ( <!> ( (benign_object_found) ) [pick_up] ) ? ( (carrying_benign) ) ? ( [take_to_drop_off] ) ) -> ( (mine_found) [disarm] ) -> ( ? ( [go_to_likely_target] ) ) )')

    word3 = word_manual3
    word4 = word_rand_false_worst

    word5 = word_rand_false_best
    word6 = word_rand_false_worst

    word_manual_coverage = createWord('? ( -> ( (wildlife_found) ? ( (in_comms) [go_to_comms] ) [report] ) -> ( (mine_found) ? ( <!> ( (is_armed) ) [disarm] ) ) -> ( ? ( <!> ( (carrying_benign) ) [take_to_drop_off] ) (benign_object_found) [pick_up] ) -> ( (likely_target_found) [go_to_likely_target] ) -> ( [coverage] ) )') #-> ( [shortest_path] ) )') #-> ( [random_walk] ) )')
    final_method_best_word = createWord('? ( -> ( (benign_object_found) [pick_up] ) -> ( (wildlife_found) <!> ( (in_comms) ) ? ( (at_surface) [report] ) [go_to_comms] ) -> ( (is_armed) [disarm] ) -> ( (benign_object_found) ) -> ( (carrying_benign) [take_to_drop_off] ) -> ( [go_to_likely_target] ) )')


    ###test(final_method_best_word, 200, seed)
    ###score, score2 = compare(final_method_best_word,word_manual_coverage,200,seed)
    (average1, std_dev1), (average2, std_dev2) = getComparisonStatistics(final_method_best_word, word_manual_coverage, 100, 200, seed)
    print((average1, std_dev1), (average2, std_dev2))
    #compare(word1,word2,200)
    #compare(word3,word4,200)
    #compare(word5,word6,200)

    #word = createWord('? ( -> ( [report] ? ( (wildlife_found) ) ? ( [go_to_comms] ) ) -> ( [random_walk] ) )')
    #word = createWord('?  (  ->  (  ?  (  [report]  [go_to_comms]  )  ?  (  (at_surface)  )  <!>  (  (in_comms)  )  )  ->  (  ?  (  [random_walk]  )  )  ) ')
    #test(word)
    #test(word)


    '''
    # Testing disarm subtree, looking for bug found during simulated annealing
    for seed in range(100):
        if rospy.is_shutdown():
            break
        print('Starting disarm subtree test ' + str(seed))
        sim = UnderwaterSimulator(seed)
        score, target_reported, belief_distance, active_word, active_subtree_indices = sim.generateReward(word_disarm_random, 200)
        print("Final score: " + str(score))
    '''