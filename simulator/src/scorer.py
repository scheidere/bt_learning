

'''
Robot can submit "answers" or locations of targets to the scorer (i.e. basestation)
Scorer knows the correct answer

If robot gets answer correct, reward is -time it took (time meaning number of iterations (in robot controller))
If answer is wrong, scorer tells robot its "False" (so robot knows to go back and look again)

Robot should only be allowed to interact with the scorer within comm range and while at surface

If robot tries to communicate when not at surface or not within comm range, scorer returns "no response"

Need to extract how many iterations are taken at the "time" the robot reports an answer
'''


class Scorer():

	RESPONSE_CORRECT = 1
	RESPONSE_FALSE = 2
	RESPONSE_NONE = 3

	def __init__(self, world):
		pass

	def submit_target(self, target_location, robot_state):
		#Scorer.RESPONSE_CORRECT
		pass

		#return Correct, False or No Response (i.e.)

