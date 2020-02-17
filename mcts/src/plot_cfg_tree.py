#!/usr/bin/env python

# do
#pip install graphviz


from graphviz import Digraph
from cfg import Word, Character, CFG
from tree_node import TreeNode

'''
todo:
* make color = score
* hide text -- show as tooltip instead
* make winner a different shape/color
* identify by node, not label -- so that non-unique labels aren't combined
* display something when unpicked children exists -- perhaps draw the node (that doesn't exist) grayed out
'''


def plot_cfg_tree(list_of_all_nodes, winner, use_uct, max_height, exploration_exploitation_parameter):

    # Start a graphviz graph
    u = Digraph('search tree', filename='tree.gv', node_attr={'color': 'lightblue2', 'style': 'filled'})
    u.attr(size='6,6')

    # For color ranges, get min and max rewards
    min_reward = 9999
    max_reward = -9999
    rewards = []
    for n in list_of_all_nodes:
        reward = getReward(n, use_uct)
        rewards.append(reward)
        node_height = len(n.sequence)
        if node_height <= max_height:
            
            if reward > max_reward:
                max_reward = reward
            if reward < min_reward:
                min_reward = reward

    # Sort the nodes by rewards
    # doesnt guarantee drawing order though...
    sorted_list_of_all_nodes = [n for _,n in sorted(zip(rewards,list_of_all_nodes))]

    # Create an edge for every parent-child pair
    included_list = []
    for n in sorted_list_of_all_nodes:

        included = False

        # Create a node
        # give a unique identifier
        node_id = str(id(n))        

        # If not root node
        if n.parent:

            node_height = len(n.sequence)
                
            # if the node is not too deep
            if node_height <= max_height:

                # Create a node
                reward = getReward(n, use_uct)
                col = getColor(reward, min_reward, max_reward) 
                u.node(node_id, n.sequence[-1].toString(), color=col)
                # u.node(node_id, n.sequence[-1].toString() + "\n" + str(reward), color=col)
                included = True
                
                # Add an edge back to the parent
                parent_id = str(id(n.parent))
                u.edge(parent_id, node_id)

            # if the children are being cut off due to max_height
            if node_height == max_height and len(n.children) > 0:
                node_id_cont = str(node_id + "...")
                u.node(node_id_cont, "...", shape="plaintext")
                u.edge(node_id, node_id_cont)

            if node_height < max_height:

                # if child has unpicked children
                for unpicked_child_word in n.unpicked_child_words:

                    # Create a new node
                    string_unpicked_child = unpicked_child_word.toString()
                    node_id_unpicked_child = str(id(string_unpicked_child)) + string_unpicked_child
                    u.node(node_id_unpicked_child, string_unpicked_child, color="white", style="dotted")

                    # Edge
                    u.edge(node_id, node_id_unpicked_child, style="dotted")

        else:

            # Create a node for the root
            col = getColor(getReward(n, use_uct), min_reward, max_reward) 
            u.node(node_id, n.sequence[-1].toString(), color=col)
            included = True

        included_list.append(included)


    # Force child order
    # This breaks things -- need to have subgraphs of child groups -- not subgraphs at each level
    # Will fix sometime...
    '''
    c = []
    nodes_lists = []
    for h in range(max_height+1):
        c.append(Digraph('child' + str(h)))
        c[h].attr(rank='same', rankdir='LR')
        nodes_lists.append([])
    for n_idx in range(len(sorted_list_of_all_nodes)):
        if included_list[n_idx]:
            n = sorted_list_of_all_nodes[n_idx]
            n_id = str(id(n))
            height = len(n.sequence)
            c[height].node(n_id)
            nodes_lists[height].append(n)
    for h in range(max_height+1):
        nodes_list = nodes_lists[h]
        for i in range(len(nodes_list) - 1):
            u.edge(str(id(nodes_list[i])), str(id(nodes_list[i+1])),style='invisible')
        u.subgraph(c[h])
    '''

    # View it
    u.view()


