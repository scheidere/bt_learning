# Behavior Tree Manipulation

Modified behavior tree to achieve some combination of:

* autonomously learning the structure of the tree
* applicability to multi-robot scenarios

## Overview

??

## Usage

Save your input tree file to the `behavior_tree/config` directory.

Edit the launch file `behavior_tree/launch/bt_manipulation.launch` to specify your config filename.

To read in a (multi-robot) tree file, manipulate it, then save it to a new file, run:
```
roslaunch behavior_tree bt_manipulation.launch
```

Currently, the manipulation will take two copies of the tree, reverse one of them, then join the two trees into one, connected by a parallel root node.

The output tree will be saved as `behavior_tree/config/<<input_filename>>_manipulated.tree`

## Who do I contact?

* Emily Scheide
* Graeme Best