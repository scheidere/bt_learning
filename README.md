# bt_learning

## Prerequisites

Confirm use of Python 2. Use ```conda deactivate``` to revert from Anaconda Python 3 if relevant.
Follow prompts to install dependencies (sorry), e.g.
```
pip install graphviz
```

## How to run

First, check that the output paths in main.py, all\_methods.py, and plot\_results.py in the mcts package are pointing to folders that exist on your system, and are consistent.

### To run the final MCDAGS+SA method:
```
roslaunch mcts all_methods.launch config:=final
```
### To run just MCDAGS (which is what we want for AI535 neural net project contexts):
```
roslaunch mcts all_methods.launch config:=no_sa
```
### To plot results, go to plot_results.py in the mcts package:
- Ensure the paths in plot_results.py match the final and intermediate output file folder paths on your system
- To plot MCDAGS (no_sa) results:
```
roslaunch mcts plot_results.launch config:=no_sa
``` 
### To generate training data for the neural net:
- Change parameters (number of MCDAGS rounds, number of iterations per round, etc.) in mcts/config/data_generation.yaml
- Ensure the output directory path matches the path on your system
- Generate data:
```
roslaunch mcts all_methods.launch config:=data_generation
```
