# bt_learning

## Prerequisites

Confirm use of Python 2. Use ```conda deactivate``` to revert from Anaconda Python 3 if relevant.
Follow prompts to install dependencies (sorry), e.g.
```
pip install graphviz
```

## How to run

To run the final MCDAGS+SA method:
```
roslaunch mcts all_methods.launch config:=final
```
To run just MCDAGS:
```
roslaunch mcts all_methods.launch config:=no_sa
```
To plot results, go to plot_results.py in the mcts package:
- Change the paths in plot_results.py to match the final and intermediate output file folder paths on your system
- Run ```roslaunch mcts plot_results.launch config:=no_sa``` to plot MCDAGS (no_sa) results
