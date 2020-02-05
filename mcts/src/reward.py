'''
Basic MCTS implementation
Graeme Best
Oregon State University
Jan 2020
'''

from action import Action #, printActionSequence

def reward(action_sequence):
    # A simple reward function

    # Iterate through the sequence, looking at pairs
    reward = 0
    for i in range(len(action_sequence)-1): # Yes, we want -1 here
        
        # Pick out a pair
        first = action_sequence[i]
        second = action_sequence[i+1]

        # Add to the reward if second is +1
        if first.id + 1 == second.id:
            reward += 1

    # Also give reward for first action by itself
    if action_sequence[0].id == 1:
        reward += 1

    # Normalise between 0 and 1
    max_reward = len(action_sequence) #-1
    if max_reward == 0:
        reward_normalised = 0
    else:
        reward_normalised = float(reward) / float(max_reward)
    return reward_normalised
