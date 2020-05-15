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
from cfg import CFG, Word, Character, extract_subtrees, ProductionRule, createWord
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

    all_iteration_rewards = [0] * max_iterations

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
    iterations_between_adding_best_edges = config['iterations_between_adding_best_edges']
    adding_best_edges_steps = config['adding_best_edges_steps']
    adding_nonzero_edges_steps = config['adding_nonzero_edges_steps']
    iterations_between_adding_production_rules = config['iterations_between_adding_production_rules']
    probability_skip_unpicked_child_words = config['probability_skip_unpicked_child_words']
    max_ancestors = config['max_ancestors']

    shortcut_words = []


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

            # Add a probability for ignoring unpicked children, to search deeper instead
            if not current.children:
                skip_unpicked_child_words = False
            else:
                skip_unpicked_child_words = random.random() < probability_skip_unpicked_child_words

            # Are there any children to be added here?
            if current.unpicked_child_words and not skip_unpicked_child_words: # if not empty

                print("current.unpicked_child_words")

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
                    print("duplicate found! " + str(child_word.toString()))
                    duplicate_node.addParent(current)

                    # Also, merge the rewards of the child into the parent
                    # Do this recursively up the tree
                    list_of_parents = []
                    list_of_parents.append(current)

                    list_of_already_updated = []

                    while list_of_parents:

                        # Get and remove a parent from the list
                        parent = list_of_parents.pop()

                        # If not already updated
                        if parent not in list_of_already_updated:
                            
                            # Update the average
                            parent.mergeRewards(all_iteration_rewards, duplicate_node)

                            # Add all parents to the list
                            list_of_parents.extend(parent.parents)

                            # Remember that we've already looked at this
                            list_of_already_updated.append(parent)
                    # current.mergeRewards(all_iteration_rewards, duplicate_node)

                    current = duplicate_node
                    count_duplicates += 1                    

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

                    if len(current.sequence) < 4:
                        print('current word', current.sequence[-1].toString())

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
                        if len(current.sequence) < 4:
                            print('child word', child.sequence[-1].toString())
                            print('child average_evaluation_score',child.average_evaluation_score)
                            print('child num_updates',child.num_updates)
                            print('ucb_score',ucb_score)
                        if best_child == -1 or (ucb_score > best_ucb_score):
                            best_child = child
                            best_ucb_score = ucb_score

                    #print('best_ucb_score',best_ucb_score)
                    #print('n_parent',n_parent)
                    # Recurse down the tree
                    current = best_child
                    if len(current.sequence) < 4:
                        print('best_child:')
                        best_child.sequence[-1].printWord()

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

        # if not is_valid:
        #     print('invalid rollout from ' + current.sequence[-1].toString())
        #     print('to ' + rollout_word.toString())

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

            print('backprop start')

            list_of_parents = []
            list_of_parents.append(current)

            list_of_already_updated = []

            while list_of_parents:

                # Get and remove a parent from the list
                parent = list_of_parents.pop()

                # If not already updated
                if parent not in list_of_already_updated:
                    
                    # Update the average
                    if is_valid:
                        parent.updateAverage(rollout_reward, iter)
                        parent.updateBestRollout(rollout_word, rollout_reward)
                    else:
                        # Invalid (empty) BT gets a reward of 0
                        parent.updateAverage(0.0, iter)

                    # Add all parents to the list
                    list_of_parents.extend(parent.parents)

                    # Remember that we've already looked at this
                    list_of_already_updated.append(parent)
            print('backprop finished')

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
                    parent.updateAverage(rollout_reward, iter)
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
                    parent.updateAverage(rollout_reward, iter)
                    #parent.updateBestRollout(rollout_word, rollout_reward)

                    # Recurse up the tree
                    parent = parent.parents[0]

        # Remember the rollout score, for DAG merging
        all_iteration_rewards[iter] = rollout_reward

        # DAG: if the rollout was good, add extra parents
        if use_dag:
            if rollout_reward > 0:
                add_backwards_edges(cfg, dict_of_all_nodes, current, all_iteration_rewards, adding_nonzero_edges_steps, max_ancestors)

        # DAG: periodically add edges
        # for parents of best node at each level of DAG
        # AND add new rules
        if use_dag:
            if iter%iterations_between_adding_best_edges==0:

                # Find best node at each level
                max_depth = budget*2
                best_nodes = [None]*max_depth
                for node in list_of_all_nodes:
                    level = len(node.sequence)
                    if node.average_evaluation_score > 0:
                        if not best_nodes[level]:
                            best_nodes[level] = node
                        elif best_nodes[level].average_evaluation_score < node.average_evaluation_score:
                            best_nodes[level] = node

                # Add backward edges
                for node in best_nodes:
                    if node:
                        add_backwards_edges(cfg, dict_of_all_nodes, node, all_iteration_rewards, adding_best_edges_steps, max_ancestors)

            if iter%iterations_between_adding_production_rules==0:

                # Find the best node that contains sequenceX as part of its evaluation, for each X
                best_nodes_dict = dict()
                for node in list_of_all_nodes:
                    if node.average_evaluation_score > 0:

                        # Find which sequenceX types are seen here
                        relevant_chars = set()
                        for word in node.sequence:
                            for char in word.list:
                                if len(char.label) > 8 and char.label[0:8] == 'sequence':
                                    relevant_chars.add(char.label[8:])

                        if relevant_chars:

                            relevant_chars_sorted = sorted(relevant_chars)

                            key = "_".join(relevant_chars_sorted)
                            value_score = node.average_evaluation_score
                            try:
                                # Check if better than previous sequenceX
                                prev_value_score = best_nodes_dict[key].average_evaluation_score
                                if value_score > prev_value_score:
                                    best_nodes_dict[key] = node
                            except KeyError:
                                # First sequenceX
                                best_nodes_dict[key] = node

                print("best nodes for adding new production rules:")
                for node in best_nodes_dict.values():
                    node.sequence[-1].printWord()
                print("associated keys:")
                for key in best_nodes_dict.keys():
                    print(key)

                # Add new shortcut production rules
                for node in best_nodes_dict.values():
                    if node:
                        # subtree_words = extract_subtrees(node.sequence[-1])
                        # subtree_words.extend(extract_subtrees(node.best_rollout))
                        subtree_words = extract_subtrees(node.best_rollout)

                        # For each subtree of node
                        for subtree_word in subtree_words:

                            subtree_word_already_shortcut = False
                            for shortcut_word in shortcut_words:
                                if shortcut_word.equal(subtree_word):
                                    subtree_word_already_shortcut = True
                                    break

                            if not subtree_word_already_shortcut:

                                # Create a new production rule
                                shortcut_words.append(subtree_word)
                                input_word = createWord("sequence")
                                output_word = subtree_word
                                production_rule = ProductionRule(input_word, output_word)

                                # Add PR to CFG
                                is_added = cfg.addProductionRule(production_rule)

                                # If was correctly added to CFG
                                if is_added:

                                    # Apply PR to all nodes
                                    for node in list_of_all_nodes:

                                        # Apply production rule
                                        child_words = production_rule.applyProductionRule(node.sequence[-1])

                                        # For each word that results from applying the PR
                                        for child_word in child_words:

                                            # If already exists in tree
                                            child_exists, child_node = check_for_duplicates(dict_of_all_nodes, child_word)
                                            if child_exists:

                                                # Add child edge
                                                if child_node not in node.children:

                                                    # Merge rewards etc.

                                                    child_node.addParent(node)

                                                    # Also, merge the rewards of the child into the parent
                                                    # Do this recursively up the tree
                                                    list_of_parents = []
                                                    list_of_parents.append(node)

                                                    list_of_already_updated = []

                                                    while list_of_parents:

                                                        # Get and remove a parent from the list
                                                        parent = list_of_parents.pop()

                                                        # If not already updated
                                                        if parent not in list_of_already_updated:
                                                            
                                                            # Update the average
                                                            parent.mergeRewards(all_iteration_rewards, child_node)

                                                            # Add all parents to the list
                                                            list_of_parents.extend(parent.parents)

                                                            # Remember that we've already looked at this
                                                            list_of_already_updated.append(parent)

                                                # Make sure not in unpicked children
                                                child_node_word = child_node.sequence[-1]
                                                for unpicked_child_word_idx in xrange(len(node.unpicked_child_words)):
                                                    if node.unpicked_child_words[unpicked_child_word_idx].equal(child_node_word):
                                                        # Found it!
                                                        del node.unpicked_child_words[unpicked_child_word_idx]
                                                        break

                                            else:

                                                # Make sure not in unpicked child already
                                                already_unpicked_child = False
                                                for unpicked_child_word in node.unpicked_child_words:
                                                    if unpicked_child_word.equal(child_word):
                                                        # Found it!
                                                        already_unpicked_child = True
                                                        break

                                                # Add unpicked child
                                                if not already_unpicked_child:
                                                    node.unpicked_child_words.append(child_word)
                # Print all shortcut words
                print("All shortcut words:")
                for word in shortcut_words:
                    word.printWord()

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

