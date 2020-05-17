'''
Basic MCTS implementation
Graeme Best
Oregon State University
Jan 2020
'''

class TreeNode():
    def __init__(self, parents, sequence, budget, unpicked_child_words):
        # tree properties
        #self.parent = parent    
        self.parents = parents    
        self.children = []
        self.unpicked_child_words = unpicked_child_words

        # sequence properties
        self.sequence = sequence
        self.budget = budget

        # reward estimate properties
        self.average_evaluation_score = 0
        self.num_updates = 0

        # for dag, number of times selected by UCB -- not this is different to num_updates
        self.num_selections = 0

        # rollout solutions
        self.best_rollout = None
        self.best_rollout_active_words = []
        self.best_rollout_evaluation_score = 0

        # keep track of which iterations where the backtracking passed through this node
        self.activated_iterations = set()

        # remember ancestor words (if they are computed) so they don't need to be recomputed
        self.ancestor_words = None

    def updateBestRollout(self, rollout, rollout_active_words, rollout_evaluation_score):
        if (self.best_rollout == None) or (rollout_evaluation_score >= self.best_rollout_evaluation_score):
            self.best_rollout = rollout
            self.best_rollout_evaluation_score = rollout_evaluation_score
            self.best_rollout_active_words = rollout_active_words

    def updateAverage(self, evaluation_score, iteration_number):
        # Incremental update to the average
        self.average_evaluation_score = float(self.average_evaluation_score * self.num_updates + evaluation_score) / float(self.num_updates + 1)
        self.num_updates = self.num_updates + 1
        self.activated_iterations.add(iteration_number)

    def updateNumSelections(self):
        self.num_selections += 1

    def addParent(self, new_parent):
        self.parents.append(new_parent)

    def mergeRewards(self, all_iteration_rewards, other_node):
        # print("mergeRewards old", self.average_evaluation_score, self.num_updates, self.activated_iterations)
        # print("mergeRewards child", other_node.average_evaluation_score, other_node.num_updates, other_node.activated_iterations)
        # First, merge the activated_iterations list
        # Since it is a set, this will take care of duplicates
        self.activated_iterations.update(other_node.activated_iterations)

        # Update the score
        self.num_updates = len(self.activated_iterations)
        reward_sum = 0
        for iter in self.activated_iterations:
            reward_sum += all_iteration_rewards[iter]
        self.average_evaluation_score = float(reward_sum) / float(self.num_updates)
        # print("mergeRewards merged", self.average_evaluation_score, self.num_updates, self.activated_iterations)

        # Update best rollout too
        self.updateBestRollout(other_node.best_rollout, other_node.best_rollout_active_words, other_node.best_rollout_evaluation_score)


def countNodes(current):
    count = 1
    for child in current.children:
        count += countNodes(child)
    return count


