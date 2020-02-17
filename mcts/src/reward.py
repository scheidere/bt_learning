'''
Basic MCTS implementation
Graeme Best
Oregon State University
Jan 2020
'''

from action import Action #, printActionSequence
from cfg import Word, Character
'''
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
    
    '''
def reward(word):

    # Another simple reward function to test A-tree cfg build

    reward = 0

    # Given current word, which is an instance of the cfg word class
    # Find number of A's in that word by checking char.equal()
    # given that char is an instance of the Character class
    # for each char in word

    num_A_in_string = 0
    char_A = Character("A")

    for char in word.list:
        if char.equal(char_A):
            num_A_in_string += 1

    # also penalise any non-terminal words
    non_terminal_penalty = 10
    char_children = Character("children")
    for char in word.list:
         if char.equal(char_children):
            num_A_in_string -= non_terminal_penalty

    if num_A_in_string < 0:
        num_A_in_string = 0

    if num_A_in_string <= 10:
        reward = num_A_in_string/10.0 #already normalized if num_A_in_string <= 10
    else:
        reward = 0

    return reward
    
