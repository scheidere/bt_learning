
import multirobot_behavior_tree
import copy

def reverse_first_level(tree):
    # Reverse the order of the nodes in the first level of the tree
    tree.root.children.reverse()

def combine_two_trees(tree1_in,tree2_in):
    # Join two trees as a sequence
    
    # Create deep copies of the original trees so they can still be used independently
    tree1 = copy.copy(tree1_in)
    tree2 = copy.copy(tree2_in)

    # Create a new empty tree
    tree_out = multirobot_behavior_tree.BehaviorTree('')

    # Create a root node
    root_node = multirobot_behavior_tree.Parallel(2)
    tree_out.root = root_node

    # Add the two trees as children of the root
    tree_out.root.add_child(tree1.root)
    tree_out.root.add_child(tree2.root)

    # Regenerate the nodes list
    tree_out.generate_nodes_list()

    # Ship it!
    return tree_out

def some_other_manipulation(tree):
    # ??
    pass
