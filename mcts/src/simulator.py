'''
Behavior Tree Reward Return 
(Skeleton code for future simulation-generated reward)
Emily Scheide
Oregon State University
March 2020
'''
from cfg import Word, Character

'''
class TempSimulator():
	def __init__(self, cfg_string):
		self.cfg_string = cfg_string

	def simReward(self):
		'''
		# Takes string and converts to object
		# Then counts number of execution nodes (sequence or fallback)
		# Reward increases as number aproaches 10, maximum at 10
		# Reward is zero elsewhere
		'''
		reward = 0
		count_execution_nodes = 0

		# Input cfg string is an instance of the cfg Word class

		# Create behavior tree (object)
		bt_root, bt = self.cfg_string.createBT()

		# Get a reward from the object

		# Example: count execution nodes (i.e. sequence + fallback)
		for node in bt.nodes:
			#print(node)
			if node.label == u'\u2192' or node.label == '?':
				#print(node)
				count_execution_nodes += 1

		if count_execution_nodes < 0:
	 			count_execution_nodes = 0

		if count_execution_nodes <= 10:
			reward = count_execution_nodes/10.0 
		else:
			reward = 0

		return reward

'''

# Outline of Simulator classes below

class Robot():
	def __init__(self, actions, conditions, num_robots):
		self.actions = actions
		self.conditions = conditions
		self.num_robots = num_robots

	def generateRobots(self):
		pass

	def moveRobotCircle(self):
		pass

	def moveRobotZigZag(self):
		pass

	def moveRobotWallFollow(self):
		pass

	def takeAction(self,condition):
		# If condition 1 do action 1

		# If condition 2 do action 2

		#...

		# Otherwise do nothing?

class Environment():
	def __init__(self, num_targets, num_obstacles):
		self. num_targets = num_targets
		self.num_obstacles = num_obstacles

	def generateObstacles(self):
		pass

	def communicationModel(self):
		pass

class Sensor():
	def __init__(self):
		pass

		# Isn't this where the uncertainty should be incorporated (i.e. noise since sensors are imperfect)?

		# Need method of determining (i.e. sensing) that an object is a target with some uncertainty

	def senseObject(self):
		# Return None if no objects in range

		# Return Target or non-target if object within range
		pass

class Target():
	def __init__(self):
		pass
		#target could be moving or stationary

		# if target is a class shouldn't obstacles also be? or vice versa?

	def generateTargets(self):
		pass 

	def moveTarget(self):
		pass







if __name__ == "__main__":

	test = Word([Character("->"),Character("("),Character("[]"),Character("?"),Character("("),Character("[]"),Character("()"),Character(")"),Character(")")])
	
	sim = TempSimulator(test)

	reward = sim.simReward()

	print(reward)
