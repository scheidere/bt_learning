# Emily Scheide, June 2022

from cfg import Word, Character, CFG


# https://pytorch-geometric.readthedocs.io/en/latest/

# Neural network class

# Input is a behavior tree

# Output is a number representing how "good" that tree is

import torch
from torch_geometric.data import Data
import sys

import pickle

class MCDAGSNet:
    def __init__(self, bt_word):
        self.bt_word = bt_word

        # Number of nodes
        # self.num_nodes = ...
        # self.num_node_features = ...

        #super()




def main(pickle_path):

    # Here is an simple training example example
    # example = [1, .06, '-> ( condition1 ? ( condition2 action1 ) )']
    # word = example[2]
    # bt = word.createBT()
    # print(BT)



    data = []
    with open(pickle_path,'rb') as fr:
        try:
            while True:
                data.append(pickle.load(fr))
        except EOFError:
            pass
 
    print(data)

    for example in data:
        print(example)
        bt_word = example[-1]
        bt_word.printWord()
        root, bt = bt_word.createBT()
        print(bt)
        print(bt.nodes)
        test = bt.nodes
        print(len(bt.nodes))

    for node in test:
        print(node.label)

    print(torch.__version__)


if __name__ == '__main__':

    pickle_path = "/home/scheidee/Desktop/neural_mcdags_output/DATA/"
    file = "2examples1654332707545.p"
    pickle_path = pickle_path + file
    main(pickle_path)
