

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
		self.world = world

	def submit_target(self, target_location, robot_belief):
		# target_location is where the target actually is, i.e. y
		# robot_belief is the location where the robot believes the target is (because it is above a certain prob?)
		
		if robot_belief == target_location:
			response = Scorer.RESPONSE_CORRECT
		elif robot_belief != None:
			response = Scorer.RESPONSE_FALSE
		else:
			response == Scorer.RESPONSE_NONE

		return response


		#need to call this in Robot class

		#where does the robot make the choice of what belief vertex to submit? need this as input

		#what does the robot do given the output of the above function?	

