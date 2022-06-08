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
    def __init__(self, pickle_path,file, is_terminal_data,nonterminal_char_words):

        self.is_terminal_data = is_terminal_data
        self.final_pickle_path = pickle_path + file + 'torch.p' # Match initial output file name to final output file name, plus 'torch'
        self.test = True
        self.bt_word_data = self.getUnprocessBTData(pickle_path + file + '.p')
        self.nonterminal_char_words = nonterminal_char_words
        self.unique_node_labels = self.getAllUniqueNodeLabels()

        #print('hello',self.unique_node_labels, len(self.unique_node_labels))

        if self.test:
            if self.is_terminal_data:
                word = self.bt_word_data[1][-1] # TERMINAL INPUT DATA: [iter, reward, terminal bt word]
                bt = self.word2BT(word)
                self.getNodeFeatureMatrix(bt)
                self.getEdgeIndexMatrix(bt)
            else: # is nonterminal
                # Can't convert to bt object, because nonterminal nodes are not behavior tree nodes
                word = self.bt_word_data[1][0] # NONTERMINAL INPUT DATA: [nonterminal bt word, reward]
                word_labels, word_labels_with_parens = self.getWordCharlabels(word)
                x = self.getNodeFeatureMatrixNONTERMINAL(word_labels, word_labels_with_parens)
                edge_index = self.getEdgeIndexMatrixNONTERMINAL(word_labels, word_labels_with_parens)
                self.createTempBT(word_labels, word_labels_with_parens)
        else:
            self.run()

    def run(self):

        with open(self.final_pickle_path, 'ab') as f:

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
                pickle.dump(torch_data, f)

    def getWordCharlabels(self, word):

        # Get char labels, with and without parentheses

        labels = []
        labels_with_parentheses = []
        for char in word.list:
            char_string = char.toString()
            if len(char_string) > 1 and char_string[0] == '(' or char_string[0] == '[':
                # sequence, [action_string], (condition_string) for e.g.
                # we want to remove the brackets within the string
                char_string = char_string[1:-1]
            if char_string != '(' and char_string != ')':
                labels.append(char_string)
            labels_with_parentheses.append(char_string)

        #print(labels, labels_with_parentheses)

        return labels, labels_with_parentheses
          

    def getNonTerminalCharLabels(self):

        nonterminal_char_labels = []
        for word in self.nonterminal_char_words:
            nonterminal_char_labels.append(word.toString())

        return nonterminal_char_labels

    def getAllUniqueNodeLabels(self):

        actions,conditions = getActionsConditions()
        control_flows = [Sequence().label,Fallback().label,NotDecorator().label]
        terminal_labels = actions + conditions + control_flows

        if self.is_terminal_data:
            actions,conditions = getActionsConditions()
            control_flows = [Sequence().label,Fallback().label,NotDecorator().label]
            return actions + conditions + control_flows

        else:
            nonterminal_char_labels = self.getNonTerminalCharLabels()
            control_flows = ['->',Fallback().label,NotDecorator().label]
            terminal_labels = actions + conditions + control_flows# with edit because arrow and '->' not equivalent
            return terminal_labels + nonterminal_char_labels



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

    def getNodeFeatureMatrixNONTERMINAL(self, word_labels, word_labels_with_parens):
        # Input is two lists, one with just labels of nodes (terminal and nonterminal)
        # the second is the same but with parenthesis to denote children/parental connections

        # Output is one-hot of shape [num_nodes, num_node_features] but as a tensor
        # Note num_node_features translates to number of unqiue node labels

        # Count total nodes in bt
        num_nodes = len(word_labels)

        # Count unique node labels
        num_node_features = len(self.unique_node_labels) # should be 112 for noterminal data

        # Init array with zeros
        x_arr = np.zeros((num_nodes,num_node_features))

        # Now create one-hot encoding
        for i in range(num_nodes):
            label = word_labels[i]
            label_idx = self.unique_node_labels.index(label)
            print(label, label_idx)
            x_arr[i][label_idx] = 1

        x = torch.tensor(x_arr,dtype=torch.float)

        if self.test:
            print(self.unique_node_labels, len(self.unique_node_labels))
            print('x_arr',x_arr,x_arr.shape)
            print('x',x, x.shape)

        #print(x)

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

    def getEdgeIndexMatrixNONTERMINAL(self, word_labels, word_labels_with_parens):
        # Input is a list of chars in given bt word, with parenthesis denoting relations
        # Output is a matrix of shape [2,2*num_edges] but as a long tensor
        # Note it is 2*num_edges not just num_edges because it requires bidirectional edge definitions

        # A BT with n nodes has n-1 edges
        num_edges = len(word_labels) - 1

        # Init array with zeros
        ei_lst = []

        # Add edge information
        # for i in range(len(word_labels)):
        #     node_label = word_labels[i]
        #     node_idx = word_labels.index(node_label)
        #     print(node_idx)

        num_found = 0
        potential_child_idx = None
        for i in range(len(word_labels_with_parens)-1):
            # if potential_child_idx:
            #     i = potential_child_idx
            char_string = word_labels_with_parens[i]
            next_char_string = word_labels_with_parens[i+1]
            print(char_string,next_char_string)
            if char_string in word_labels: # excludes '(' and ')'
                node_idx = word_labels.index(char_string)
                print(node_idx)
                if next_char_string == '(': # found parent
                    print('is_parent')
                    idx_of_next = word_labels_with_parens.index(next_char_string)
                    potential_child_idx = i+2
                    potential_child = word_labels_with_parens[potential_child_idx]
                    count_children = 0
                    while potential_child != ')':
                        count_children+=1
                        potential_child_idx += 1
                        potential_child = word_labels_with_parens[potential_child_idx]
                    num_found+= count_children
        print(num_found)



        # Add edge information
        # for char_string in word_labels:
        #     node_idx = word_labels.index(char_string)
        #     if node.children: # Look at control flow nodes only
        #         for child_node in node.children:
        #             child_idx = bt.nodes.index(child_node)
        #             # Count each edge twice
        #             ei_lst.append([node_idx,child_idx]), ei_lst.append([child_idx, node_idx])


        ei_arr = np.array(ei_lst).T

        edge_index = torch.tensor(ei_arr,dtype=torch.long)
        # if self.test:
        #     for i in range(len(bt.nodes)):
        #         node = bt.nodes[i]
        #         print(i, node.label)
        #     print("Need to print children to see which are children of which...")
        #     print(edge_index, edge_index.shape)
        return edge_index

    def createTempBT(self, word_labels, word_labels_with_parens):        
    
        nodes_worklist = []
        root = None
        
        for i in range(len(word_labels_with_parens)-1):

            char_label = word_labels_with_parens[i]
            #char.printLabel()
            next_char_label = word_labels_with_parens[i+1]
            #next_char.printLabel()

            node = TempNode(char_label,children=[])
            # print('new node', node, node.label, node.children)

            # Check if it is the root node, and if so add to list
            if root == None:
                root = node
                nodes_worklist.append(node)
                continue

            # print('worklist', nodes_worklist)

            # Check for "(" after a node character, denoting the latter is a parent node
            if next_char_label == '(':
                # Current node (char) is a child of current parent but also a parent itself
                # Add it as a child to its parent
                parent = nodes_worklist[-1]
                parent.add_child(node)
                # Add it to the worklist so its children can be added subsequently
                nodes_worklist.append(node)
                # print('parent1', parent.label)
                # child_labels = []
                # for child in parent.children:
                #     child_labels.append(child.label)
                # print('children', child_labels)
                # test = input('wait')
                
            elif char_label == ')':
                # Done with children of most recent parent
                nodes_worklist.pop()
                parent = nodes_worklist[-1]
                
            elif char_label != '(':
                # Remember each child node of current parent
                parent = nodes_worklist[-1]
                parent.add_child(node)
                # print('parent2', parent.label)
                # child_labels = []
                # for child in parent.children:
                #     child_labels.append(child.label)
                # print('children', child_labels)
                # test = input('wait')

        print("+++++++++++++++++++++++++++++")
        # print('UMMM',root, root.children)
        # for child in root.children:
        #     print(child.label)
        #     print(child.children)
        #     for c in child.children:
        #         print(c.label)
        print('root', root.label)
        print('root.children', root.printChildLabels())
        for child in root.children:
            print('child', child.label)
            print('child.children', child.printChildLabels())


