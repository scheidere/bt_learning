#!/usr/bin/env python

import numpy as np 
from cfg import Character, Word, createWord

import itertools
import copy

import rospy

class State():
    def __init__(self, state_list, known_subtree_words):
        self.state_list = state_list # ex. [1,5,2]
        self.known_subtree_words = known_subtree_words #list of words

    def numToSubtreeWord(self, num):
        return self.known_subtree_words[num]

    def stateToFulltreeWord(self):
        if len(self.state_list) == 0:
            return None
        char_list = []
        char_list.append(Character("?"))
        char_list.append(Character("("))
        for num in self.state_list:
            char_list += self.numToSubtreeWord(num).list
        char_list.append(Character(")"))
        state_word = Word(char_list)
        return state_word

    def stateToBT(self):
        if len(self.state_list) == 0:
            return None
        char_list = []
        char_list.append(Character("?"))
        char_list.append(Character("("))
        for num in self.state_list:
            char_list += self.numToSubtreeWord(num).list
        char_list.append(Character(")"))
        state_word = Word(char_list)
        root, state_BT = state_word.createBT()
        return state_BT


class Neighbors():
    def __init__(self, state):
        self.state = state
        self.state_list = self.state.state_list
        self.known_subtree_words = self.state.known_subtree_words

    def swapAll(self):
        '''
        Returns all new lists (a list of lists) obtained by swapping the order of the numbers
        '''
        swap_list_of_neighbor_lists = []
        # Check if no subtrees are present
        if len(self.state_list) == 0:
            return swap_list_of_neighbor_lists
        swapped = list(itertools.permutations(self.state_list)) #list of tuples
        swapped.remove(tuple(self.state_list))
        # CHANGE: swap all possible PAIRS (use double for loop)
        for tupl in swapped:
            swap_list_of_neighbor_lists.append(list(tupl))

        return swap_list_of_neighbor_lists

    def deleteAll(self):
        '''
        Returns all new lists obtained by removing an individual number
        '''
        delete_list_of_neighbor_lists = []
        #print('state_list',self.state_list)
        if len(self.state_list) == 0:
            return delete_list_of_neighbor_lists
        for num in self.state_list:
            #print(self.state_list)
            new_list = copy.copy(self.state_list)
            new_list.remove(num)
            #print(new_list)
            delete_list_of_neighbor_lists.append(new_list)
        
        return delete_list_of_neighbor_lists

    def insertAll(self):
        '''
        Returns all new lists obtained by inserting all not-initially present numbers, 
        one per new list at all possible locations
        '''
        insert_list_of_neighbor_lists = []
        for i in range(len(self.known_subtree_words)):
            new_list = copy.copy(self.state_list)
            #print('new_list',new_list)
            if i not in self.state_list:
                #print("i",i)
                new_lists = [new_list[j:] + [i] + new_list[:j] for j in xrange(len(new_list),-1,-1)]
                insert_list_of_neighbor_lists += new_lists

        return insert_list_of_neighbor_lists

    def getAllNeighbors(self):
        '''
        Returns all neighbors of current state
        '''
        swap_list_of_neighbor_lists = self.swapAll()
        delete_list_of_neighbor_lists = self.deleteAll()
        insert_list_of_neighbor_lists = self.insertAll()

        return swap_list_of_neighbor_lists + delete_list_of_neighbor_lists + insert_list_of_neighbor_lists
        


if __name__ == "__main__":

    rospy.init_node('state')

    manual_subtree_report = createWord('-> ( (wildlife_found) ? ( (in_comms) [go_to_comms] ) [report] )')
    manual_subtree_disarm = createWord('-> ( (mine_found) ? ( <!> ( (is_armed) ) [disarm] ) )')
    manual_subtree_pickplace = createWord('-> ( ? ( <!> ( (carrying_benign) ) [take_to_drop_off] ) (benign_found) [pick_up] )')
    manual_subtree_likelytarget = createWord('-> ( (likely_target_found) [go_to_likely_target] )')
    manual_subtree_randomwalk = createWord('-> ( [random_walk] )')
    shortcut_words = [manual_subtree_report, manual_subtree_disarm, manual_subtree_pickplace] #, manual_subtree_likelytarget, manual_subtree_randomwalk]

    initial_state_list = []

    state = State(initial_state_list, shortcut_words)
    state_BT = state.stateToBT()
    print(state_BT)
    state_word = state.stateToFulltreeWord()
    print(state_word)

    # swap: [2,1]
    # delete: [1],[2]
    # insert (give 3 total): [3,1,2],[1,3,2],[1,2,3]

    neighbors = Neighbors(state)
    list1 = neighbors.swapAll()
    #print(list1)
    list2 = neighbors.deleteAll()
    #print(list2)
    list3 = neighbors.insertAll()
    #print(list3)
    neighbors_list = neighbors.getAllNeighbors()
    #print(neighbors_list)