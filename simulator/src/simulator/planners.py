#!/usr/bin/env python

import rospy
import robot
import world
import random
import sys
import numpy as np
import copy

# base class... don't use directly
class Planner():
    def __init__(self, robot, world ):
        self.world = world
        self.robot = robot

    def plan(self):
        raise NotImplementedError()

class PlannerRandomWalk(Planner):
    def plan(self, debug=False):
        vertex_start_idx = self.robot.state.vertex_from_idx

        v_current = vertex_start_idx
        if debug:
            print('v_current: ', v_current)
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
        if debug:
            print('action_sequence: ', action_sequence)
        return action_sequence

class PlannerShortestPath(Planner):

    def set_parameters(self, vertex_start_idx, vertex_goal_idx):
        self.vertex_start_idx = vertex_start_idx
        self.vertex_goal_idx = vertex_goal_idx

        # if find_nearest_target returned None (doesn't think it knows where any targets are)
        if self.vertex_goal_idx == None: # Check with Graeme
            rospy.logerr("PlannerShortestPath() goal vertex is None") #maybe just print it instead 
            #pause()           


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
        if path == []: # Check with Graeme
            return path 
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
        # Check if goal vertex is None # Check with Graeme
        if v == None:
            return [None,[]]
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

class PlannerCoverage(PlannerShortestPath):

    def set_parameters(self, vertex_start_idx):
        self.vertex_start_idx = vertex_start_idx

        # Replaced logic below with check in dijkstra's to ensure planning to NEAREST unvisited location
        '''
        # visit_tracker same size as classes_y, initially 0's to denote unvisited, 1 once visited
        # Should come from robot class since robot knows where it has been

        unvisited_indices = []
        for idx in range(len(self.robot.visit_tracker)):
                if self.robot.visit_tracker[idx] == 0:
                    unvisited_indices.append(idx)

        print("unvisited_indices", unvisited_indices)
        print("length of unvisited_indices", len(unvisited_indices))
        print("visit tracker", self.robot.visit_tracker)
        # Choose randomly from unvisited list
        if len(unvisited_indices) > 0:
            self.vertex_goal_idx = random.choice(unvisited_indices)
            print("goal idx",self.vertex_goal_idx)
            #print("before visit update: ", self.robot.visit_tracker)
            #self.robot.visit_tracker[self.vertex_goal_idx] = 1 # mark as visited ??? Need to do this in robot.py
            #print("after visit update: ", self.robot.visit_tracker)
        else:
            self.vertex_goal_idx = random.randint(0,self.world.num_nodes - 1) # random_walk once visited everywhere

        while self.vertex_start_idx == self.vertex_goal_idx:
            self.vertex_goal_idx = random.randint(0,self.world.num_nodes - 1) # random_walk once visited everywhere

        # if find_nearest_target returned None (doesn't think it knows where any targets are)
        if self.vertex_goal_idx == None: # Check with Graeme
            rospy.logerr("PlannerShortestPath() goal vertex is None") #maybe just print it instead 
            #pause()           
        '''

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

            # check if vertex has not been visited, and if so that is the goal
            # i.e. the goal is the shortest path to any vertex that has not been visited (i.e. 0 in tracker)
            if self.robot.visit_tracker[v_current] == 0:
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

class PlannerPeakBelief(PlannerShortestPath):
    # find shortest path from robot current location to vertex with highest probability of being target

    def set_parameters(self,vertex_start_idx, target_belief): # Check with Graeme: goal idx/y + rename
        self.vertex_start_idx = vertex_start_idx
        self.target_belief = target_belief
        self.vertex_goal_idx, self.vertex_goal_y = self.target_belief.generateTargetBeliefIdxClass()#self.target_belief.generateRobotBeliefIdx()

        while self.vertex_start_idx == self.vertex_goal_idx: #if you get stuck at the peak, go to a random other location
            self.vertex_goal_idx = random.randint(0,self.world.num_nodes - 1)

    # has a goal, unlike comms range (which has a list of possible goals)
    # goal is updated every iteration (since prob_dist also updated)
    # need to change things in robot.py to implement correctly (also bt_list.yaml) 


class PlannerResurface(PlannerShortestPath):

    def set_parameters(self, vertex_start_idx):
        self.vertex_start_idx = vertex_start_idx

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

            # check if vertex is at surface, and if so that is the goal
            # i.e. the goal is the shortest path to any vertex in comms range (calc'd outside loop)
            if self.world.vertices[v_current].position.z == 0: # Check with Graeme DONE
                if debug:
                    print('vertex at surface',v_current,self.world.vertices[v_current].position)

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
