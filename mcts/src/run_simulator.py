'''
Behavior Tree Reward Return 
(Skeleton code for future simulation-generated reward)
Emily Scheide
Oregon State University
March 2020
'''
from cfg import Word, Character
#from simulator.robot import init_bt, tick_bt, Robot, RobotController
import simulator

class UnderwaterSimulator():
    def __init__(self,word):
        self.word = word

    def generateReward(self):
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
            init_bt(bt)

            graphviz_pub = rospy.Publisher('behavior_tree_graphviz', String, queue_size=1)
            compressed_pub = rospy.Publisher('behavior_tree_graphviz_compressed', String, queue_size=1)

            tick_bt(bt)

            robot = Robot(config, robot_id, num_robots, seed, bt)
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
