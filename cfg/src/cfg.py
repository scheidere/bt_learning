#!/usr/bin/env python
#import bla

#import behavior_tree
from behavior_tree.behavior_tree import Sequence, Fallback, Condition, Action, BehaviorTree, Node, get_decorator
import rospy
import rospkg
import yaml

# from behavior_tree_node
import rospy
from std_msgs.msg import String, Bool
import behavior_tree.behavior_tree as bt
import behavior_tree.behavior_tree_graphviz as gv
import cv2
import zlib


def getActionsConditions():
    # Read in the list of actions and conditions from the bt_list file
    rospack = rospkg.RosPack()
    filepath = rospack.get_path('simulator') + "/config/bt_list.yaml" 
    with open(filepath, 'r') as stream:
        bt_list = yaml.safe_load(stream)

    # Extract conditions and actions
    conditions = []
    actions = []

    # Loop over all groups
    for g in bt_list['groups']:
        conditions.extend(g['conditions'])
        actions.extend(g['actions'])

    # remove duplicates
    conditions = list(set(conditions))
    actions = list(set(actions))

    return actions, conditions
    #return bt_list["actions"], bt_list["conditions"]

def getActionsConditionsGroups():

    # Read in the list of actions and conditions from the bt_list file
    rospack = rospkg.RosPack()
    filepath = rospack.get_path('simulator') + "/config/bt_list.yaml" 
    with open(filepath, 'r') as stream:
        bt_list = yaml.safe_load(stream)

    return bt_list["groups"]

class Character():
    def __init__(self, label):
        self.label = label

    def printLabel(self):
        print(self.label + " "), 

    def equal(self, char):
        return self.label == char.label

    def toString(self):
        return self.label


class Word():
    def __init__(self, input_list):
        self.list = input_list

    def isTerminal(self):
        pass

    def printWord(self):
        for char in self.list:
            char.printLabel()
        print("")

    def lenWord(self):
        return len(self.list)

    def at(self, index):
        return self.list[index]

    def equal(self, word):
        # Check if words are same length
        if len(self.list) != word.lenWord():
            return False

        # Check if all characters are the same in same length words
        else:
            for i in range(len(self.list)):
                if not self.list[i].equal(word.at(i)): #might need to do .at(i) for word?
                    return False

        return True

    def toString(self):
        str_list = []
        for char in self.list:
            str_list.append(char.toString())
        return " ".join(str_list)

    '''
    def preventSameLevelDuplicates(self):
        # This is for the prevention of duplicate actions/conditions
        control_flow_related = [Character('?'),Character('->'),Character('<!>'),Character('('),Character(')')]

        for i in range(len(self.list)-1):
            char = self.list[i]
            if char not in control_flow_related:

    '''


    def createBT(self):        
        
        nodes_worklist = []

        bt = BehaviorTree('')
        
        for i in range(len(self.list)-1):

            char = self.list[i]
            #char.printLabel()
            next_char = self.list[i+1]
            #next_char.printLabel()
        
            node = None

            # Determine the kind of node char is
            if char.equal(Character("?")):
                node = Fallback()
                #print(node)
            elif char.equal(Character("->")):
                node = Sequence()
                #print(node)
                '''
                if char.equal(Character("||")):
                    arguments = ??? # Number of children parallel node has
                    node = Parallel(int(arguments[0]))
                    self.num_child = int(arguments[0])
                '''
            elif char.label[0] == '<':
                node_label = '!'
                node = get_decorator(node_label)

            elif char.label[0] == '(' and not char.equal(Character("(")):
                node_label = char.label.replace('(', '').replace(')', '')
                node = Condition(node_label)
                #bt.node_text = node_label

            elif char.label[0] == '[':
                node_label = char.label.replace('[', '').replace(']', '')
                node = Action(node_label)
                #bt.node_text = node_label
                bt.active_ids[node_label] = 0
                '''
                elif char.equal(Character("()")):
                    node_label = "condition" # Will be the text of the specific condition node
                    node = Condition(node_label)
                    #print(node)
                    bt.node_text = node_label
                elif char.equal(Character("[]")):
                    node_label = "action" # Will be the text of the specific action node
                    node = Action(node_label)
                    #print(node)
                    bt.node_text = node_label
                    bt.active_ids[node_label] = 0
                '''
            else:
                # Catches ||, (, and maybe )
                # Which leaves node = None
                #char.printLabel()
                pass

            #print("before if not node statement")
            #print(node)
            if node:
                #print("Check if node exists")
                #node.print_node()
                #print("and after it")
                #print(node)
                bt.nodes.append(node)
            else:
                #print(node)
                pass

            # Check if it is the root node, and if so add to list
            if bt.root == None:
                bt.root = node
                nodes_worklist.append(node)
                continue

            #print(nodes_worklist)

            # Check for "(" after a node character, denoting the latter is a parent node
            if next_char.equal(Character("(")):
                # Current node (char) is a child of current parent but also a parent itself
                # Add it as a child to its parent
                parent = nodes_worklist[-1]
                parent.add_child(node)
                # Add it to the worklist so its children can be added subsequently
                nodes_worklist.append(node)
                
            elif char.equal(Character(")")):
                # Done with children of most recent parent
                nodes_worklist.pop()
                parent = nodes_worklist[-1]
                
            elif not char.equal(Character("(")):
                # Remember each child node of current parent
                parent = nodes_worklist[-1]
                parent.add_child(node)   

        # print("Finished")
        # print("len(bt.nodes)",len(bt.nodes))
        # bt.print_BT()
        return bt.root, bt


def exportBT(bt, include_nodes=None):  
    # Create a Word that represents this BT  
    # But only include nodes that include_nodes[node_idx]==True

    # Setup a stack data structure (similar to nodes_worklist)
    # Do this for both keeping track of nodes and for number of tabs
    nodes_stack = []
    level_stack = []
    nodes_stack.append(bt.root) #push
    level_stack.append(0)

    char_list = []

    prev_level = 0
    #print("initial: ", len(include_nodes))
    num_include_nodes = 0
    for i in include_nodes:
        if i:
            num_include_nodes += 1
    # print("exportBT num_include_nodes", num_include_nodes)
    # print("exportBT len(include_nodes)", len(include_nodes))

    # Do the traversal, using the stack to help
    while len(nodes_stack) != 0:

        # Pop a node off the stack
        current_node = nodes_stack.pop() #pop
        level = level_stack.pop()
        # print(current_node.__class__.__name__)

        if include_nodes == None:
            include_node = True
        else:
            #print("include_nodes: ", include_nodes)
            #print("current node: ", current_node)
            node_index = bt.nodes.index(current_node)
            #print("node_index: ", node_index)
            #print(len(include_nodes))
            include_node = include_nodes[node_index]

        if include_node:
            if level > prev_level:
                char_list.append(Character('('))
            elif level < prev_level:
                for i in xrange(prev_level-level):
                    char_list.append(Character(')'))
            
            label = bt.get_node_text(current_node)
            char_list.append(Character(label))

            # Add all children to the stack
            for child_idx in reversed(range(len(current_node.children))):
                nodes_stack.append(current_node.children[child_idx]) #push
                level_stack.append(level+1)

            prev_level = level

    while prev_level > 0:
        char_list.append(Character(')'))
        prev_level -= 1

    # Close the file
    new_word = Word(char_list)
    return new_word

