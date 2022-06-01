# Emily Scheide, June 2022

from cfg import Word, Character, CFG


# https://pytorch-geometric.readthedocs.io/en/latest/

# Neural network class

# Input is a behavior tree

# Output is a number representing how "good" that tree is

import torch
from torch_geometric.data import Data
import sys

class MCDAGSNet:
	def __init__(self, bt_word):
		self.bt_word = bt_word

		# Number of nodes
		# self.num_nodes = ...
		# self.num_node_features = ...

		#super()




def main():

	# Here is an simple training example example
	example = [1, .06, '-> ( condition1 ? ( condition2 action1 ) )']
	word = example[2]
	bt = word.createBT()
	print(BT)

if __name__ == '__main__':
	main()
