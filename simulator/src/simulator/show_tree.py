#!/usr/bin/env python

import rospy
import yaml
import rospkg
from cfg import CFG, Word, Character, createWord

from behavior_tree.behavior_tree import *
from behavior_tree_msgs.msg import Status, Active

import behavior_tree.behavior_tree_graphviz as gv
import zlib

def init_bt(bt):
    # print("BT_Interface initialising BT...")
    for node in bt.nodes:
        node.init_ros()
        # print(node.label)
    # print("BT finished init")

def tick_bt(bt):
    bt.tick()#root.tick(True)

    source = gv.get_graphviz(bt)
    source_msg = String()
    source_msg.data = source
    graphviz_pub.publish(source_msg) 

    compressed = String()
    compressed.data = zlib.compress(source)
    compressed_pub.publish(compressed)

if __name__ == '__main__':

	# Initialise the node
    rospy.init_node('show_tree')
    # Get the config file etc
    rospack = rospkg.RosPack()
    filepath = rospack.get_path('simulator') + "/config/" + rospy.get_param('~config')
    with open(filepath, 'r') as stream:
        config = yaml.safe_load(stream)
    robot_id = rospy.get_param('~robot_id')
    num_robots = rospy.get_param('~num_robots')
    seed = rospy.get_param('~seed')

    graphviz_pub = rospy.Publisher('behavior_tree_graphviz', String, queue_size=1)
    compressed_pub = rospy.Publisher('behavior_tree_graphviz_compressed', String, queue_size=1)

    try:

        # Setup a simple BT
        #character_list = [Character('?'),Character('('), Character('->'),Character('('),\
            #Character('(target_found_90)'),Character('?'),Character('('),Character('(in_comms)'),\
            #Character('[go_to_comms]'),Character(')'),Character('[report]'),Character(')'),Character('[go_to_belief]'),Character(')')]
        
        #test
        #character_list = [Character('->'),Character('('),Character('[report]'),Character('[go_to_belief]'),Character('[random_walk]'),Character(')')]

        #single robot single target mcts generated tree - not great
        #character_list = [Character('->'),Character('('),Character('[go_to_belief]'),Character(')')]

        #onr report manual tree
        
        '''
        character_list = [Character('?'),Character('('),\
        	Character('?'),Character('('),\
        	Character('<!>'),Character('('),\
        	Character('(battery_low)'),Character(')'),Character('[resurface]'),Character(')'),\
        	Character('->'),Character('('),\
        	Character('(wildlife_found)'),Character('?'),Character('('),\
        	Character('(in_comms)'),Character('[go_to_comms]'),Character(')'),Character('[report]'),Character(')'),\
        	Character('->'),Character('('),\
        	Character('(mine_found)'),Character('?'),Character('('),\
        	Character('<!>'),Character('('),\
        	Character('(is_armed)'),Character(')'),Character('[disarm]'),Character(')'),Character(')'),\
        	Character('->'),Character('('),\
        	Character('(benign_object_found)'),Character('[pick_up]'),Character('[take_to_drop_off]'),Character(')'),\
        	Character('->'),Character('('),\
        	Character('?'),Character('('),\
        	Character('(likely_target_found)'),Character('[go_to_target]'),Character(')'),Character('random_walk'),Character(')'),\
        	Character(')')]
        '''
        '''
        character_list = [Character('?'),Character('('),\
        	Character('->'),Character('('),\
        	Character('(battery_low)'),Character('[resurface]'),Character(')'),\
        	Character('->'),Character('('),\
        	Character('(wildlife_found)'),Character('?'),Character('('),\
        	Character('(in_comms)'),Character('[go_to_comms]'),Character(')'),Character('[report]'),Character(')'),\
        	Character('->'),Character('('),\
        	Character('(mine_found)'),Character('?'),Character('('),\
        	Character('<!>'),Character('('),\
        	Character('(is_armed)'),Character(')'),Character('[disarm]'),Character(')'),Character(')'),\
        	Character('->'),Character('('),\
        	Character('(benign_object_found)'),Character('[pick_up]'),Character('[take_to_drop_off]'),Character(')'),\
        	Character('->'),Character('('),\
        	Character('?'),Character('('),\
        	Character('(likely_target_found)'),Character('[go_to_target]'),Character(')'),\
        	Character('[random_walk]'),Character(')'),\
        	Character(')')]
        '''
        '''
        # updated multi-target manual tree
        character_list = [Character('?'),Character('('),\
            Character('->'),Character('('),\
            Character('(battery_low)'),Character('[resurface]'),Character(')'),\
            Character('->'),Character('('),\
            Character('(wildlife_found)'),Character('?'),Character('('),\
            Character('(in_comms)'),Character('[go_to_comms]'),Character(')'),Character('[report]'),Character(')'),\
            Character('->'),Character('('),\
            Character('(mine_found)'),Character('?'),Character('('),\
            Character('<!>'),Character('('),\
            Character('(is_armed)'),Character(')'),Character('[disarm]'),Character(')'),Character(')'),\
            Character('->'),Character('('),\
            Character('(benign_object_found)'),Character('[pick_up]'),Character(')'),\
            Character('->'),Character('('),\
            Character('(carrying_benign)'),Character('[take_to_drop_off]'),Character(')'),\
            Character('->'),Character('('),\
            Character('(likely_target_found)'),Character('[go_to_likely_target]'),Character(')'),\
            Character('[random_walk]'),\
            Character(')')]
        '''
        '''
        character_list = [Character('?'),Character('('),\
            Character('->'),Character('('),\
            Character('->'),Character('('),\
            Character('?'),Character('('),\
            Character('<!>'),Character('('),\
            Character('(likely_target_found)'),Character(')'),\
            Character('(is_armed)'), Character(')'),\
            Character('[random_walk]'),Character(')'),\
            Character('(carrying_benign)'),Character(')'),\
            Character('[pick_up]'),Character(')')]
        '''
        
        '''    
        character_list = [Character('?'),Character('('),\
            Character('?'),Character('('),\
            Character('->'),Character('('),\
            Character('(mine_found)'),Character('[disarm]'),Character(')'),\
            Character('[shortest_path]'),Character(')'),\
            Character('[go_to_comms]'),Character(')')]


        cfg_word = Word(character_list)
        '''
        cfg_word = createWord('? ( ? ( -> ( (mine_found) [disarm] ) [shortest_path] ) [go_to_comms] )')

        bt_root, bt = cfg_word.createBT()

        init_bt(bt)
        #bt.write_config('onr_example2.tree') # need to manually add in decorator nodes to config file/ implement it dur
        while not rospy.is_shutdown():   
        	tick_bt(bt)

    except rospy.ROSInterruptException: pass