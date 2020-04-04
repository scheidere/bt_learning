'''
Basic MCTS implementation
Graeme Best
Oregon State University
Jan 2020
'''

from tree_node import TreeNode
from reward import reward
from cost import cost
from rollout import rollout
from action import Action, printActionSequence
import copy
import random
import math
from cfg import CFG, Word, Character

def mcts( cfg, budget, max_iterations, exploration_exploitation_parameter, max_sim_iterations ):

    ################################
    # Setup
    start_sequence = [Word([Character("S")])]
    unpicked_child_words = cfg.applyAllProductionRules(start_sequence[0]) #??? #breaks here
    root = TreeNode(parent=None, sequence=start_sequence, budget=budget, unpicked_child_words=unpicked_child_words)
    list_of_all_nodes = []
    list_of_all_nodes.append(root) # for debugging only

    ################################
    # Main loop
    for iter in range(max_iterations):

        print(iter)

        ################################
        # Selection and Expansion
        # move recursively down the tree from root
        # then add a new leaf node
        print("MCTS selection " + str(iter))
        current = root
        while True: 

            # Are there any children to be added here?
            if current.unpicked_child_words: # if not empty

                # Pick one of the children that haven't been added
                # Do this at random
                num_unpicked_child_words = len(current.unpicked_child_words)
                if num_unpicked_child_words == 1:
                    child_index = 0
                else:
                    child_index = random.randint(0,num_unpicked_child_words-1)
                child_word = current.unpicked_child_words[child_index]

                # Remove the child form the unpicked list
                del current.unpicked_child_words[child_index]

                # Setup the new word sequence
                new_sequence = copy.deepcopy(current.sequence)
                new_sequence.append(child_word)
                new_budget_left = budget - cost(new_sequence)

                # Setup the new child's unpicked children
                # Remove any over budget children from this set
                new_unpicked_child_words = cfg.applyAllProductionRules(child_word)

                # print("word:")
                # child_word.printWord()

                # print("has children:")
                # for w in new_unpicked_child_words:
                #     w.printWord()



                def is_overbudget(w):
                    seq_copy = copy.deepcopy(current.sequence)
                    seq_copy.append(w)
                    return cost(seq_copy) >= budget

                new_unpicked_child_words = [w for w in new_unpicked_child_words if not is_overbudget(w)]

                # Create the new node and add it to the tree
                # printActionSequence(new_sequence)
                new_child_node = TreeNode(parent=current, sequence=new_sequence, budget=new_budget_left, unpicked_child_words=new_unpicked_child_words)
                current.children.append(new_child_node)
                current = new_child_node
                list_of_all_nodes.append(new_child_node) # for debugging only

                break # don't go deeper in the tree...

            else:
                
                # All possible children already exist
                # Therefore recurse down the tree
                # using the UCT selection policy

                if not current.children:

                    # Reached planning horizon -- just do this again
                    break
                else:

                    # Define the UCB
                    def ucb(average, n_parent, n_child):
                        if n_child == 0:
                            return 999999999.0
                        return average + exploration_exploitation_parameter * math.sqrt( (2*math.log(n_parent)) / float(n_child) )

                    # Pick the child that maximises the UCB
                    n_parent = current.num_updates
                    best_child = -1
                    best_ucb_score = 0
                    for child_idx in range(len(current.children)):
                        child = current.children[child_idx]
                        ucb_score = ucb(child.average_evaluation_score, n_parent, child.num_updates)
                        if best_child == -1 or (ucb_score > best_ucb_score):
                            best_child = child
                            best_ucb_score = ucb_score

                    # Recurse down the tree
                    current = best_child

        ################################
        # Rollout
        print("MCTS rollout " + str(iter))
        #rollout_sequence = rollout(subsequence=current.sequence, action_set=action_set, budget=budget)
        #rollout_reward = reward(action_sequence=rollout_sequence)
        rollout_word = rollout(partial_word=current.sequence[-1], cfg=cfg, budget=budget)

        print("MCTS reward " + str(iter))
        is_valid, rollout_reward = reward(word = rollout_word, max_iterations=max_sim_iterations)

        ################################
        # Back-propagation
        # update stats of all nodes from current back to root node
        if is_valid:
            print("MCTS backprop " + str(iter))
            parent = current
            while parent: # is not None

                # Update the average
                parent.updateAverage(rollout_reward)

                # Recurse up the tree
                parent = parent.parent
        else:
            print("invalid rollout (empty?)")

    ################################
    # Extract solution
    # calculate best solution so far
    # by recursively choosing child with highest average reward
    '''
    current = root
    while current.children: # is not empty

        # Find the child with best score
        best_score = 0
        best_child = -1
        for child_idx in range(len(current.children)):
            child = current.children[child_idx]
            score = child.average_evaluation_score
            if best_child == -1 or (score > best_score):
                best_child = child
                best_score = score

        current = best_child

    solution = current.sequence
    winner = current
    '''

    # Extract best single node from search tree
    best_node = None
    for node in list_of_all_nodes:
        if not best_node:
            best_node = node
        elif best_node.average_evaluation_score < node.average_evaluation_score:
            print(best_node.average_evaluation_score)
            print(node.average_evaluation_score)
            best_node = node

    solution = best_node.sequence
    winner = best_node

    return [solution, root, list_of_all_nodes, winner]