class ProductionRule():
    def __init__(self, input_word, output_word):
        self.input_word = input_word
        self.output_word = output_word

    def equal(self, other_production_rule):
        return self.input_word.equal(other_production_rule.input_word) and self.output_word.equal(other_production_rule.output_word)

    def applyProductionRule(self, start_word):

        # Initialize list for found word/char within word indices
        index_pair_list = []

        # Find insert index
        word_found = False
        for i in range(start_word.lenWord() - self.input_word.lenWord() + 1):
            flag = True
            for j in range(self.input_word.lenWord()):
                if not start_word.at(i+j).equal(self.input_word.at(j)):
                    flag = False
                    break
            if flag:
                word_found = True
                start_index = i
                end_index = i + self.input_word.lenWord() - 1
                index_pair_list.append((start_index,end_index))

        '''
        if not word_found:
            return None 
        '''

        new_word_list = []

        for index_pair in index_pair_list:

            start_index = index_pair[0]
            end_index = index_pair[1]

            new_char_list = []

            # Before edit
            for i in range(start_index):
                new_char_list.append(start_word.at(i))

            # During edit
            for i in range(self.output_word.lenWord()):
                new_char_list.append(self.output_word.at(i))

            # After edit
            for i in range(end_index + 1, start_word.lenWord()):
                new_char_list.append(start_word.at(i))

            new_word = Word(new_char_list)


            #############
            # do filtering for BT duplicates
            new_word_filtered = filterDuplicates(new_word)
            duplicate_found = False

            if new_word_filtered.equal(start_word):
                duplicate_found = True

            if not duplicate_found:
                for word in new_word_list:
                    if new_word_filtered.equal(word):
                        duplicate_found = True
                        break

            if not duplicate_found:        
                new_word_list.append(new_word_filtered)

        return new_word_list

    def applyProductionRuleBackwards(self, start_word):
        '''
        almost identical to applyProductionRule()
        but apply rule backwards
        and don't bother doing the filtering
        '''

        # Initialize list for found word/char within word indices
        index_pair_list = []

        # Find insert index
        word_found = False
        for i in range(start_word.lenWord() - self.output_word.lenWord() + 1):
            flag = True
            for j in range(self.output_word.lenWord()):
                if not start_word.at(i+j).equal(self.output_word.at(j)):
                    flag = False
                    break
            if flag:
                word_found = True
                start_index = i
                end_index = i + self.output_word.lenWord() - 1
                index_pair_list.append((start_index,end_index))

        '''
        if not word_found:
            return None 
        '''

        new_word_list = []

        for index_pair in index_pair_list:

            start_index = index_pair[0]
            end_index = index_pair[1]

            new_char_list = []

            # Before edit
            for i in range(start_index):
                new_char_list.append(start_word.at(i))

            # During edit
            for i in range(self.input_word.lenWord()):
                new_char_list.append(self.input_word.at(i))

            # After edit
            for i in range(end_index + 1, start_word.lenWord()):
                new_char_list.append(start_word.at(i))

            new_word = Word(new_char_list)


            duplicate_found = False

            if new_word.equal(start_word):
                duplicate_found = True

            if not duplicate_found:
                for word in new_word_list:
                    if new_word.equal(word):
                        duplicate_found = True
                        break

            if not duplicate_found:        
                new_word_list.append(new_word)

        return new_word_list

    def printProductionRule(self):
        input_word_string = self.input_word.toString()
        output_word_string = self.output_word.toString()
        print_string = input_word_string + " -> " + output_word_string
        print(print_string)


def createWord(string_list):
    # instead of
    # word = Word([Character("A"),Character("("),Character("children"),Character(")")])
    # use
    # word = createWord(["A", "(", "children", ")"])
    # OR (even better):
    # word = createWord("A ( children )")    -- Note: ' ' is used as a delimiter
    # :partyparrot: LOL

    if type(string_list) != type([]):
        # If a single string is passed in, split between spaces
        string_list = string_list.split(" ")

    # Remove any empty strings
    try:
        while True:
            string_list.remove('')
    except ValueError:
        pass

    character_list = []
    for s in string_list:
        character_list.append(Character(s))
    return Word(character_list)


# Precompute these rather than recreating them many times in the below function
char_open_bracket = Character("(")
char_close_bracket = Character(")")
char_sequence = Character("->")
char_fallback = Character("?")

'''
def filterDuplicates(in_word):
    # This filter is specific to the BT CFGs (not really CFGs in general)
    # Filter out the right most occurence of any duplicate actions/conditions that are:
    # - within the same subtree
    # - and at the same level
    # i.e., are siblings
    # Also don't allow duplicates for ""sequence"+s" nodes

    maxlevels = 10 # max height of the BT
    words_at_levels = []
    for l in xrange(maxlevels):
        words_at_levels.append([])

    level = 0

    keep_indices = [] # keep these Characters
    deletion_found = False

    for char_idx in xrange(len(in_word.list)):

        char = in_word.list[char_idx]
        # char.printLabel()
        # print

        keep = True

        # Determine the kind of node char is
        if char.equal(char_open_bracket):
            level += 1
        elif char.equal(char_close_bracket):
            # Clear the siblings at this level
            words_at_levels[level] = []
            level -= 1
        elif len(char.label) > 8 and char.label[0:8] == 'sequence':
            # "sequence"+s nodes
            # Note this does not include "sequence" (without the s) nodes
            if char.label in words_at_levels[level]:
                keep = False
            else:
                words_at_levels[level].append(char.label)

        elif char.label[0] == '(' and not char.equal(char_open_bracket):
            # Condition
            if char.label in words_at_levels[level]:
                keep = False
            else:
                words_at_levels[level].append(char.label)

        elif char.label[0] == '[':
            # Action
            if char.label in words_at_levels[level]:
                keep = False
            else:
                words_at_levels[level].append(char.label)

        # print(words_at_levels)

        if keep:
            keep_indices.append(char_idx)
        else:
            deletion_found = True
            # print('duplicate!')

    if deletion_found:
        new_word_list = []
        for i in keep_indices:
            new_word_list.append(in_word.list[i])
        new_word = Word(new_word_list)
        # print('filterDuplicates duplicate found!')
        # print('filterDuplicates in', in_word.toString())
        # print('filterDuplicates out', new_word.toString())
        return new_word
    else:
        # print('filterDuplicates keep input word')
        # print('filterDuplicates in', in_word.toString())
        # print(words_at_levels)
        return in_word
'''

def filterDuplicates(in_word):
    # This filter is specific to the BT CFGs (not really CFGs in general)
    # Filter out the right most occurence of any duplicate actions/conditions that are:
    # - within the same subtree
    # - and at the same level
    # i.e., are siblings
    # Also don't allow duplicates for ""sequence"+s" nodes

    maxlevels = 10 # max height of the BT
    words_at_levels = []
    for l in xrange(maxlevels):
        words_at_levels.append([])

    level = 0

    keep_indices = [] # keep these Characters
    deletion_found = False

    for char_idx in xrange(len(in_word.list)):

        char = in_word.list[char_idx]
        # char.printLabel()
        # print

        keep = True

        # Determine the kind of node char is
        if char.equal(char_open_bracket):
            level += 1
        elif char.equal(char_close_bracket):
            level -= 1
            # Clear lists above level 1
            if level <= 1:
                for l in xrange(level+1,maxlevels):
                    words_at_levels[l] = []
        elif len(char.label) > 8 and char.label[0:8] == 'sequence':
            # "sequence"+s nodes
            # Note this does not include "sequence" (without the s) nodes
            if char.label in words_at_levels[level]:
                keep = False
            else:
                words_at_levels[level].append(char.label)

        elif char.label[0] == '(' and not char.equal(char_open_bracket):
            # Condition
            if char.label in words_at_levels[2]:
                keep = False
            else:
                words_at_levels[2].append(char.label)

        elif char.label[0] == '[':
            # Action
            if char.label in words_at_levels[2]:
                keep = False
            else:
                words_at_levels[2].append(char.label)

        # print(words_at_levels)

        if keep:
            keep_indices.append(char_idx)
        else:
            deletion_found = True
            # print('duplicate!')

    if deletion_found:
        new_word_list = []
        for i in keep_indices:
            new_word_list.append(in_word.list[i])

        new_word = Word(new_word_list)

        # For this version of this method, we also need to then remove all empty subtrees
        subtree_removed,new_word = removeEmptySubtrees(new_word)

        # print('filterDuplicates duplicate found!')
        # print('filterDuplicates in', in_word.toString())
        # print('filterDuplicates out', new_word.toString())
        return new_word
    else:
        # print('filterDuplicates keep input word')
        # print('filterDuplicates in', in_word.toString())
        # print(words_at_levels)
        return in_word