def getReward(node, use_uct):
    return node.average_evaluation_score

def getColor(reward, min_reward, max_reward):
    
    '''
    g = (reward - min_reward) / (max_reward - min_reward) + min_reward
    if g > 1:
        g = 1
    elif g < 0:
        g = 0
    r = 1 - g
    b = 0
    '''

    # colormap
    # adapted from http://blogs.perl.org/users/ovid/2010/12/perl101-red-to-green-gradient.html
    middle = (min_reward + max_reward) / 2
    if reward < min_reward:
        r = 1
        g = 0
        b = 0
    elif reward > max_reward:
        r = 0
        g = 1
        b = 0
    elif reward < middle:
        r = 1
        g = (reward - min_reward) / (middle - min_reward)
        b = 0
    else: 
        r = 1 - (reward - middle) / (middle - min_reward)
        g = 1
        b = 0

    r *= 255.0
    g *= 255.0
    b *= 255.0

    rgb = (r,g,b)
    hex = '#%02x%02x%02x' % rgb
    return hex

'''
# example from
# https://graphviz.readthedocs.io/en/stable/examples.html
u = Digraph('unix', filename='unix.gv',
            node_attr={'color': 'lightblue2', 'style': 'filled'})
u.attr(size='6,6')

u.edge('5th Edition', '6th Edition')
u.edge('5th Edition', 'PWB 1.0')
u.edge('6th Edition', 'LSX')
u.edge('6th Edition', '1 BSD')
u.edge('6th Edition', 'Mini Unix')
u.edge('6th Edition', 'Wollongong')
u.edge('6th Edition', 'Interdata')
u.edge('Interdata', 'Unix/TS 3.0')
u.edge('Interdata', 'PWB 2.0')
u.edge('Interdata', '7th Edition')
u.edge('7th Edition', '8th Edition')
u.edge('7th Edition', '32V')
u.edge('7th Edition', 'V7M')
u.edge('7th Edition', 'Ultrix-11')
u.edge('7th Edition', 'Xenix')
u.edge('7th Edition', 'UniPlus+')
u.edge('V7M', 'Ultrix-11')
u.edge('8th Edition', '9th Edition')
u.edge('1 BSD', '2 BSD')
u.edge('2 BSD', '2.8 BSD')
u.edge('2.8 BSD', 'Ultrix-11')
u.edge('2.8 BSD', '2.9 BSD')
u.edge('32V', '3 BSD')
u.edge('3 BSD', '4 BSD')
u.edge('4 BSD', '4.1 BSD')
u.edge('4.1 BSD', '4.2 BSD')
u.edge('4.1 BSD', '2.8 BSD')
u.edge('4.1 BSD', '8th Edition')
u.edge('4.2 BSD', '4.3 BSD')
u.edge('4.2 BSD', 'Ultrix-32')
u.edge('PWB 1.0', 'PWB 1.2')
u.edge('PWB 1.0', 'USG 1.0')
u.edge('PWB 1.2', 'PWB 2.0')
u.edge('USG 1.0', 'CB Unix 1')
u.edge('USG 1.0', 'USG 2.0')
u.edge('CB Unix 1', 'CB Unix 2')
u.edge('CB Unix 2', 'CB Unix 3')
u.edge('CB Unix 3', 'Unix/TS++')
u.edge('CB Unix 3', 'PDP-11 Sys V')
u.edge('USG 2.0', 'USG 3.0')
u.edge('USG 3.0', 'Unix/TS 3.0')
u.edge('PWB 2.0', 'Unix/TS 3.0')
u.edge('Unix/TS 1.0', 'Unix/TS 3.0')
u.edge('Unix/TS 3.0', 'TS 4.0')
u.edge('Unix/TS++', 'TS 4.0')
u.edge('CB Unix 3', 'TS 4.0')
u.edge('TS 4.0', 'System V.0')
u.edge('System V.0', 'System V.2')
u.edge('System V.2', 'System V.3')

u.view()
'''