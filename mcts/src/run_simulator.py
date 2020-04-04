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


class UnderwaterSimulator():
    def __init__(self,word):
        self.word = word

    def generateReward(self, max_iterations):
        # Get the config file etc
        rospack = rospkg.RosPack()
        filepath = rospack.get_path('simulator') + "/config/" + rospy.get_param('~config')
        with open(filepath, 'r') as stream:
            config = yaml.safe_load(stream)
        robot_id = rospy.get_param('~robot_id')
        num_robots = rospy.get_param('~num_robots')
        seed = rospy.get_param('~seed')

        try:

            # Create BT object from terminal BT CFG
            bt_root, bt = self.word.createBT()

            robot = Robot(config, robot_id, num_robots, seed, bt, max_iterations)
            # cProfile.run('RobotController(config, robot)')
            robot_controller = RobotController(config, robot)
            score = robot_controller.run()
            #print('Score: ', score)
            return score

        except rospy.ROSInterruptException: pass






if __name__ == "__main__":

    test = Word([Character("->"),Character("("),Character("[]"),Character("?"),Character("("),Character("[]"),Character("()"),Character(")"),Character(")")])
    
    sim = TempSimulator(test)

    reward = sim.simReward()

    print(reward)
