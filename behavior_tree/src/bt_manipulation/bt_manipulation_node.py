#!/usr/bin/python
import rospy
from std_msgs.msg import String, Bool
import multirobot_behavior_tree # note this is not the standard behavior_tree!
import bt_manipulation
import cv2
import zlib
import os

def get_output_filename(config_filename):
    # return 'test_output.tree'
    # add a string to the filename to get the output filename
    # see https://stackoverflow.com/questions/37487758/how-to-add-an-id-to-filename-before-extension
    suffix = 'manipulated'
    return "{0}_{2}{1}".format(*os.path.splitext(config_filename) + (suffix,))

class BTManipulationNode:
    def __init__(self, config_filename):
        
        # Read in the given tree
        rospy.loginfo('reading in tree: ' + config_filename)
        self.tree1 = multirobot_behavior_tree.BehaviorTree(config_filename)
        self.tree2 = multirobot_behavior_tree.BehaviorTree(config_filename)

        # Manipulate the tree in some way
        # Pick some of the following options...
        rospy.loginfo('manipulating the tree...')
        bt_manipulation.reverse_first_level(self.tree1)
        self.tree = bt_manipulation.combine_two_trees(self.tree1, self.tree2)

        # Save the output to a new config file
        output_filename = get_output_filename(config_filename)
        rospy.loginfo('saving new config file to: ' + output_filename)
        self.save_tree(self.tree, output_filename)

    def save_tree(self, tree, output_filename):
        tree.write_config(output_filename)


if __name__ == '__main__':
    # Start the ROS node
    rospy.init_node('bt_manipulation_node')
    
    # Read in tree filename
    config_filename = rospy.get_param('~config', '')
    
    # Create an instance of BTManipulationNode (defined above)
    node = BTManipulationNode(config_filename)

    rospy.loginfo('bt_manipulation_node shutting down')