def removeEmptySubtrees(in_word):

    maxlevels = 10 # max height of the BT
    level_start_index = [0]*maxlevels
    level_subtree_count = [0]*maxlevels

    level = 0

    deletion_ranges = [] # keep these Characters
    deletion_found = False

    for char_idx in xrange(len(in_word.list)):

        char = in_word.list[char_idx]
        # char.printLabel()
        # print

        keep = True

        # Determine the kind of node char is
        if char.equal(char_open_bracket):
            level += 1
            level_start_index[level] = char_idx-1
        elif char.equal(char_close_bracket):
            if level_subtree_count[level] == 0:
                deletion_ranges.append([level_start_index[level], char_idx])
                deletion_found = True
                # print('remove level', level, [level_start_index[level], char_idx])
            level_subtree_count[level] = 0
            level -= 1            

        # If not a control node
        # Increment all level counts up to this level
        if not char.equal(char_open_bracket) and not char.equal(char_close_bracket) and not char.equal(char_sequence) and not char.equal(char_fallback) and not char.label[0] == '<':
            for l in xrange(level+1):
                level_subtree_count[l] += 1

    if deletion_found:
        new_word_list = []
        for char_idx in xrange(len(in_word.list)):
            in_deletion_range = False
            for deletion_range in deletion_ranges:
                if char_idx >= deletion_range[0] and char_idx <= deletion_range[1]:
                    in_deletion_range = True
                    break
            if not in_deletion_range:
                new_word_list.append(in_word.list[char_idx])

        new_word = Word(new_word_list)
        # in_word.printWord()
        # new_word.printWord()
        return True, new_word
    else:
        return False, in_word

def extract_subtrees(word):
    # extracts the words for the sequence subtrees

    subtree_words = []

    level = 0

    for char_idx in xrange(len(word.list)):

        char = word.list[char_idx]

        # Determine the kind of node char is
        if char.equal(char_open_bracket):
            level += 1
            if level == 2:
                start_subtree = char_idx-1
        elif char.equal(char_close_bracket):
            level -= 1 
            if level == 1:
                end_subtree = char_idx+1
                subtree_word_list = word.list[start_subtree:end_subtree]
                subtree_words.append(Word(subtree_word_list))
    return subtree_words

class GeneticRule():
    def __init__(self):
        pass

    # Copied from ProductionRule()
    def equal(self, other_production_rule):
        return self.input_word.equal(other_production_rule.input_word) and self.output_word.equal(other_production_rule.output_word)
    
    def findSubtree(self, start_word, input_word):
        word_found = False
        #print("in findSubtree")
        #print(start_word, start_word.lenWord())
        #print(input_word, input_word.lenWord())
        for i in range(start_word.lenWord() - input_word.lenWord() + 1):
            flag = True
            for j in range(input_word.lenWord()):
                if not start_word.at(i+j).equal(input_word.at(j)):
                    flag = False
                    break
            if flag:
                word_found = True
                start_index = i
                end_index = i + input_word.lenWord() - 1
                return start_index, end_index

        return None

    # Copied from ProductionRule()
    def applyProductionRule(self, start_word): #changed name from applyGeneticRule (made rollout.py easier)

        # return error if ever called from here
        raise ValueError("Cannot apply rule with parent class")


class CrossoverRule(GeneticRule):

    def applyProductionRule(self, start_word): #changed name from applyGeneticRule

        new_word_list = []

        # Extract sub-trees as words from current BT word
        subtree_words_list = extract_subtrees(start_word)
        #print(len(subtree_words_list),'len')

        if start_word.list[-1].equal(Character("*")) and len(subtree_words_list) > 1:

            # Check that crossover has not been applied yet (i.e. star still at end)
            #if start_word.list[-1].equal(Character("*")):
            #start_word.printWord()

            # Remove subtrees from starting BT, start_word
            first_start_index, first_end_index = self.findSubtree(start_word, subtree_words_list[0])
            last_start_index, last_end_index = self.findSubtree(start_word, subtree_words_list[-1])
            pre_subtree_char_list = start_word.list[:first_start_index]
            post_subtree_char_list = start_word.list[last_end_index+1:-1] # End of tree minus star
            ##print("pre,post",pre_subtree_char_list,post_subtree_char_list)

            ##print("start_word:")
            ##start_word.printWord()
            ##print("new words:")
            ## Iterate through all pairs of two subtrees
            for i in range(len(subtree_words_list)-1):
                #print("i",i)
                test_i = i
                for j in range(i+1,len(subtree_words_list)):

                    # Reset subtree order
                    subtree_order = [k for k in range(len(subtree_words_list))]
                    #print(subtree_order)
                    #print(i,j)
                    # Update subtree order via swapping of given pair
                    subtree_order[test_i], subtree_order[j] = subtree_order[j], subtree_order[test_i]
                    #print(subtree_order)
                     
                    # Add subtrees in new order to create child tree from crossover
                    new_char_list = []

                    # Add original root structure
                    for char in pre_subtree_char_list:
                        new_char_list.append(char)

                    # Add ordered subtrees 
                    for i in subtree_order:
                        for char in subtree_words_list[i].list:
                            new_char_list.append(char)

                    # Add original conclusive characters, relating to root
                    for char in post_subtree_char_list:
                        new_char_list.append(char)

                    #for char in new_char_list:
                        #print(char.label)
                    new_word = Word(new_char_list)
                    ###new_word.printWord()

                    # Add new word to the population
                    new_word_list.append(new_word)

        if start_word.list[-1].equal(Character("*")):
            new_char_list = []
            # Add non-crossed-over word without star
            for char in start_word.list[:-1]:
                new_char_list.append(char)
            new_word_list.append(Word(new_char_list))

        #for word in new_word_list:
        #    word.printWord()

        return new_word_list


       

