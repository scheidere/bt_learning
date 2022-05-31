'''
Basic MCTS implementation
Graeme Best
Oregon State University
Jan 2020
'''

from action import Action #, printActionSequence
from cfg import Word, Character, createWord
from simulator.run_simulator import UnderwaterSimulator


def reward(word, max_iterations, underwater_simulator, min_reward, max_reward): # multi-target case

    best_temp_reward = 0 # Check with Graeme

    word.printWord()

    num_simulations = 1
    active_words = []

    if word.list:
        is_valid = True
        reward_sum = 0
        for i in xrange(num_simulations):
            print("LOOK")
            #test = underwater_simulator.generateReward(word, max_iterations)
            #print('test length' + str(len(test)))
            temp_reward, robot_reported, distance, active_word, active_subtree_indices = underwater_simulator.generateReward(word, max_iterations)
            print('active_subtree_indices', active_subtree_indices)
            active_words.append(active_word)
            print("Active word:")
            active_word.printWord()
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
        active_subtree_indices = []

    # Normalisation
    reward = float(reward - min_reward)/float(max_reward - min_reward)
    print("reward",reward)
    best_reward = float(best_temp_reward - min_reward)/float(max_reward - min_reward)

    return is_valid, reward, best_reward, active_words, active_subtree_indices



if __name__ == "__main__":

    word = Word([Character("->"),Character("("),Character("[]"),Character("?"),Character("("),Character("[]"),Character("()"),Character(")"),Character(")")])
    #word = createWord('? ( -> ( (target_found) ? ( (in_comms) [go_to_comms] ) [report] ) -> ( (mine_found) ? ( <!> ( (is_armed) ) [disarm] ) ) -> ( ? ( <!> ( (carrying_object) ) [take_to_drop_off] ) (object_found) [pick_up] ) -> ( (likely_target_found) [go_to_likely_target] ) -> ( [random_walk] ) )')

    underwater_simulator = UnderwaterSimulator()
    is_valid, rollout_reward, best_rollout_reward, rollout_active_words = reward(word, 200, underwater_simulator)

    print('is_valid, rollout_reward, best_rollout_reward, rollout_active_words',is_valid, rollout_reward, best_rollout_reward, rollout_active_words)
