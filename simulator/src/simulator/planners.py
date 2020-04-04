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

    #go cw or ccw every vertex until to reach start vertex

class ZigZagPlanner(Planner):
    pass

    # alternate left and right choices of next vertex

class WallFollowPlanner(Planner):
    pass

    # less applicable to environment at hand

class GoToKnownTarget(Planner):
    pass
    # need to brainstorm/just will take more time

    # perhaps more helpful once we have multiple targets



class PlannerRandomWalk(Planner):
    def plan(self, debug=False):
        vertex_start_idx = self.robot.state.vertex_from_idx

        v_current = vertex_start_idx
        plan_length = 10
        action_sequence = []

        at_surface = self.world.vertices[vertex_start_idx].position.z > self.world.surface_level - 0.0001

        for i in range(plan_length):
            '''
            edges_out = self.world.edge_matrix[v_current]
            valid_vertices = []
            for v in xrange(len(edges_out)):
                if edges_out[v].exists and v != v_current:
                    # don't let the robot surface
                    allowed = True
                    if not at_surface:
                        edge_at_surface = self.world.vertices[v].position.z > self.world.surface_level - 0.0001
                        if edge_at_surface:
                            allowed = False
                    if allowed:
                        valid_vertices.append(v)
            '''
            edges_idx_out = self.world.edge_adjacency_idx_lists[v_current]
            if debug:
                print('edges_idx_out',edges_idx_out)
            valid_vertices = []
            for v_idx in edges_idx_out:
                allowed = True
                if not at_surface:
                    edge_at_surface = self.world.vertices[v_idx].position.z > self.world.surface_level - 0.0001
                    if edge_at_surface:
                        allowed = False
                if allowed:
                    valid_vertices.append(v_idx)

            if debug:
                print('valid_vertices',valid_vertices)

            if not valid_vertices:
                v_next = v_current
                if debug:
                    print('v_next is stationary')
            else:
                r = random.randint(0,len(valid_vertices)-1)
                v_next = valid_vertices[r]
                if debug:
                    print('v_next',v_next)
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
        '''
        edges_out = self.world.get_edges_out(vertex_idx)

        # filter out the non-existent edges
        edges_out_keep = []
        for e in edges_out:
            if e.exists:
                edges_out_keep.append(e)
        return edges_out_keep
        '''
        return self.world.edge_adjacency_edge_lists[vertex_idx]


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

class PlannerCommsRange(PlannerShortestPath):
    #this inherently only goes to vertices within comms range on the surface
    #world.vertices_in_comms_range is a list that only contains vertices in comms range on surface

    def set_parameters(self, vertex_start_idx): #can this just be removed?? Can figure this out by getting original shortest path planner to run...
        # Initial location, i.e. current location of robot, can be fed in
        self.vertex_start_idx = vertex_start_idx

        '''
        robot_vertex = self.world.vertices[vertex_start_idx]

        # Find closest vertex (this might be an issue since it is euclidean and not necessarily closest by edge cost)
        closest_vertex = None
        for vertex in self.world.vertices_in_comms_range:
            current_distance = distance(robot_vertex, vertex)
            if closest_vertex == None:
                closest_vertex = vertex
                shortest_distance = current_distance
            elif shortest_distance > current_distance:
                closest_vertex = vertex
                shortest_distance = current_distance


        self.vertex_goal_idx = closest_vertex.vertex_idx
        '''

        # DO NOT NEED GOAL
        # Will expand from the source node in graph (i.e. start vertex in map) to all other nodes
        # Finding the shortest path to every other node
        # Will do check at each visited node to see when one is in comms range, when one is found, stop

    def plan(self, debug=False):
        #rospy.loginfo("PlannerShortestPath plan()")
        #debug = True
        try: 
            self.vertex_start_idx
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

        if debug:
            print(self.vertex_start_idx)

        open_set = [True] * num_vertices

        #iteration_count = 0 # for debugging

        while not self.is_open_set_empty(open_set):

            #iteration_count = iteration_count + 1
            #rospy.logwarn("dijkstra iteration_count: " + str(iteration_count))

            # find the vertex in open_set that has minimum dist_to_go
            v_current = self.find_min_vertex(dist_to_go, open_set)

            # check if vertex is in comms range, and if so that is the goal
            # i.e. the goal is the shortest path to any vertex in comms range (calc'd outside loop)
            if v_current in self.world.vertices_in_comms_range:
                if debug:
                    print('vertex in comms',v_current,self.world.vertices[v_current].position)

                break

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
        v = v_current
        d = dist_to_go[v]
        if debug:
            print('distance to go',d)
        if debug:
            print "dijkstra goal: " + str(v_current)
            print(v,self.vertex_start_idx)
            print('prev',prev[v])
        if prev[v] >= 0 or v == self.vertex_start_idx:
            while v >= 0:
                path.insert(0, v)
                v = prev[v]
        if debug:
            print path
        return [d, path] 