def add_backwards_edges(cfg, dict_of_all_nodes, current_node, all_iteration_rewards, max_steps, max_ancestors):

    current_node_word = current_node.sequence[-1]

    if current_node.ancestor_words == None:

        # Get a list of existing parents, so we don't try to rederive those paths
        ignore_words = []
        for parent in current_node.parents:
            ignore_words.append(parent.sequence[-1])

        # Get a list of ancestor words of this word
        ancestors = cfg.derivePreviousWords(current_node_word, max_steps, ignore_words, max_ancestors)
        # current_node.ancestor_words = ancestors
    else:
        ancestors = current_node.ancestor_words

    print('add_backwards_edges current_node_word:')
    current_node_word.printWord()

    # print('add_backwards_edges ancestors:')
    # for a in ancestors:
    #     a.printWord()

    stats_count_ancestors = len(ancestors)
    stats_count_new_parents = 0

    # Keep track of parents that have already had their reward merged
    list_of_already_updated = []

    for ancestor in ancestors:

        # Does this ancestor exist in the DAG?
        ancestor_key = ancestor.toString()
        try:
            ancestor_node = dict_of_all_nodes[ancestor_key]
        except KeyError:
            # Not found!
            ancestor_node = None
            continue

        # If not already a parent?
        if ancestor_node not in current_node.parents:

            stats_count_new_parents += 1

            # Add them as parents
            current_node.addParent(ancestor_node)

            # Add me as child
            ancestor_node.children.append(current_node)

            # Removed from unpicked children if it exists
            for unpicked_child_word_idx in xrange(len(ancestor_node.unpicked_child_words)):
                if ancestor_node.unpicked_child_words[unpicked_child_word_idx].equal(current_node_word):
                    # Found it!
                    del ancestor_node.unpicked_child_words[unpicked_child_word_idx]
                    break
                

            # Merge rewards of all ancestors
            # Do this recursively up the DAG
            list_of_parents = []
            list_of_parents.append(ancestor_node)

            while list_of_parents:

                # Get and remove a parent from the list
                parent = list_of_parents.pop()

                # If not already updated
                if parent not in list_of_already_updated:
                    
                    # Update the average
                    parent.mergeRewards(all_iteration_rewards, current_node)

                    # Add all parents to the list
                    list_of_parents.extend(parent.parents)

                    # Remember that we've already looked at this
                    list_of_already_updated.append(parent)

    # Print stats
    print('add_backwards_edges stats_count_ancestors', stats_count_ancestors)
    print('add_backwards_edges stats_count_new_parents', stats_count_new_parents)
            