class CFG():
    def __init__(self):

        # Generate a grammar
        self.grammar = self.generateGrammar()
        self.printAllProdRules()

        self.genetic_grammar = self.generateGeneticGrammar()

        # Print word
        #self.printWord()

        # Print all words
        #self.printAllTerminalWords(4)

    def addProductionRule(self, new_production_rule):

        # Check it doesn't already exist
        for pr in self.grammar:
            if pr.equal(new_production_rule):
                return False

        # Add it
        self.grammar.append(new_production_rule)
        print("Production rule added!")
        new_production_rule.printProductionRule()
        return True

    def printAllProdRules(self):
        for rule in self.grammar:
            rule.printProductionRule()
    
    def generateGrammar(self): 
        
        return self.generateGrammarGuidedStructureGroups()

    def generateGeneticGrammar(self):

        rules = []

        rules.append(CrossoverRule())

        return rules

    def generateGrammar_treeTest(self):

        # Create empty production rule list
        production_rule_list = []

        # Word = entire tree

        input_word = Word([Character("S")])
        output_word = Word([Character("tree")])
        production_rule = ProductionRule(input_word, output_word)
        production_rule_list.append(production_rule)

        input_word = Word([Character("tree")])
        output_word = Word([Character("A"),Character("("),Character("children"),Character(")")])
        production_rule = ProductionRule(input_word, output_word)
        production_rule_list.append(production_rule)

        return production_rule_list

    def generateGrammar_parenthesisTest(self):

        # Create empty production rule list
        production_rule_list = []
        
        input_word = Word([Character("S")])
        output_word = Word([Character("("), Character("S"), Character(")")])
        production_rule = ProductionRule(input_word, output_word)
        production_rule_list.append(production_rule)


        input_word = Word([Character("S")])
        output_word = Word([Character("S"), Character("S")])
        production_rule = ProductionRule(input_word, output_word)
        production_rule_list.append(production_rule)


        input_word = Word([Character("S")])
        output_word = Word([Character("("), Character(")")])
        production_rule = ProductionRule(input_word, output_word)
        production_rule_list.append(production_rule)

        return production_rule_list
        

    def generateGrammar_readingGroupPaper(self):
        # Define input and output words to define a production rule, and add the list

        # Create empty production rule list
        production_rule_list = []
        
        input_word = Word([Character("S")])
        output_word = Word([Character("a"), Character("b"), Character("c")])
        production_rule = ProductionRule(input_word, output_word)
        production_rule_list.append(production_rule)
       
        input_word = Word([Character("A")])
        output_word = Word([Character("a")])
        production_rule = ProductionRule(input_word, output_word)
        production_rule_list.append(production_rule)
        

        input_word = Word([Character("a"), Character("B")])
        output_word = Word([Character("a"), Character("c")])
        production_rule = ProductionRule(input_word, output_word)
        production_rule_list.append(production_rule)

        
        input_word = Word([Character("B")])
        output_word = Word([Character("b")])
        production_rule = ProductionRule(input_word, output_word)
        production_rule_list.append(production_rule)


        input_word = Word([Character("S")])
        output_word = Word([Character("A"), Character("B")])
        production_rule = ProductionRule(input_word, output_word)
        production_rule_list.append(production_rule)


        input_word = Word([Character("A"), Character("B")])
        output_word = Word([Character("b"), Character("c")])
        production_rule = ProductionRule(input_word, output_word)
        production_rule_list.append(production_rule)
        
        return production_rule_list

    def generateGrammar_nolr(self):

        # Create empty production rule list
        production_rule_list = []
        list_actions,list_conditions = getActionsConditions()  
        
        # Behavior Tree Production Rules
        input_word = Word([Character("S")])
        output_word = Word([Character("tree")])
        production_rule = ProductionRule(input_word, output_word)
        production_rule_list.append(production_rule)

        input_word = Word([Character("tree")])
        output_word = Word([Character("?"),Character("("),Character("A"),Character("children"),Character(")")])
        production_rule = ProductionRule(input_word, output_word)
        production_rule_list.append(production_rule)

        input_word = Word([Character("tree")])
        output_word = Word([Character("->"),Character("("),Character("A"),Character("children"),Character(")")])
        production_rule = ProductionRule(input_word, output_word)
        production_rule_list.append(production_rule)

        input_word = Word([Character("children")])
        output_word = Word([Character("A"),Character("children")])
        production_rule = ProductionRule(input_word, output_word)
        production_rule_list.append(production_rule)

        input_word = Word([Character("children")])
        output_word = Word([Character("A")])
        production_rule = ProductionRule(input_word, output_word)
        production_rule_list.append(production_rule)

        for action in list_actions:
            action_string = '[' + action + ']'
            input_word = Word([Character("A")])
            output_word = Word([Character(action_string)]) #'[]'
            production_rule = ProductionRule(input_word, output_word)
            production_rule_list.append(production_rule)

        for condition in list_conditions:
            condition_string = '(' + condition + ')'
            input_word = Word([Character("A")])
            output_word = Word([Character(condition_string)]) #'()'
            production_rule = ProductionRule(input_word, output_word)
            production_rule_list.append(production_rule)

        input_word = Word([Character("A")])
        output_word = Word([Character("tree")])
        production_rule = ProductionRule(input_word, output_word)
        production_rule_list.append(production_rule)
        
        return production_rule_list

    def generateGrammar_lr(self):    
        # Behavior Tree Production Rules
        
        # Needed this rule before we changed the following four to tree = S (anywhere there is an S, it was tree)

        # Create empty production rule list
        production_rule_list = []
        list_actions,list_conditions = getActionsConditions()  

        input_word = Word([Character("S")])
        output_word = Word([Character("SorSprime")])
        production_rule = ProductionRule(input_word, output_word)
        production_rule_list.append(production_rule)

        input_word = Word([Character("Sprime")]) #was tree but we replaced tree with Sprime everywhere else
        output_word = Word([Character("SorSprime")])
        production_rule = ProductionRule(input_word, output_word)
        production_rule_list.append(production_rule)

        input_word = Word([Character("SorSprime")])
        output_word = Word([Character("?"),Character("("),Character("A"),Character("children_r"),Character(")")])
        production_rule = ProductionRule(input_word, output_word)
        production_rule_list.append(production_rule)

        input_word = Word([Character("SorSprime")])
        output_word = Word([Character("->"),Character("("),Character("A"),Character("children_r"),Character(")")])
        production_rule = ProductionRule(input_word, output_word)
        production_rule_list.append(production_rule)
        
        input_word = Word([Character("SorSprime")])
        output_word = Word([Character("?"),Character("("),Character("children_l"),Character("A"),Character(")")])
        production_rule = ProductionRule(input_word, output_word)
        production_rule_list.append(production_rule)

        input_word = Word([Character("SorSprime")])
        output_word = Word([Character("->"),Character("("),Character("children_l"),Character("A"),Character(")")])
        production_rule = ProductionRule(input_word, output_word)
        production_rule_list.append(production_rule)

        # Potential new rule to allow fallback nodes to only have conditions as children (no actions)
        input_word = Word([Character("Sprime")])
        output_word = Word([Character("?"),Character("("),Character("children_l"),Character("CorD"),Character(")")])
        production_rule = ProductionRule(input_word, output_word)
        production_rule_list.append(production_rule)

        input_word = Word([Character("Sprime")])
        output_word = Word([Character("->"),Character("("),Character("children_l"),Character("CorD"),Character(")")])
        production_rule = ProductionRule(input_word, output_word)
        production_rule_list.append(production_rule)

        input_word = Word([Character("CorD")])
        output_word = Word([Character("<!>"),Character("("),Character("C"),Character(")")])
        production_rule = ProductionRule(input_word, output_word)
        production_rule_list.append(production_rule)

        input_word = Word([Character("CorD")])
        output_word = Word([Character("C")])
        production_rule = ProductionRule(input_word, output_word)
        production_rule_list.append(production_rule)

        '''
        # This allows actions to be alone under parent node
        input_word = Word([Character("tree")])
        output_word = Word([Character("?"),Character("("),Character("A"),Character(")")])
        production_rule = ProductionRule(input_word, output_word)
        production_rule_list.append(production_rule)

        input_word = Word([Character("tree")])
        output_word = Word([Character("->"),Character("("),Character("A"),Character(")")])
        production_rule = ProductionRule(input_word, output_word)
        production_rule_list.append(production_rule)
        '''

        # Note: there are more ways than just the following two, but I chose this method for simplicity
        # ex. you could add children_r to the right of A under a children_l input word... Too complicated
        input_word = Word([Character("children_l")])
        output_word = Word([Character("children_l"),Character("CorD")])
        production_rule = ProductionRule(input_word, output_word)
        production_rule_list.append(production_rule)

        input_word = Word([Character("children_r")])
        output_word = Word([Character("A"),Character("children_r")])
        production_rule = ProductionRule(input_word, output_word)
        production_rule_list.append(production_rule)

        # Prevent tree by itself (Don't want 1-wide tree)
        input_word = Word([Character("children_l")])
        output_word = Word([Character("children_l"),Character("Sprime")])
        production_rule = ProductionRule(input_word, output_word)
        production_rule_list.append(production_rule)

        input_word = Word([Character("children_r")])
        output_word = Word([Character("S"),Character("children_r")])
        production_rule = ProductionRule(input_word, output_word)
        production_rule_list.append(production_rule)

        # A A A
        input_word = Word([Character("children_r")])
        output_word = Word([Character("A")])
        production_rule = ProductionRule(input_word, output_word)
        production_rule_list.append(production_rule)

        # C C A
        input_word = Word([Character("children_l")])
        output_word = Word([Character("CorD")])
        production_rule = ProductionRule(input_word, output_word)
        production_rule_list.append(production_rule)
        
        input_word = Word([Character("children_r")])
        output_word = Word([Character("S")])
        production_rule = ProductionRule(input_word, output_word)
        production_rule_list.append(production_rule)

        input_word = Word([Character("children_l")])
        output_word = Word([Character("Sprime")])
        production_rule = ProductionRule(input_word, output_word)
        production_rule_list.append(production_rule)


        for action in list_actions:
            action_string = '[' + action + ']'
            input_word = Word([Character("A")])
            output_word = Word([Character(action_string)]) #'[]'
            production_rule = ProductionRule(input_word, output_word)
            production_rule_list.append(production_rule)

        for condition in list_conditions:
            condition_string = '(' + condition + ')'
            input_word = Word([Character("C")])
            output_word = Word([Character(condition_string)]) #'()'
            production_rule = ProductionRule(input_word, output_word)
            production_rule_list.append(production_rule)

        '''
        # These we dont want because they allow 1-wide search tree
        input_word = Word([Character("A")])
        output_word = Word([Character("tree")])
        production_rule = ProductionRule(input_word, output_word)
        production_rule_list.append(production_rule)

        input_word = Word([Character("C")])
        output_word = Word([Character("tree")])
        production_rule = ProductionRule(input_word, output_word)
        production_rule_list.append(production_rule)
        '''
        
        # Might need to generalize to using N for a general node instead of using A for general and specifically action
        # Note for Graeme: I looked at the output but I am not confident these will work the way we need them to
        
        return production_rule_list

    def generateGrammar_testing(self):

        # Create empty production rule list
        production_rule_list = []
        list_actions,list_conditions = getActionsConditions()  
        
        # Behavior Tree Production Rules
        input_word = Word([Character("S")])
        output_word = Word([Character("tree")])
        production_rule = ProductionRule(input_word, output_word)
        production_rule_list.append(production_rule)

        input_word = Word([Character("tree")])
        output_word = Word([Character("?"),Character("("),Character("A"),Character("children_r"),Character(")")])
        production_rule = ProductionRule(input_word, output_word)
        production_rule_list.append(production_rule)

        input_word = Word([Character("tree")])
        output_word = Word([Character("->"),Character("("),Character("A"),Character("children_r"),Character(")")])
        production_rule = ProductionRule(input_word, output_word)
        production_rule_list.append(production_rule)

        input_word = Word([Character("tree")])
        output_word = Word([Character("?"),Character("("),Character("children_l"),Character("A"),Character(")")])
        production_rule = ProductionRule(input_word, output_word)
        production_rule_list.append(production_rule)

        input_word = Word([Character("tree")])
        output_word = Word([Character("->"),Character("("),Character("children_l"),Character("A"),Character(")")])
        production_rule = ProductionRule(input_word, output_word)
        production_rule_list.append(production_rule)

        input_word = Word([Character("children_r")])
        output_word = Word([Character("A"),Character("children_r")])
        production_rule = ProductionRule(input_word, output_word)
        production_rule_list.append(production_rule)
        '''
        input_word = Word([Character("children_r")])
        output_word = Word([Character("tree"),Character("children_r")])
        production_rule = ProductionRule(input_word, output_word)
        production_rule_list.append(production_rule)
        '''
        input_word = Word([Character("children_r")])
        output_word = Word([Character("A")])
        production_rule = ProductionRule(input_word, output_word)
        production_rule_list.append(production_rule)

        input_word = Word([Character("children_l")])
        output_word = Word([Character("children_l"), Character("C")])
        production_rule = ProductionRule(input_word, output_word)
        production_rule_list.append(production_rule)
        
        input_word = Word([Character("children_l")])
        output_word = Word([Character("children_l"), Character("tree")])
        production_rule = ProductionRule(input_word, output_word)
        production_rule_list.append(production_rule)
        
        input_word = Word([Character("children_l")])
        output_word = Word([Character("C")])
        production_rule = ProductionRule(input_word, output_word)
        production_rule_list.append(production_rule)

        for action in list_actions:
            action_string = '[' + action + ']'
            input_word = Word([Character("A")])
            output_word = Word([Character(action_string)]) #'[]'
            production_rule = ProductionRule(input_word, output_word)
            production_rule_list.append(production_rule)

        for condition in list_conditions:
            condition_string = '(' + condition + ')'
            input_word = Word([Character("C")])
            output_word = Word([Character(condition_string)]) #'()'
            production_rule = ProductionRule(input_word, output_word)
            production_rule_list.append(production_rule)

        '''
        input_word = Word([Character("A")])
        output_word = Word([Character("tree")])
        production_rule = ProductionRule(input_word, output_word)
        production_rule_list.append(production_rule)

        input_word = Word([Character("C")])
        output_word = Word([Character("tree")])
        production_rule = ProductionRule(input_word, output_word)
        production_rule_list.append(production_rule)
        '''

        #test children l or r -> tree
        input_word = Word([Character("children_r")])
        output_word = Word([Character("tree")])
        production_rule = ProductionRule(input_word, output_word)
        production_rule_list.append(production_rule)

        input_word = Word([Character("children_l")])
        output_word = Word([Character("tree")])
        production_rule = ProductionRule(input_word, output_word)
        production_rule_list.append(production_rule)
        
        return production_rule_list

    def generateGrammarGuidedStructure(self):

        '''
        This CFG results in the following guided (or forced) structure
        ?
        -> -> -> ...
        ? A C
        A C
        '''

        # Create empty production rule list
        production_rule_list = []
        list_actions,list_conditions = getActionsConditions()

        input_word = createWord("S")
        output_word = createWord("? ( sequence add_sequence )")
        production_rule = ProductionRule(input_word, output_word)
        production_rule_list.append(production_rule)

        input_word = createWord("add_sequence")
        output_word = createWord("sequence add_sequence")
        production_rule = ProductionRule(input_word, output_word)
        production_rule_list.append(production_rule)

        input_word = createWord("add_sequence")
        output_word = createWord("sequence")
        production_rule = ProductionRule(input_word, output_word)
        production_rule_list.append(production_rule)

        input_word = createWord("sequence")
        output_word = createWord("-> ( A children_r )")
        production_rule = ProductionRule(input_word, output_word)
        production_rule_list.append(production_rule)

        input_word = createWord("sequence")
        output_word = createWord("-> ( children_l A )")
        production_rule = ProductionRule(input_word, output_word)
        production_rule_list.append(production_rule)

        input_word = createWord("sequence")
        output_word = createWord("-> ( fallback children_r )")
        production_rule = ProductionRule(input_word, output_word)
        production_rule_list.append(production_rule)

        input_word = createWord("sequence")
        output_word = createWord("-> ( children_l fallback )")
        production_rule = ProductionRule(input_word, output_word)
        production_rule_list.append(production_rule)

        input_word = createWord("fallback")
        output_word = createWord("? ( A level3_r )")
        production_rule = ProductionRule(input_word, output_word)
        production_rule_list.append(production_rule)

        input_word = createWord("fallback")
        output_word = createWord("? ( level3_l A )")
        production_rule = ProductionRule(input_word, output_word)
        production_rule_list.append(production_rule)

        input_word = createWord("children_r")
        output_word = createWord("A children_r")
        production_rule = ProductionRule(input_word, output_word)
        production_rule_list.append(production_rule)

        input_word = createWord("children_r")
        output_word = createWord("fallback children_r")
        production_rule = ProductionRule(input_word, output_word)
        production_rule_list.append(production_rule)

        input_word = createWord("children_r")
        output_word = createWord("A")
        production_rule = ProductionRule(input_word, output_word)
        production_rule_list.append(production_rule)

        input_word = createWord("children_r")
        output_word = createWord("fallback")
        production_rule = ProductionRule(input_word, output_word)
        production_rule_list.append(production_rule)

        input_word = createWord("children_l")
        output_word = createWord("children_l CorD")
        production_rule = ProductionRule(input_word, output_word)
        production_rule_list.append(production_rule)

        input_word = createWord("children_l")
        output_word = createWord("children_l fallback")
        production_rule = ProductionRule(input_word, output_word)
        production_rule_list.append(production_rule)

        input_word = createWord("children_l")
        output_word = createWord("CorD")
        production_rule = ProductionRule(input_word, output_word)
        production_rule_list.append(production_rule)

        input_word = createWord("children_l")
        output_word = createWord("fallback")
        production_rule = ProductionRule(input_word, output_word)
        production_rule_list.append(production_rule)

        input_word = createWord("level3_r")
        output_word = createWord("A level3_r")
        production_rule = ProductionRule(input_word, output_word)
        production_rule_list.append(production_rule)

        input_word = createWord("level3_r")
        output_word = createWord("A")
        production_rule = ProductionRule(input_word, output_word)
        production_rule_list.append(production_rule)

        input_word = createWord("level3_l")
        output_word = createWord("level3_l CorD")
        production_rule = ProductionRule(input_word, output_word)
        production_rule_list.append(production_rule)

        input_word = createWord("level3_l")
        output_word = createWord("CorD")
        production_rule = ProductionRule(input_word, output_word)
        production_rule_list.append(production_rule)

        input_word = createWord("CorD")
        output_word = createWord("C")
        production_rule = ProductionRule(input_word, output_word)
        production_rule_list.append(production_rule)

        input_word = createWord("CorD")
        output_word = createWord("<!> ( C )")
        production_rule = ProductionRule(input_word, output_word)
        production_rule_list.append(production_rule)

        for action in list_actions:
            action_string = '[' + action + ']'
            input_word = Word([Character("A")])
            output_word = Word([Character(action_string)]) #'[]'
            production_rule = ProductionRule(input_word, output_word)
            production_rule_list.append(production_rule)

        for condition in list_conditions:
            condition_string = '(' + condition + ')'
            input_word = Word([Character("C")])
            output_word = Word([Character(condition_string)]) #'()'
            production_rule = ProductionRule(input_word, output_word)
            production_rule_list.append(production_rule)

        return production_rule_list

    def generateGrammarGuidedStructureGroups(self):

        '''
        Same as generateGrammarGuidedStructure, but with groups
        Only actions and conditions in the same group are allowed within the same sequence subtree

        This CFG results in the following guided (or forced) structure
        ?
        -> -> -> ...
        ? A C
        A C
        '''

        # Create empty production rule list
        production_rule_list = []
        # list_actions,list_conditions = getActionsConditions()
        groups = getActionsConditionsGroups()
        num_groups = len(groups)

        '''
        input_word = createWord("S")
        output_word = createWord("? ( add_sequence sequence add_sequence )")
        production_rule = ProductionRule(input_word, output_word)
        production_rule_list.append(production_rule)

        input_word = createWord("add_sequence")
        output_word = createWord("add_sequence sequence add_sequence")
        production_rule = ProductionRule(input_word, output_word)
        production_rule_list.append(production_rule)

        input_word = createWord("add_sequence")
        output_word = createWord("sequence")
        production_rule = ProductionRule(input_word, output_word)
        production_rule_list.append(production_rule)

        input_word = createWord("add_sequence")
        output_word = Word([])
        production_rule = ProductionRule(input_word, output_word)
        production_rule_list.append(production_rule)
        '''
        '''
        input_word = createWord("S")
        output_word = createWord("? ( sequence add_sequence )")
        production_rule = ProductionRule(input_word, output_word)
        production_rule_list.append(production_rule)
        '''

        # Star denotes crossover has not yet been applied
        input_word = createWord("S")
        output_word = createWord("? ( sequence add_sequence ) *")
        production_rule = ProductionRule(input_word, output_word)
        production_rule_list.append(production_rule)

        input_word = createWord("add_sequence")
        output_word = createWord("sequence add_sequence")
        production_rule = ProductionRule(input_word, output_word)
        production_rule_list.append(production_rule)

        input_word = createWord("add_sequence")
        output_word = createWord("sequence")
        production_rule = ProductionRule(input_word, output_word)
        production_rule_list.append(production_rule)

        for g_idx in xrange(num_groups):

            g = groups[g_idx]
            s = str(g_idx)

            # Convert generic sequence to a sequence of a particular group
            input_word = createWord("sequence")
            output_word = createWord("sequence"+s)
            production_rule = ProductionRule(input_word, output_word)
            production_rule_list.append(production_rule)

            input_word = createWord("sequence"+s)
            output_word = createWord(["->", "(", "A"+s, "children_r"+s, ")"])
            production_rule = ProductionRule(input_word, output_word)
            production_rule_list.append(production_rule)

            input_word = createWord("sequence"+s)
            output_word = createWord(["->","(","children_l"+s,"A"+s, ")"])
            production_rule = ProductionRule(input_word, output_word)
            production_rule_list.append(production_rule)

            input_word = createWord("sequence"+s)
            output_word = createWord(["->","(","fallback"+s,"children_r"+s, ")"])
            production_rule = ProductionRule(input_word, output_word)
            production_rule_list.append(production_rule)

            input_word = createWord("sequence"+s)
            output_word = createWord(["->","(","children_l"+s,"fallback"+s, ")"])
            production_rule = ProductionRule(input_word, output_word)
            production_rule_list.append(production_rule)

            input_word = createWord("fallback"+s)
            output_word = createWord(["?","(","A"+s,"level3_r"+s, ")"])
            production_rule = ProductionRule(input_word, output_word)
            production_rule_list.append(production_rule)

            input_word = createWord("children_r"+s)
            output_word = createWord(["A"+s, "children_r"+s])
            production_rule = ProductionRule(input_word, output_word)
            production_rule_list.append(production_rule)

            input_word = createWord("children_r"+s)
            output_word = createWord(["fallback"+s, "children_r"+s])
            production_rule = ProductionRule(input_word, output_word)
            production_rule_list.append(production_rule)

            input_word = createWord("children_r"+s)
            output_word = createWord("A"+s)
            production_rule = ProductionRule(input_word, output_word)
            production_rule_list.append(production_rule)

            input_word = createWord("children_r"+s)
            output_word = createWord("fallback"+s)
            production_rule = ProductionRule(input_word, output_word)
            production_rule_list.append(production_rule)

            input_word = createWord("children_l"+s)
            output_word = createWord(["children_l"+s,"fallback"+s])
            production_rule = ProductionRule(input_word, output_word)
            production_rule_list.append(production_rule)

            # Only do the following if there are conditions in this group
            if len(g["conditions"]) > 0:

                input_word = createWord("fallback"+s)
                output_word = createWord(["?", "(", "level3_l"+s, "A"+s, ")"])
                production_rule = ProductionRule(input_word, output_word)
                production_rule_list.append(production_rule)

                input_word = createWord("children_l"+s)
                output_word = createWord(["children_l"+s, "CorD"+s])
                production_rule = ProductionRule(input_word, output_word)
                production_rule_list.append(production_rule)

                input_word = createWord("children_l"+s)
                output_word = createWord("CorD"+s)
                production_rule = ProductionRule(input_word, output_word)
                production_rule_list.append(production_rule)

                input_word = createWord("level3_l"+s)
                output_word = createWord(["level3_l"+s,"CorD"+s])
                production_rule = ProductionRule(input_word, output_word)
                production_rule_list.append(production_rule)

                input_word = createWord("level3_l"+s)
                output_word = createWord("CorD"+s)
                production_rule = ProductionRule(input_word, output_word)
                production_rule_list.append(production_rule)

                input_word = createWord("CorD"+s)
                output_word = createWord("C"+s)
                production_rule = ProductionRule(input_word, output_word)
                production_rule_list.append(production_rule)

                input_word = createWord("CorD"+s)
                output_word = createWord(["<!>", "(", "C"+s, ")"])
                production_rule = ProductionRule(input_word, output_word)
                production_rule_list.append(production_rule)

                for condition in g["conditions"]:
                    condition_string = '(' + condition + ')'
                    input_word = Word([Character("C"+s)])
                    output_word = Word([Character(condition_string)]) #'()'
                    production_rule = ProductionRule(input_word, output_word)
                    production_rule_list.append(production_rule)

            input_word = createWord("children_l"+s)
            output_word = createWord("fallback"+s)
            production_rule = ProductionRule(input_word, output_word)
            production_rule_list.append(production_rule)

            input_word = createWord("level3_r"+s)
            output_word = createWord(["A"+s,"level3_r"+s])
            production_rule = ProductionRule(input_word, output_word)
            production_rule_list.append(production_rule)

            input_word = createWord("level3_r"+s)
            output_word = createWord("A"+s)
            production_rule = ProductionRule(input_word, output_word)
            production_rule_list.append(production_rule)

            for action in g["actions"]:
                action_string = '[' + action + ']'
                input_word = Word([Character("A"+s)])
                output_word = Word([Character(action_string)]) #'[]'
                production_rule = ProductionRule(input_word, output_word)
                production_rule_list.append(production_rule)

            

        return production_rule_list


    def generateGrammarShortcutsOnly(self):

        '''
        Same as generateGrammarGuidedStructure, but with groups
        Only actions and conditions in the same group are allowed within the same sequence subtree

        This CFG results in the following guided (or forced) structure
        ?
        -> -> -> ...
        ? A C
        A C
        '''

        # Create empty production rule list
        production_rule_list = []
        # list_actions,list_conditions = getActionsConditions()
        groups = getActionsConditionsGroups()
        num_groups = len(groups)

        '''
        input_word = createWord("S")
        output_word = createWord("? ( add_sequence sequence add_sequence )")
        production_rule = ProductionRule(input_word, output_word)
        production_rule_list.append(production_rule)

        input_word = createWord("add_sequence")
        output_word = createWord("add_sequence sequence add_sequence")
        production_rule = ProductionRule(input_word, output_word)
        production_rule_list.append(production_rule)

        input_word = createWord("add_sequence")
        output_word = createWord("sequence")
        production_rule = ProductionRule(input_word, output_word)
        production_rule_list.append(production_rule)

        input_word = createWord("add_sequence")
        output_word = Word([])
        production_rule = ProductionRule(input_word, output_word)
        production_rule_list.append(production_rule)
        '''

        
        input_word = createWord("S")
        output_word = createWord("? ( sequence sequence sequence sequence sequence sequence sequence sequence ) *")
        production_rule = ProductionRule(input_word, output_word)
        production_rule_list.append(production_rule)

        input_word = createWord("sequence")
        output_word = createWord("")
        production_rule = ProductionRule(input_word, output_word)
        production_rule_list.append(production_rule)
        

        return production_rule_list


    def generateGrammarGuidedStructureGroupsOneSequence(self):

        '''
        Same as generateGrammarGuidedStructure, but with groups
        Only actions and conditions in the same group are allowed within the same sequence subtree

        This CFG results in the following guided (or forced) structure
        ?
        -> -> -> ...
        ? A C
        A C
        '''

        # Create empty production rule list
        production_rule_list = []
        # list_actions,list_conditions = getActionsConditions()
        groups = getActionsConditionsGroups()
        num_groups = len(groups)

        '''
        input_word = createWord("S")
        output_word = createWord("? ( add_sequence sequence add_sequence )")
        production_rule = ProductionRule(input_word, output_word)
        production_rule_list.append(production_rule)

        input_word = createWord("add_sequence")
        output_word = createWord("add_sequence sequence add_sequence")
        production_rule = ProductionRule(input_word, output_word)
        production_rule_list.append(production_rule)

        input_word = createWord("add_sequence")
        output_word = createWord("sequence")
        production_rule = ProductionRule(input_word, output_word)
        production_rule_list.append(production_rule)

        input_word = createWord("add_sequence")
        output_word = Word([])
        production_rule = ProductionRule(input_word, output_word)
        production_rule_list.append(production_rule)
        '''

        input_word = createWord("S")
        output_word = createWord("? ( sequence )")
        production_rule = ProductionRule(input_word, output_word)
        production_rule_list.append(production_rule)

        for g_idx in xrange(num_groups):

            g = groups[g_idx]
            s = str(g_idx)

            # Convert generic sequence to a sequence of a particular group
            input_word = createWord("sequence")
            output_word = createWord("sequence"+s)
            production_rule = ProductionRule(input_word, output_word)
            production_rule_list.append(production_rule)

            input_word = createWord("sequence"+s)
            output_word = createWord(["->", "(", "A"+s, "children_r"+s, ")"])
            production_rule = ProductionRule(input_word, output_word)
            production_rule_list.append(production_rule)

            input_word = createWord("sequence"+s)
            output_word = createWord(["->","(","children_l"+s,"A"+s, ")"])
            production_rule = ProductionRule(input_word, output_word)
            production_rule_list.append(production_rule)

            input_word = createWord("sequence"+s)
            output_word = createWord(["->","(","fallback"+s,"children_r"+s, ")"])
            production_rule = ProductionRule(input_word, output_word)
            production_rule_list.append(production_rule)

            input_word = createWord("sequence"+s)
            output_word = createWord(["->","(","children_l"+s,"fallback"+s, ")"])
            production_rule = ProductionRule(input_word, output_word)
            production_rule_list.append(production_rule)

            input_word = createWord("fallback"+s)
            output_word = createWord(["?","(","A"+s,"level3_r"+s, ")"])
            production_rule = ProductionRule(input_word, output_word)
            production_rule_list.append(production_rule)

            input_word = createWord("children_r"+s)
            output_word = createWord(["A"+s, "children_r"+s])
            production_rule = ProductionRule(input_word, output_word)
            production_rule_list.append(production_rule)

            input_word = createWord("children_r"+s)
            output_word = createWord(["fallback"+s, "children_r"+s])
            production_rule = ProductionRule(input_word, output_word)
            production_rule_list.append(production_rule)

            input_word = createWord("children_r"+s)
            output_word = createWord("A"+s)
            production_rule = ProductionRule(input_word, output_word)
            production_rule_list.append(production_rule)

            input_word = createWord("children_r"+s)
            output_word = createWord("fallback"+s)
            production_rule = ProductionRule(input_word, output_word)
            production_rule_list.append(production_rule)

            input_word = createWord("children_l"+s)
            output_word = createWord(["children_l"+s,"fallback"+s])
            production_rule = ProductionRule(input_word, output_word)
            production_rule_list.append(production_rule)

            # Only do the following if there are conditions in this group
            if len(g["conditions"]) > 0:

                input_word = createWord("fallback"+s)
                output_word = createWord(["?", "(", "level3_l"+s, "A"+s, ")"])
                production_rule = ProductionRule(input_word, output_word)
                production_rule_list.append(production_rule)

                input_word = createWord("children_l"+s)
                output_word = createWord(["children_l"+s, "CorD"+s])
                production_rule = ProductionRule(input_word, output_word)
                production_rule_list.append(production_rule)

                input_word = createWord("children_l"+s)
                output_word = createWord("CorD"+s)
                production_rule = ProductionRule(input_word, output_word)
                production_rule_list.append(production_rule)

                input_word = createWord("level3_l"+s)
                output_word = createWord(["level3_l"+s,"CorD"+s])
                production_rule = ProductionRule(input_word, output_word)
                production_rule_list.append(production_rule)

                input_word = createWord("level3_l"+s)
                output_word = createWord("CorD"+s)
                production_rule = ProductionRule(input_word, output_word)
                production_rule_list.append(production_rule)

                input_word = createWord("CorD"+s)
                output_word = createWord("C"+s)
                production_rule = ProductionRule(input_word, output_word)
                production_rule_list.append(production_rule)

                input_word = createWord("CorD"+s)
                output_word = createWord(["<!>", "(", "C"+s, ")"])
                production_rule = ProductionRule(input_word, output_word)
                production_rule_list.append(production_rule)

                for condition in g["conditions"]:
                    condition_string = '(' + condition + ')'
                    input_word = Word([Character("C"+s)])
                    output_word = Word([Character(condition_string)]) #'()'
                    production_rule = ProductionRule(input_word, output_word)
                    production_rule_list.append(production_rule)

            input_word = createWord("children_l"+s)
            output_word = createWord("fallback"+s)
            production_rule = ProductionRule(input_word, output_word)
            production_rule_list.append(production_rule)

            input_word = createWord("level3_r"+s)
            output_word = createWord(["A"+s,"level3_r"+s])
            production_rule = ProductionRule(input_word, output_word)
            production_rule_list.append(production_rule)

            input_word = createWord("level3_r"+s)
            output_word = createWord("A"+s)
            production_rule = ProductionRule(input_word, output_word)
            production_rule_list.append(production_rule)

            for action in g["actions"]:
                action_string = '[' + action + ']'
                input_word = Word([Character("A"+s)])
                output_word = Word([Character(action_string)]) #'[]'
                production_rule = ProductionRule(input_word, output_word)
                production_rule_list.append(production_rule)

            

        return production_rule_list

    def printWord(self):

        # Need an input word
        start_word = Word([Character("S")])

        # Apply production rules
        all_rules_tried = False
        while not all_rules_tried:
            no_outputs = False
            for i in range(len(self.grammar)):
                output_word_list = self.grammar[i].applyProductionRule(start_word)

                if len(output_word_list) != 0:
                    no_outputs = True
                    start_word = output_word_list[0]
                    print("Applied rule " + str(i))

                    # print word
                    start_word.printWord()
                    break
            if not no_outputs:
                all_rules_tried = True

    def printAllWords(self):

        # Need the same input word
        start_word = Word([Character("S")])

        # Define word list
        current_list = []

        # Add first word to list
        current_list.append(start_word)

        # Apply production rules
        all_rules_tried = False
        while not all_rules_tried:
            new_list = []
            no_outputs = True
            for i in range(len(current_list)):
                for j in range(len(self.grammar)):
                    output_word_list = self.grammar[j].applyProductionRule(current_list[i])

                    for output_word in output_word_list:
                    #if output_word:
                        no_outputs = False
                        #if output_word not in new_list:
                        duplicate_found = False
                        for word in new_list:
                            if output_word.equal(word):
                                duplicate_found = True
                        if not duplicate_found:        
                            new_list.append(output_word)
                            #print("Applied rule " + str(j))

                            # print word
                            output_word.printWord()
                 
            
            current_list = new_list


            if no_outputs:
                all_rules_tried = True

    def printAllTerminalWords(self, max_depth):

        # Need the same input word
        #start_word = Word([Character("a"), Character("B"), Character("a"), Character("B")])
        start_word = Word([Character("S")])

        # Define word list
        current_list = []

        # Define terminal word list
        terminal_list = []

        # Add first word to list
        current_list.append(start_word)

        # Apply production rules
        all_rules_tried = False
        depth = 0
        while not all_rules_tried and depth < max_depth:
            new_list = []
            no_outputs = True
            for i in range(len(current_list)):
                no_output = True
                for j in range(len(self.grammar)):
                    output_word_list = self.grammar[j].applyProductionRule(current_list[i]) #output_word is now a list

                    for output_word in output_word_list:
                    #if output_word: #removed this because if output_word = None, never appended to output_word_list
                        no_outputs = False
                        no_output = False
                        #if output_word not in new_list:
                        duplicate_found = False
                        for word in new_list:
                            if output_word.equal(word):
                                duplicate_found = True
                        if not duplicate_found:        
                            new_list.append(output_word)
                            #print("Applied rule " + str(j))

                            # print word
                            output_word.printWord()

                if no_output:
                    terminal_list.append(current_list[i])
                    #current_list[i].printWord()
                 
            print("=======")
            current_list = new_list
            depth += 1

            if no_outputs:
                all_rules_tried = True

    def applyAllProductionRules(self, input_word):
        '''
        Return list of all child words of the input word
        '''

        # print("applyAllProductionRules")
        # print("input word: ")
        # input_word.printWord()

        child_words = []
        for i in range(len(self.grammar)):
            output_word_list = self.grammar[i].applyProductionRule(input_word) 

            # print("applying production rule: ")
            # self.grammar[i].printProductionRule()

            # print("generates words: ")
            # for w in output_word_list:
            #     w.printWord()

            # Check if word in output_word_list already in child_words
            for output_word in output_word_list:

                #####
                # MOVED FILTER TO WITHIN applyProductionRule instead
                #####

                # Filter out any rubbish duplicate nodes
                #output_word = filterDuplicates(output_word_before_filter)

                # If output_word not in child_words:
                duplicate_found = False

                # Make sure this production doesn't go nowhere
                # Only really relevant after adding the filter step above
                #if output_word.equal(input_word):
                #    duplicate_found = True

                if not duplicate_found:
                    for word in child_words:
                        if output_word.equal(word):
                            duplicate_found = True
                            break
                if not duplicate_found:        
                    child_words.append(output_word)

        # Now do the same for all genetic rules
        for i in range(len(self.genetic_grammar)):
            output_word_list = self.genetic_grammar[i].applyProductionRule(input_word) #changed name from applyGeneticRule

            # print("applying production rule: ")
            # self.grammar[i].printProductionRule()

            # print("generates words: ")
            # for w in output_word_list:
            #     w.printWord()

            # Check if word in output_word_list already in child_words
            for output_word in output_word_list:

                #####
                # MOVED FILTER TO WITHIN applyProductionRule instead
                #####

                # Filter out any rubbish duplicate nodes
                #output_word = filterDuplicates(output_word_before_filter)

                # If output_word not in child_words:
                duplicate_found = False

                # Make sure this production doesn't go nowhere
                # Only really relevant after adding the filter step above
                #if output_word.equal(input_word):
                #    duplicate_found = True

                if not duplicate_found:
                    for word in child_words:
                        if output_word.equal(word):
                            duplicate_found = True
                            break
                if not duplicate_found:        
                    child_words.append(output_word)            


        return child_words

    def applyAllProductionRulesBackwards(self, input_word):
        '''
        Return list of all child words of the input word
        '''

        # print("applyAllProductionRules")
        # print("input word: ")
        # input_word.printWord()

        parent_words = []
        for i in range(len(self.grammar)):
            output_word_list = self.grammar[i].applyProductionRuleBackwards(input_word) 

            # print("applying production rule: ")
            # self.grammar[i].printProductionRule()

            # print("generates words: ")
            # for w in output_word_list:
            #     w.printWord()

            # Check if word in output_word_list already in child_words
            for output_word in output_word_list:

                # If output_word not in child_words:
                duplicate_found = False

                if not duplicate_found:
                    for word in parent_words:
                        if output_word.equal(word):
                            duplicate_found = True
                            break
                if not duplicate_found:        
                    parent_words.append(output_word)
            

        return parent_words

    def derivePreviousWords(self, input_word, num_steps, ignore_words, max_ancestors):
        '''
        Apply production rules BACKWARDS
        repeat this num_steps times
        '''

        parent_words_each_step = []
        count_ancestors = 0

        for step in xrange(num_steps):

            if count_ancestors > max_ancestors:
                break

            # Get the set of child words at this step
            if step == 0:
                child_words = [input_word]
            else:
                child_words = parent_words_each_step[step-1]

            if not child_words:
                break

            parent_words_each_step.append([])

            # Apply production rules BACKWARDS to each child
            for child_word in child_words:

                if count_ancestors > max_ancestors:
                    break

                # Backward production rules
                parent_words_list = self.applyAllProductionRulesBackwards(child_word)

                # Ensure unique
                for parent_word in parent_words_list:

                    # If parent_word not in child_words:
                    duplicate_found = False

                    if parent_word.equal(input_word):
                        duplicate_found = True

                    if not duplicate_found:
                        for prev_word in ignore_words:
                            if parent_word.equal(prev_word):
                                duplicate_found = True
                                break

                    if not duplicate_found:
                        for prev_step in xrange(step-1):
                            for prev_word in parent_words_each_step[prev_step]:
                                if parent_word.equal(prev_word):
                                    duplicate_found = True
                                    break
                    if not duplicate_found:        
                        parent_words_each_step[step].append(parent_word)
                        count_ancestors += 1

            # If none, stop
            if len(parent_words_each_step[step]) == 0:
                break

        # Concatenate the lists
        parent_words_concat = []
        for step in xrange(len(parent_words_each_step)):
            parent_words_concat.extend(parent_words_each_step[step])
        return parent_words_concat


