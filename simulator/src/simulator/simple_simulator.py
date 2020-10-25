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

from bt_interface import BT_Interface

import random
import copy
import math

def conditionNumToLabel(condition_num):
    return 'c' + str(condition_num)

def actionNumToLabel(action_num):
    return 'a' + str(action_num)

def conditionLabelToNum(condition_label):
    return int(condition_label[1:])

def actionLabelToNum(action_label):
    return int(action_label[1:])

class SimpleSimulator():
    def __init__(self, seed):
        # Currently ignored
        self.seed = seed
        self.N = 3

    

    def setConditions(self, bt_interface, condition_combination):

        # Convert to binary string, chop off the '0b' prefix
        binary = bin(condition_combination)
        binary = binary[2:]

        # Loop through from end
        binary_i = len(binary) - 1
        for i in xrange(self.N + 1):

            label = conditionNumToLabel(i)

            if binary_i >= 0:

                if binary[binary_i] == '0':
                    # turn off condition
                    # print(label, False)
                    bt_interface.setConditionStatus(label, False)
                else:
                    # turn on condition
                    # print(label, True)
                    bt_interface.setConditionStatus(label, True)
            else:
                # beyond length of binary number, treat as 0
                # turn off condition
                # print(label, False)
                bt_interface.setConditionStatus(label, False)

            # decrement counter
            binary_i -= 1

    def getCorrectAction(self, condition_combination):
        # multiply the condition numbers
        # (if none, default score is 1)

        # Convert to binary string, chop off the '0b' prefix
        binary = bin(condition_combination)
        binary = binary[2:]

        m = 1
        binary_i = len(binary) - 1
        for i in xrange(self.N + 1):

            if binary_i >= 0:

                if binary[binary_i] == '1':
                    m *= i
            else:
                break

            # decrement counter
            binary_i -= 1
        return m

    def setActions(self, bt_interface):
        # Just set them all to running
        for action_num in xrange(math.factorial(self.N) + 1):

            action_label = actionNumToLabel(action_num)
            bt_interface.setActionStatusRunning(action_label)

    def getActiveActionNum(self, active_actions):
        l = []
        for a in active_actions:

            l.append(actionLabelToNum(a))

            # !!Changed to only get the first one!! to prevent cheating by just making all of them active
            break

        return l

    def generateReward(self, word, max_iterations):

        debug = False

        try:
            

            # Create BT object from terminal BT CFG
            bt_root, bt = word.createBT()
            do_graphviz = False # False should make faster, but turns off GUI
            bt_interface = BT_Interface(bt, do_graphviz)

            if debug:
                print("run_simulator")
                word.printWord()

            # Set score
            score = 0
            max_score = 2**(self.N + 1)

            # Set all actions to running
            self.setActions(bt_interface)

            # Iterate through combinations of conditions
            for condition_combination in xrange( max_score ):

                if debug:
                    print('==================')
                    print('condition_combination', condition_combination)

                # Tell BT which conditions are true and false
                self.setConditions(bt_interface, condition_combination)

                # Do a BT tick
                bt_interface.tick_bt()

                # Check which action is active
                active_actions = bt_interface.getActiveActions()
                active_action_nums = self.getActiveActionNum( active_actions )
                if debug:
                    print('active_action_nums', active_action_nums)

                # Which action should be active?
                correct_action = self.getCorrectAction( condition_combination )
                if debug:
                    print('correct_action', correct_action)

                # Is the correct action active?
                if correct_action in active_action_nums:
                    score += 1
                    if debug:
                        print('score!')

            # Extra tick here to ensure active is computed correctly (I think)
            # bt_interface.tick_bt()

            # Normalize score
            if debug:
                print( 'score: ' + str(score) + " of " + str(max_score) ) 
            score = float(score) / float(max_score)



            # Get the Word of all active parts of the BT
            active_word = bt_interface.generateActiveCFGWord()
            if debug:
                print("active_word:")
                active_word.printWord()
            active_subtree_indices = bt_interface.getActiveSubtreeIndices()
            if debug:
                print('active_subtree_indices', active_subtree_indices)

            #test = [score,target_reported,belief_distance,active_word,active_subtree_indices]
            if debug:
                print('generateReward output', score, active_word, active_subtree_indices)

            return score, active_word, active_subtree_indices

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

