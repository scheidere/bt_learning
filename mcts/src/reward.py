'''
Basic MCTS implementation
Graeme Best
Oregon State University
Jan 2020
'''

from action import Action #, printActionSequence
from cfg import Word, Character
# from run_simulator import UnderwaterSimulator


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
'''
'''
def reward(word):

    # Simple reward function to test behavior tree production rules

    reward = 0

    # Given current word, which is an instance of the cfg word class
    # Find number of sets of parentheses in that word to determine depth from root (1 set is depth = 1)

    # The number of sets of parentheses is equivalent to the number of one kind of parenthesis (i.e. ( or ))
    num_sets_parentheses = 0
    char_p = Character("(")

    for char in word.list:
        if char.equal(char_p):
            num_sets_parentheses += 1

    # also penalise any non-terminal words
    non_terminal_penalty = 10
    char_children = Character("children")
    for char in word.list:
         if char.equal(char_children):
            num_sets_parentheses -= non_terminal_penalty

    if num_sets_parentheses < 0:
        num_sets_parentheses = 0

    if num_sets_parentheses <= 10:
        reward = num_sets_parentheses/10.0 #already normalized if num_A_in_string <= 10
    else:
        reward = 0

    return reward

'''




###RUN SIMULATOR (which returns reward)
'''
def reward(word, max_iterations, underwater_simulator): # single target case

    distance_scale = 20.0
    # roughly...
    min_reward = -max_iterations - (underwater_simulator.config['environment_size'][0] + underwater_simulator.config['environment_size'][1])/distance_scale
    max_reward = 0

    word.printWord()

    num_simulations = 1

    if word.list:
        is_valid = True
        reward_sum = 0
        for i in xrange(num_simulations):
            temp_reward, robot_reported, distance = underwater_simulator.generateReward(word, max_iterations)
            #if robot_reported: #but was wrong
            print('robot_reported:', robot_reported)
            print('temp_reward:', temp_reward)
            print('distance:', distance)
            if robot_reported:
                temp_reward = temp_reward/2.0 - distance/distance_scale
            else:
                temp_reward = temp_reward - distance/distance_scale
            print('temp_reward', temp_reward)
            reward_sum += temp_reward

        reward = float(reward_sum) / float(num_simulations)
        print(reward)
    else:
        is_valid = False
        reward = min_reward

    # Normalisation
    reward = float(reward - min_reward)/float(max_reward - min_reward)

    return is_valid, reward
'''
def reward(word, max_iterations, underwater_simulator): # multi-target case

    min_reward = 0
    max_reward = 100 # Our tree gets 75 on average # or avg_num_targets_in_world * max_reward_per_target

    best_temp_reward = 0 # Check with Graeme

    word.printWord()

    num_simulations = 3

    if word.list:
        is_valid = True
        reward_sum = 0
        for i in xrange(num_simulations):
            temp_reward, robot_reported, distance = underwater_simulator.generateReward(word, max_iterations)
            reward_sum += temp_reward
            
            if i == 1: # Check with Graeme
                best_temp_reward = temp_reward
            elif temp_reward > best_temp_reward:
                best_temp_reward = temp_reward

        reward = float(reward_sum) / float(num_simulations) # average, not-normalized
        #print("reward",reward)

    else:
        is_valid = False
        reward = min_reward
        best_reward = min_reward

    # Normalisation
    reward = float(reward - min_reward)/float(max_reward - min_reward)
    print("reward",reward)
    best_reward = float(best_temp_reward - min_reward)/float(max_reward - min_reward)

    return is_valid, reward, best_reward


'''
if __name__ == "__main__":

    word = Word([Character("->"),Character("("),Character("[]"),Character("?"),Character("("),Character("[]"),Character("()"),Character(")"),Character(")")])

    reward(word)

    print(reward(word))
'''