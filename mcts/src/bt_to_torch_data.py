# Emily Scheide, June 2022

from cfg import Word, Character, CFG, createWord, getActionsConditions
from behavior_tree.behavior_tree import Sequence, Fallback, Decorator, NotDecorator
import torch
from torch_geometric.data import Data
import sys

import pickle
import numpy as np


# class MCDAGSNet:
#     def __init__(self, bt_word):
#         self.bt_word = bt_word

#         # Number of nodes
#         # self.num_nodes = ...
#         # self.num_node_features = ...

#         #super()


class BT2TorchConversion:
    def __init__(self, pickle_path,file):

        self.final_pickle_path = pickle_path + file + 'torch.p' # Match initial output file name to final output file name, plus 'torch'
        self.test = False
        self.bt_word_data = self.getUnprocessBTData(pickle_path + file + '.p')
        self.unique_node_labels = self.getAllUniqueNodeLabels()

        if self.test:
            word = self.bt_word_data[1][-1]
            bt = self.word2BT(word)
            self.getNodeFeatureMatrix(bt)
            self.getEdgeIndexMatrix(bt)
        else:
            self.run()

    def run(self):

        # Walk through unprocessed data, example = [iteration, reward, bt_word]
        for example in self.bt_word_data:

            bt_word = example[-1]
            bt = self.word2BT(bt_word)
            edge_index = self.getEdgeIndexMatrix(bt) # Tensor, dtype long
            x = self.getNodeFeatureMatrix(bt) # Tensor, dtype float
            torch_data = Data(x=x, edge_index=edge_index)

            # Set y value equal to reward in example
            reward = example[1]
            torch_data.y = reward

            # Write Data objects to new pickle file
            pickle.dump(torch_data, open(self.final_pickle_path,'a+'))
        


    def getAllUniqueNodeLabels(self):

        actions,conditions = getActionsConditions()
        control_flows = [Sequence().label,Fallback().label,NotDecorator().label]

        return actions + conditions + control_flows

    def word2BT(self,word):

        root, bt = word.createBT()

        return bt

    def getUnprocessBTData(self, pickle_path):
        data = []
        with open(pickle_path,'rb') as fr:
            try:
                while True:
                    data.append(pickle.load(fr))
            except EOFError:
                pass

        return data

    def getNodeFeatureMatrix(self, bt):
        # Input is a bt object
        # Output is one-hot of shape [num_nodes, num_node_features] but as a tensor
        # Note num_node_features translates to number of unqiue node labels

        # Count total nodes in bt
        num_nodes = len(bt.nodes)

        # Get labels of nodes
        node_labels = []
        for node_obj in bt.nodes:
            node_labels.append(node_obj.label)

        # Count unique node labels
        num_node_features = len(self.unique_node_labels)

        # Init array with zeros
        x_arr = np.zeros((num_nodes,num_node_features))

        # Now create one-hot encoding
        for i in range(len(bt.nodes)):
            node_obj = bt.nodes[i]
            label_idx = self.unique_node_labels.index(node_obj.label)
            x_arr[i][label_idx] = 1

        x = torch.tensor(x_arr,dtype=torch.float)

        if self.test:
            print(node_labels, len(node_labels))
            print(self.unique_node_labels, len(self.unique_node_labels))
            print('x_arr',x_arr,x_arr.shape)
            print('x',x, x.shape)

        return x

    def getChildNodeIndices(self, node, bt_nodes):

        node_idx = bt_nodes.index(node)

        child_nodes = node.children

        # Current bt node order list, bt_nodes
        child_idxs = []
        for child in child_nodes:
            child_idxs.append(bt_nodes.index(child))


    def getEdgeIndexMatrix(self, bt):
        # Input is a bt object
        # Output is a matrix of shape [2,2*num_edges] but as a long tensor
        # Note it is 2*num_edges not just num_edges because it requires bidirectional edge definitions

        # A BT with n nodes has n-1 edges
        num_edges = len(bt.nodes) - 1

        # Init array with zeros
        ei_lst = []

        # Add edge information
        for node in bt.nodes:
            node_idx = bt.nodes.index(node)
            if node.children: # Look at control flow nodes only
                for child_node in node.children:
                    child_idx = bt.nodes.index(child_node)
                    # Count each edge twice
                    ei_lst.append([node_idx,child_idx]), ei_lst.append([child_idx, node_idx])


        ei_arr = np.array(ei_lst).T

        edge_index = torch.tensor(ei_arr,dtype=torch.long)
        if self.test:
            for i in range(len(bt.nodes)):
                node = bt.nodes[i]
                print(i, node.label)
            print("Need to print children to see which are children of which...")
            print(edge_index, edge_index.shape)
        return edge_index



def test(pickle_path):

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


    #+++++++++++++++ TESTING BELOW +++++++++++++++

    # Create simple bt for testing (node list is broken with this example; actions and conditions show up as None...)
    # bt_word = createWord(['?','(','c1','->','(','a1','a2',')','?','(','c2','a3',')',')'])
    # bt_word.printWord()
    # root, bt = bt_word.createBT()
    # print(bt)
    # print('root',bt.root)
    # print('root child', bt.root.children)
    # print('+++++++++++')
    # bt.generate_nodes_list()
    # print('+++++++++++')
    # print(bt.nodes)
    # bt.print_BT()

    # Example that works
    word = data[1][-1]
    word.printWord()
    root, bt = bt_word.createBT()
    print('Nodes', bt.nodes, len(bt.nodes))
    node_labels = []
    for node_obj in bt.nodes:
        node_labels.append(node_obj.label)
    print('node labels', node_labels, len(node_labels))
    print('Set', set(bt.nodes), len(set(bt.nodes)))
    print('set labels', set(node_labels), len(set(node_labels)))

    #edge_index = torch.tensor(...,dtype=torch.long)

    # Define x, the node feature matrix with shape [num_nodes, num_node_features]
    num_nodes = len(bt.nodes) # total number of nodes in bt
    print('num_nodes', num_nodes)
    num_node_features = len(set(bt.nodes)) # number of UNIQUE types of nodes in bt
    print('num_node_features', num_node_features)

    x_arr = np.array((num_nodes,num_node_features))
    x = torch.tensor(x_arr,dtype=torch.float)

    #torch_data = Data(x=x, edge_index=edge_index)




if __name__ == '__main__':

    pickle_path = "/home/scheidee/Desktop/neural_mcdags_output/DATA/"
    file = "2examples1654332707545"
    pickle_path = pickle_path
    #test(pickle_path)
    BT2TorchConversion(pickle_path,file)
