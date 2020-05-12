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
import matplotlib.pyplot as plt

import rospy

def mcts( cfg, budget, max_iterations, exploration_exploitation_parameter, max_sim_iterations, underwater_simulator, use_dag, config ):

    ################################
    # Setup
    start_sequence = [Word([Character("S")])]
    unpicked_child_words = cfg.applyAllProductionRules(start_sequence[0]) #??? #breaks here
    root = TreeNode(parents=[], sequence=start_sequence, budget=budget, unpicked_child_words=unpicked_child_words)
    list_of_all_nodes = []
    list_of_all_nodes.append(root) # for debugging only

    dict_of_all_nodes = dict()
    dict_of_all_nodes[root.sequence[-1].toString()] = root # for check_for_duplicates()

    avg_rollout_rewards = [] # Check with Graeme
    avg_rollout = 0 # current average
    rollout_rewards = []
    best_rewards = []
    best_reward = 0
    best_reward_word = None
    count_duplicates = 0

    plot_intermediate_results = config['plot_intermediate_results']
    plot_intermediate_results_iterations = config['plot_intermediate_results_iterations']

    if plot_intermediate_results:
        # Initialize results figure
        fig = plt.figure()
        ax = fig.add_subplot(111)
        first_plot = True

    ################################
    # Main loop
    for iter in range(max_iterations):

        if rospy.is_shutdown(): 
            # Return solution before closing
            break


        print("MCTS iteration: " + str(iter))



        ################################
        # Selection and Expansion
        # move recursively down the tree from root
        # then add a new leaf node
        # print("MCTS selection " + str(iter))
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

                # If doing DAG, check for duplicate nodes first
                if use_dag:
                    # found_duplicate, duplicate_node = check_for_duplicates(list_of_all_nodes, child_word)
                    found_duplicate, duplicate_node = check_for_duplicates(dict_of_all_nodes, child_word)
                else:
                    found_duplicate = False

                if found_duplicate:
                    # In this case, don't add a new node
                    duplicate_node.addParent(current)
                    current = duplicate_node
                    count_duplicates += 1
                    print("duplicate found! " + str(child_word.toString()))

                else:
                    # Create the new node and add it to the tree
                    # printActionSequence(new_sequence)
                    new_child_node = TreeNode(parents=[current], sequence=new_sequence, budget=new_budget_left, unpicked_child_words=new_unpicked_child_words)
                    current.children.append(new_child_node)
                    current = new_child_node
                    list_of_all_nodes.append(new_child_node) # for debugging only
                    dict_of_all_nodes[child_word.toString()] = current # for check_for_duplicates()
                    #print('new_child_node')
                    #new_child_node.sequence[-1].printWord()

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
                        #print('child average_evaluation_score',child.average_evaluation_score)
                        ucb_score = ucb(child.average_evaluation_score, n_parent, child.num_updates)
                        #print('ucb_score',ucb_score)
                        if best_child == -1 or (ucb_score > best_ucb_score):
                            best_child = child
                            best_ucb_score = ucb_score

                    #print('best_ucb_score',best_ucb_score)
                    #print('n_parent',n_parent)
                    # Recurse down the tree
                    current = best_child
                    #print('best_child')
                    #best_child.sequence[-1].printWord()

        ################################
        # Rollout
        # print("MCTS rollout " + str(iter))
        #rollout_sequence = rollout(subsequence=current.sequence, action_set=action_set, budget=budget)
        #rollout_reward = reward(action_sequence=rollout_sequence)
        rollout_word = rollout(partial_word=current.sequence[-1], cfg=cfg, budget=budget)
        #print('rollout_word')
        #rollout_word.printWord()
        # print("MCTS reward " + str(iter))
        is_valid, rollout_reward, best_rollout_reward = reward(word = rollout_word, max_iterations=max_sim_iterations, underwater_simulator=underwater_simulator)

        if best_reward_word == None or best_reward < rollout_reward:
            best_reward = rollout_reward
            best_reward_word = rollout_word

        best_rewards.append(best_reward) # whether same or different
        rollout_rewards.append(rollout_reward)

        avg_rollout = float(avg_rollout*len(avg_rollout_rewards)+rollout_reward) / float(len(avg_rollout_rewards) + 1)
        # avg_rollout_rewards.append(sum(rollout_rewards)/len(rollout_rewards))
        avg_rollout_rewards.append(avg_rollout)

        ################################
        # Print intermediate results
        
        # If iteration is multiple of 100
        # if iter != 0 and not iter%plot_intermediate_results_iterations: # Check with Graeme
        if True:
            print("Average rollout reward: " + str(avg_rollout_rewards[-1]))
            print("Best reward: " + str(best_reward))
            best_reward_word.printWord()
            print("Num duplicates: " + str(count_duplicates) + "; num nodes: " + str(len(list_of_all_nodes)))
            
        if plot_intermediate_results:   
            # If iteration is multiple of 1000
            if iter != 0 and not iter%plot_intermediate_results_iterations: #changed to 100 for testing - was 1000
                print('Plotting results')
                if first_plot:
                    first_plot = False

                    line1, = ax.plot(range(iter+1),best_rewards,label = 'best reward') #plot
                    #avg_rollout_rewards = rollout_rewards
                    line2, = ax.plot(range(iter+1),avg_rollout_rewards,label = 'average reward')
                    plt.xlabel('MCTS Iterations')
                    plt.ylabel('Score')
                    fig_text = fig.text(0.5, 0.9, best_reward_word.toString(), ha='center')
                    plt.legend(loc='best')
                    plt.show(block=False)
                    # plt.ion()
                else:
                    line1.set_xdata(range(iter+1))
                    line2.set_xdata(range(iter+1))
                    line1.set_ydata(best_rewards)
                    line2.set_ydata(avg_rollout_rewards)
                    plt.xlim(0,iter+1)
                    plt.ylim(0,best_rewards[-1]*1.1)
                    fig_text.set_text(best_reward_word.toString())

                    fig.canvas.draw()
                    fig.canvas.flush_events()

                
               
                #plt.pause(0.001)
        

        ################################
        # Back-propagation
        # update stats of all nodes from current back to root node
        if use_dag:
            # DAG case
            # backpropagate up ALL paths through the graph to the root node

            list_of_parents = []
            list_of_parents.append(current)

            list_of_already_updated = []

            while list_of_parents:
                # Get a parent from the list
                parent = list_of_parents[0]

                # Remove that parent
                # TODO more efficient way to do this?
                list_of_parents = list_of_parents[1:]

                # If not already updated
                if parent not in list_of_already_updated:
                    
                    # Update the average
                    if is_valid:
                        parent.updateAverage(rollout_reward)
                        parent.updateBestRollout(rollout_word, rollout_reward)
                    else:
                        # Invalid (empty) BT gets a reward of 0
                        parent.updateAverage(0.0)

                    # Add all parents to the list
                    # TODO more efficient way to do this?
                    list_of_parents = list_of_parents + parent.parents

                    # Remember that we've already looked at this
                    list_of_already_updated.append(parent)
        else:
            # Tree case
            if is_valid:
                # print("MCTS backprop " + str(iter))
                parent = current
                while parent: # is not None

                    # Update the average
                    #print('rollout_reward', rollout_reward)
                    #print('parent.average_evaluation_score before',parent.average_evaluation_score)
                    #print('parent.num_updates before',parent.num_updates)
                    parent.updateAverage(rollout_reward)
                    #print('parent.average_evaluation_score after',parent.average_evaluation_score)
                    #print('parent.num_updates after',parent.num_updates)
                    parent.updateBestRollout(rollout_word, rollout_reward)

                    # Recurse up the tree
                    parent = parent.parents[0]
            else:
                print("invalid rollout (empty?)")
                # print("MCTS backprop " + str(iter))
                parent = current
                rollout_reward = 0.0
                while parent: # is not None

                    # Update the average
                    parent.updateAverage(rollout_reward)
                    #parent.updateBestRollout(rollout_word, rollout_reward)

                    # Recurse up the tree
                    parent = parent.parents[0]

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
    # This allows for a solution to still be generated if the program is terminated before max_iterations reached
    best_node = None
    for node in list_of_all_nodes:
        if not best_node:
            best_node = node
        elif best_node.average_evaluation_score < node.average_evaluation_score:
            print(best_node.average_evaluation_score)
            print(node.average_evaluation_score)
            best_node = node

    solution = best_node.sequence
    best_rollout = best_node.best_rollout
    winner = best_node

    return [solution, best_rollout, root, list_of_all_nodes, winner]


'''
def check_for_duplicates(list_of_all_nodes, child_word):

    for n in list_of_all_nodes:
        current_word = n.sequence[-1]
        # check if child_word matches current_word
        if current_word.equal(child_word):
            return True, n
    return False, None
'''
def check_for_duplicates(dict_of_all_nodes, child_word):

    key = child_word.toString()
    if key in dict_of_all_nodes.keys():
        return True, dict_of_all_nodes[key]
    return False, None