class TempNode:

    # Could have terminal or noterminal label
    # Not a real BT node

    def __init__(self,label,children = []):

        self.label = label
        self.children = children

    def add_child(self,node):
        self.children.append(node)

    def printChildLabels(self):
        child_labels = []
        for child in self.children:
            child_labels.append(child.label)
        # print('children', child_labels)
        return child_labels

def test(pickle_path):
    pass



def getTorchData(new_path):

    data = []
    with open(new_path,'rb') as fr:
        try:
            while True:
                data.append(pickle.load(fr))
        except EOFError:
            pass

    return data

def getGrammarData(char_pickle_path):

    with open(char_pickle_path, 'rb') as f:

        data_list = pickle.load(f)

    return data_list


if __name__ == '__main__':

    # TERMINAL
    # pickle_path = "/home/scheidee/Desktop/neural_mcdags_output/DATA/"
    # #file = "2examples1654332707545"
    # file = '10000examples1654535066918'
    # is_terminal_data = True

    #NONTERMINAL
    pickle_path = "/home/scheidee/Desktop/neural_mcdags_output/DATA/"
    file = '10000examples1654670294773nonterminal_'
    is_terminal_data = False

    char_pickle_path = "/home/scheidee/Desktop/neural_mcdags_output/DATA/nonterminal_char_words.p"
    nonterminal_chars = getGrammarData(char_pickle_path)

    # The following call will convert the give pickle file into one with equivalent torch.geometric.data objects
    BT2TorchConversion(pickle_path,file,is_terminal_data, nonterminal_chars)

    # The new pickle file can be read like this if using python3
    new_path = '/home/scheidee/Desktop/neural_mcdags_output/DATA/'
    # file = '2examples1654332707545torch.p'
    #file = '1500ish_examplestorch.p'
    file = file + 'torch.p'
    new_path += file

    data = getTorchData(new_path)
    print(data,len(data))