

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

		self.score = 0
		self.finished = False

	def submit_target(self, robot_belief_idx, robot_location_idx, is_at_surface, is_in_comms, num_iterations):
		# robot_belief_idx: location where the robot believes the target is (because it is above a certain prob?)
		# robot_location_idx: vertex idx where robot is

		target_location_idx = self.world.vertex_target_idx
		#vertices_in_comms_range = self.world.vertices_in_comms_range

		# First, check if you are within comms range and at surface
		if is_at_surface and is_in_comms:
			if robot_belief_idx == target_location_idx:
				self.finished = True
				self.score = -num_iterations
				response = Scorer.RESPONSE_CORRECT
			else:
				response = Scorer.RESPONSE_FALSE
		else: # either not in comms range or not at surface so robot should receive nothing from basestation
			response == Scorer.RESPONSE_NONE

		return response


		#need to call this in Robot class

		#where does the robot make the choice of what belief vertex to submit? need this as input

		#what does the robot do given the output of the above function?	