class BehaviorTreeNode:
    def __init__(self, bt_object):
        #self.tree = bt.BehaviorTree(config_filename)
        self.tree = bt_object
        for node in self.tree.nodes:
            node.init_ros()

def timer_callback(event):
    node.tree.tick()#root.tick(True)

    source = gv.get_graphviz(node.tree)
    source_msg = String()
    source_msg.data = source
    graphviz_pub.publish(source_msg)

    compressed = String()
    compressed.data = zlib.compress(source)
    compressed_pub.publish(compressed)
    '''
    img = gv.get_graphviz_image(source)
    cv2.imshow('img', img)
    cv2.waitKey(1)
    '''
'''
if __name__ == '__main__':
    rospy.init_node('behavior_tree_node')
    
    config_filename = rospy.get_param('~config', '')
    
    node = BehaviorTreeNode(config_filename)

    graphviz_pub = rospy.Publisher('behavior_tree_graphviz', String, queue_size=1)
    compressed_pub = rospy.Publisher('behavior_tree_graphviz_compressed', String, queue_size=1)
    timer = rospy.Timer(rospy.Duration(0.05), timer_callback)

    rospy.spin()
'''
             

if __name__ == "__main__":

    # Execute only if run as a script
    
    cfg = CFG()

    #cfg.printAllTerminalWords(7)

    start_word = createWord('? ( -> ( (mine_found) ? ( [disarm] ) ) -> ( [shortest_path] ) -> ( [random_walk] ) ) *')
    #test_char = Character("*")
    #print(test_char.label)

    #test_word = createWord('? ( (mine_found) ) *')
    #print(test_word.list[-1])
    #test_word.list[-1].printLabel()
    '''
    subtrees = extract_subtrees(start_word)
    for tree in subtrees:
        tree.printWord()
    
    for tree in subtrees:
        print(tree)
        for char in tree.list:
            print(char.label)
    '''
    #print(subtrees[-1].list[-1].label)
    #print('test')
    #bla = subtrees[-1].list[-1]
    #bla.printLabel()
    #print('test')
    #start_word.list[-1].printLabel()
    #if start_word.list[-1].equal(Character("*")):
    #    print("win")

    

    ##crossover = CrossoverRule()
    ##crossover.applyProductionRule(start_word)

    #rospy.init_node('behavior_tree_node')
    #list_actions,list_conditions = getActionsConditions()
    #print(list_actions,list_conditions)

    #test = Word([Character("->"),Character("("),Character("[]"),Character("?"),Character("("),Character("[]"),Character("()"),Character(")"),Character(")")])

    #bt1root,bt1 = test.createBT()

    #rospy.spin()

    #rospy.init_node('behavior_tree_node')
    
    #config_filename = rospy.get_param('~config', '')
    
    #node = BehaviorTreeNode(bt1)

    #graphviz_pub = rospy.Publisher('behavior_tree_graphviz', String, queue_size=1)
    #compressed_pub = rospy.Publisher('behavior_tree_graphviz_compressed', String, queue_size=1)
    #timer = rospy.Timer(rospy.Duration(0.05), timer_callback)

    #rospy.spin()