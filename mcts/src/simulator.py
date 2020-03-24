'''
Behavior Tree Reward Return 
(Skeleton code for future simulation-generated reward)
Emily Scheide
Oregon State University
March 2020
'''
from cfg import Word, Character

class TempSimulator():
	def __init__(self, cfg_string):
		self.cfg_string = cfg_string

	def simReward(self):
		'''
		Takes string and converts to object
		Then counts number of execution nodes (sequence or fallback)
		Reward increases as number aproaches 10, maximum at 10
		Reward is zero elsewhere
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


if __name__ == "__main__":

	test = Word([Character("->"),Character("("),Character("[]"),Character("?"),Character("("),Character("[]"),Character("()"),Character(")"),Character(")")])
	
	sim = TempSimulator(test)

	reward = sim.simReward()

	print(reward)
