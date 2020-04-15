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

    return bt_list["actions"], bt_list["conditions"]

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

        #print("Finished")
        #print(bt)
        #bt.print_BT()
        return bt.root, bt
    

class ProductionRule():
    def __init__(self, input_word, output_word):
        self.input_word = input_word
        self.output_word = output_word

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
            new_word_list.append(new_word)

        return new_word_list

    def printProductionRule(self):
        input_word_string = self.input_word.toString()
        output_word_string = self.output_word.toString()
        print_string = input_word_string + " -> " + output_word_string
        print(print_string)


class CFG():
    def __init__(self):

        # Generate a grammar
        self.grammar = self.generateGrammar()
        self.printAllProdRules()

        # Print word
        #self.printWord()

        # Print all words
        #self.printAllTerminalWords(4)

    def printAllProdRules(self):
        for rule in self.grammar:
            rule.printProductionRule()
    
    def generateGrammar(self): 
        
        return self.generateGrammar_lr()

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
                # If output_word not in child_words:
                duplicate_found = False
                for word in child_words:
                    if output_word.equal(word):
                        duplicate_found = True
                if not duplicate_found:        
                    child_words.append(output_word)
            

        return child_words


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

    cfg.printAllTerminalWords(7)

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