def test(word, sim_iterations, seed):
    sim = UnderwaterSimulator(seed=seed)
    score, target_reported, belief_distance, active_word, active_subtree_indices = sim.generateReward(word, sim_iterations)
    word.printWord()
    print(sim.world.classes_y)
    print('Score: ', score)





if __name__ == "__main__":


    # Run with roslaunch mcts sim_test.launch

    rospy.init_node('simple_simulator')
    seed = rospy.get_param('~seed')

    # word_manual = createWord('? ( -> ( (c0) [a0] ) )')
    # word_manual = createWord('? ( -> ( (c0) [a0] ) -> ( (c2) (c3) [a6] ) )')
    # word_manual = createWord('? ( -> ( (c0) [a0] ) -> ( (c2) (c3) [a6] ) -> ( (c2) [a2] ) -> ( (c3) [a3] ) -> ( [a1] ) )')

    # word_manual = createWord('? ( -> ( <!> ( (c0) ) ? ( [a1] ) ) -> ( [a0] ) )')
    # word_manual = createWord('? ( -> ( [a0] [a2] [a1] ? ( <!> ( (c2) ) (c1) ) ) -> ( <!> ( (c0) ) [a1] ) )')
    word_manual = createWord('? ( -> ( <!> ( (c0) ) ? ( <!> ( (c2) ) [a2] ) (c1) ? ( [a1] ) ) -> ( <!> ( (c2) ) (c0) ? ( [a0] ) ) -> ( ? ( <!> ( (c2) ) [a0] ) [a1] ) )')

    

   



    simulator = SimpleSimulator(0)
    score, active_word, active_subtree_indices = simulator.generateReward(word_manual, 0) 
    print score






    '''
    character_list = [Character('?'),Character('('), Character('->'),Character('('),\
    Character('(target_found_90)'),Character('?'),Character('('),Character('(in_comms)'),\
    Character('[go_to_comms]'),Character(')'),Character(')'),Character('[shortest_path]'),Character(')')]
    word = Word(character_list)
    '''
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

    word1 = word_manual3
    word2 = word_rand_false_best
    #word2 = createWord('? ( -> ( (wildlife_found) ? ( [report] ) ? ( [go_to_comms] ) ) -> ( ? ( <!> ( (benign_object_found) ) [pick_up] ) ? ( (carrying_benign) ) ? ( [take_to_drop_off] ) ) -> ( (mine_found) [disarm] ) -> ( ? ( [go_to_likely_target] ) ) )')

    word3 = word_manual3
    word4 = word_rand_false_worst

    word5 = word_rand_false_best
    word6 = word_rand_false_worst

    word_manual_coverage = createWord('? ( -> ( (wildlife_found) ? ( (in_comms) [go_to_comms] ) [report] ) -> ( (mine_found) ? ( <!> ( (is_armed) ) [disarm] ) ) -> ( ? ( <!> ( (carrying_benign) ) [take_to_drop_off] ) (benign_object_found) [pick_up] ) -> ( (likely_target_found) [go_to_likely_target] ) -> ( [coverage] ) )') #-> ( [shortest_path] ) )') #-> ( [random_walk] ) )')
    test(word_manual_coverage, 200, seed)

    #compare(word1,word2,200)
    #compare(word3,word4,200)
    #compare(word5,word6,200)

    #word = createWord('? ( -> ( [report] ? ( (wildlife_found) ) ? ( [go_to_comms] ) ) -> ( [random_walk] ) )')
    #word = createWord('?  (  ->  (  ?  (  [report]  [go_to_comms]  )  ?  (  (at_surface)  )  <!>  (  (in_comms)  )  )  ->  (  ?  (  [random_walk]  )  )  ) ')
    #test(word)
    #test(word)
    '''

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