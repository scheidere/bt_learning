'''
Basic MCTS implementation
Graeme Best
Oregon State University
Jan 2020
'''

from cost import cost
import random
import copy

def rollout(subsequence, action_set, budget):
    # Random rollout policy
    # Pick random actions until budget is exhausted
    num_actions = len(action_set)
    if num_actions <= 0:
        raise ValueError('rollout: num_actions is ' + str(num_actions))
    sequence = copy.deepcopy(subsequence)
    while cost(sequence) < budget:
        r = random.randint(0,num_actions-1)
        sequence.append(action_set[r])

    return sequence

