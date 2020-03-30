#!/usr/bin/env python

import rospy
import robot
import world
import random
import sys

# base class... don't use directly
class Planner():
	def __init__(self, robot, world ):
		self.world = world
		self.robot = robot

	def plan(self):
		raise NotImplementedError()

class CirclePlanner(Planner):
	pass
	# need to brainstorm/just will take more time

class ZigZagPlanner(Planner):
	pass

class WallFollowPlanner(Planner):
	pass

class GoToKnownTarget(Planner):
	pass
	# need to brainstorm/just will take more time

class GoToSurface(Planner):
	pass ******

class GoToCommsRange(Planner):
	pass ******
	#need to define which vertices are in comms range in world.py


class PlannerRandomWalk(Planner):
	def plan(self):
		vertex_start_idx = self.robot.state.vertex_from_idx

		v_current = vertex_start_idx
		plan_length = 10
		action_sequence = []

		for i in range(plan_length):
			edges_out = self.world.edge_matrix[v_current]
			valid_vertices = []
			for v in xrange(len(edges_out)):
				if edges_out[v].exists and v != v_current:
					valid_vertices.append(v)

			if not valid_vertices:
				v_next = v_current
			else:
				r = random.randint(0,len(valid_vertices)-1)
				v_next = valid_vertices[r]
			action_sequence.append(v_next)
			v_current = v_next
		return action_sequence

class PlannerShortestPath(Planner):

	def set_parameters(self, vertex_start_idx, vertex_goal_idx, use_known_world):
		self.vertex_start_idx = vertex_start_idx
		self.vertex_goal_idx = vertex_goal_idx
		self.use_known_world = use_known_world

	def plan(self, debug=False):
		#rospy.loginfo("PlannerShortestPath plan()")
		try: 
			self.vertex_start_idx
			self.vertex_goal_idx
		except AttributeError:
			rospy.logerr("set_parameters() for dijkstras needs to be called")
			return None

		# rospy.loginfo("Calling dijkstras")
		[distance, path] = self.dijkstras(debug)
		if len(path) > 1:
			path = path[1:]
			return path
		else:
			#rospy.logwarn("no path to goal, or goal has been reached")
			return None
		
	def dijkstras(self, debug=False):
		num_vertices = len(self.world.vertices)
		dist_to_go = [sys.maxint] * num_vertices
		prev = [-1] * num_vertices
		dist_to_go[self.vertex_start_idx] = 0

		open_set = [True] * num_vertices

		#iteration_count = 0 # for debugging

		while not self.is_open_set_empty(open_set):

			#iteration_count = iteration_count + 1
			#rospy.logwarn("dijkstra iteration_count: " + str(iteration_count))

			# find the vertex in open_set that has minimum dist_to_go
			v_current = self.find_min_vertex(dist_to_go, open_set)

			# remove it from the open set
			open_set[v_current] = False

			# get the set of neighbours
			neighbours = self.get_neighbours(v_current)

			# expand neighbouring nodes
			for e in neighbours:
				v_next = e.vertex_end_idx
				if open_set[v_next] == True:
					alternative_distance = dist_to_go[v_current] + e.cost
					if alternative_distance < dist_to_go[v_next]:
						dist_to_go[v_next] = alternative_distance
						prev[v_next] = v_current

		# backtrack to find path and distance
		path = []
		v = self.vertex_goal_idx
		d = dist_to_go[v]
		if debug:
			print "dijkstra goal: " + str(self.vertex_goal_idx)
		if prev[v] >= 0 or v == self.vertex_start_idx:
			while v >= 0:
				path.insert(0, v)
				v = prev[v]
		if debug:
			print path
		return [d, path] 

	def is_open_set_empty(self, open_set):
		for i in open_set:
			if i == True:
				return False
		return True

	def get_neighbours(self, vertex_idx):
		edges_out = self.world.get_edges_out(vertex_idx)

		# filter out the non-existent edges
		edges_out_keep = []
		for e in edges_out:
			if e.exists:
				edges_out_keep.append(e)
		return edges_out_keep


	def find_min_vertex(self, dist_to_go, open_set):
		
		min_idx = -1
		min_value = sys.maxint

		for i in xrange(len(dist_to_go)):
			
			value = dist_to_go[i]
			if open_set[i] == True:
				if value <= min_value:

					min_value = value
					min_idx = i
		return min_idx
