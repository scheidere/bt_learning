'''
Basic MCTS implementation
Graeme Best
Oregon State University
Jan 2020
'''

class TreeNode():
    def __init__(self, parent, sequence, budget, unpicked_child_words):
        # tree properties
        self.parent = parent        
        self.children = []
        self.unpicked_child_words = unpicked_child_words

        # sequence properties
        self.sequence = sequence
        self.budget = budget

        # reward estimate properties
        self.average_evaluation_score = 0
        self.num_updates = 0

        # rollout solutions
        self.best_rollout = None
        self.best_rollout_evaluation_score = 0

    def updateBestRollout(self, rollout, rollout_evaluation_score):
        if (self.best_rollout == None) or (rollout_evaluation_score >= self.best_rollout_evaluation_score):
            self.best_rollout = rollout
            self.best_rollout_evaluation_score = rollout_evaluation_score

    def updateAverage(self, evaluation_score):
        # Incremental update to the average
        self.average_evaluation_score = float(self.average_evaluation_score * self.num_updates + evaluation_score) / float(self.num_updates + 1)
        self.num_updates = self.num_updates + 1



def countNodes(current):
    count = 1
    for child in current.children:
        count += countNodes(child)
    return count


