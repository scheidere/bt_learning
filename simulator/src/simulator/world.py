#!/usr/bin/env python

import rospy
import rospkg
import sys
import yaml
import random
import numpy as np

import cPickle as pickle
#from simulator.srv import PickleString
from geometry_msgs.msg import Point

#from simulator.msg import EdgeObservation

#from robot import TargetBelief

import matplotlib.pyplot as plt

from math import sqrt

def distance(vertex_start, vertex_end):
    # Euclidean distance, for now
    #return ( (vertex_start.position.x-vertex_end.position.x)**2 + (vertex_start.position.y-vertex_end.position.y)**2 + (vertex_start.position.z-vertex_end.position.z)**2)**0.5
    x = (vertex_start.position.x-vertex_end.position.x)
    y = (vertex_start.position.y-vertex_end.position.y)
    z = (vertex_start.position.z-vertex_end.position.z)
    return sqrt( x*x + y*y + z*z )

def distance_to_base(vertex):
    # Euclidean distance from basestation at 0,0,0 to vertex
    return ( (vertex.position.x-0)**2 + (vertex.position.y-0)**2 + (vertex.position.z-0)**2)**0.5

# Generalized (including z) vertex
class Vertex():
    def __init__(self, x, y, z, vertex_idx):
        self.position = Point(x,y,z)
        self.vertex_idx = vertex_idx

class Edge():
    def __init__(self, vertex_start_idx, vertex_end_idx, cost, exists):
        self.vertex_start_idx = vertex_start_idx
        self.vertex_end_idx = vertex_end_idx
        self.cost = cost
        self.potentially_exists = exists
        self.exists = exists
        self.known = True

class GraphPickle():
    def __init__(self, vertices, edge_matrix):
        self.vertices = vertices
        self.edge_matrix = edge_matrix

class World():
    def __init__(self, config):

        # Create a world
        self.config = config
        self.surface_level = 0

    def init_world(self, seed1, do_test=True):
        # create a blank world, PRM style
        random.seed(seed1) # for repeatable trials
        num_nodes = self.config["num_nodes"]
        connection_radius = self.config["connection_radius"]
        environment_size = self.config["environment_size"]

        # vertices
        vertices_surface = []
        self.vertices = []
        count = 0
        for vertex_idx in xrange(num_nodes):
            x = random.uniform(0, environment_size[0])
            y = random.uniform(0, environment_size[1])
            for z in [-10,self.surface_level]:
                v = Vertex(x,y,z,count)
                count += 1
                self.vertices.append(v)
                if z == self.surface_level:
                    vertices_surface.append(True)
                else:
                    vertices_surface.append(False)


        # edges, stored as a matrix indexed as [vertex_start, vertex_end]
        num_nodes = len(self.vertices) #doubled the input num_nodes in creating two layers of vertices instead of one
        self.edge_matrix = [None] * num_nodes        
        for vertex_start_idx in xrange(num_nodes):
            self.edge_matrix[vertex_start_idx] = [None] * num_nodes
            for vertex_end_idx in xrange(num_nodes):

                cost = distance(self.vertices[vertex_start_idx], self.vertices[vertex_end_idx])
                if cost <= connection_radius and not (vertices_surface[vertex_start_idx] and vertices_surface[vertex_end_idx]):  
                    exists = True 
                else:
                    exists = False
                edge = Edge(vertex_start_idx, vertex_end_idx, cost, exists)
                self.edge_matrix[vertex_start_idx][vertex_end_idx] = edge

        if do_test:
            self.test_indices()

        self.vertex_target_idx = self.create_target_idx()

        self.comms_range = self.config["comms_range"]

        self.vertices_in_comms_range = self.generateCommsRangeVertices()
    '''
    #old likelihood function we have replaced
    # it did not account for beyond sensor range -> 0
    def robot_env_observations(self, vertex_robot, vertex_target):
        # need robot location, robot sensor model, and the actual target location

        # Do we want to have a field of view or assume 360 degree awareness for now?

        # Do we really need to get closer to a target ever once we are in range?

        # Where do we check if we have already sensed the particular target?
        # wouldn't want to just keep circling back to the same target and reporting it
        sensor_range = self.config["sensor_range"]

        distance_to_target = distance(vertex_robot, vertex_target)
        if distance_to_target <= sensor_range:
                prob_true_pos = 0.95 - 0.01*distance_to_target
                #prob_false_pos = 0.2 - 0.01*distance_to_target
            # True positive
            if random.random() <= prob_true_pos:
                robot_senses_target = True
                return vertex_target
            else: # False negative
                robot_senses_target = False
        else:
            # False positive
            if random.random() <= prob_false_pos:
                robot_senses_target = True
                # for vertex in range pick a random one 
                    vertex_near_robot = 
                return vertex_near_robot # near defined as within sensor_range
            else: # True negative
                robot_senses_target = False

        if robot_senses_target:
            return True
        else:
            return False
    '''

    def generateCommsRangeVertices(self):
        idx_list = []
        for vertex in self.vertices:
            if distance_to_base(vertex) < self.comms_range and vertex.position.z > self.surface_level - 0.0001:
                idx_list.append(vertex.vertex_idx)

        return idx_list #list of indices of vertices in comms range (and at surface)

    def robot_env_observations(self, vertex_robot_idx): 
        likelihoods = self.sensor_model.all_likelihoods(vertex_robot_idx, self.vertex_target_idx)
        #return a single observation, z based on the probability distribution
        return np.random.choice(a=len(self.vertices)+1, p=likelihoods)

    def set_sensor_model(self, sensor_model):
        # normally do this is __init__, but in this context the sensor model gets created after init

        self.sensor_model = sensor_model

    def create_target_idx(self):
        #pick random vertex
        random_vertex_idx = random.randrange(len(self.vertices))

        #random_vertex = self.vertices[random_vertex_idx]

        return random_vertex_idx

    def pickle_graph(self):
        graph = GraphPickle(self.vertices, self.edge_matrix)
        return pickle.dumps( graph )

    def test_indices(self):
        # sanity check that graph was constructed correctly
        rospy.loginfo("running graph test")
        num_nodes = len(self.vertices)  
        if num_nodes <= 0:
            rospy.logerr("empty graph created")

        for vertex_idx in xrange(num_nodes):
            if self.vertices[vertex_idx].vertex_idx != vertex_idx:
                rospy.logerr("vertex index test failed")

        for vertex_start_idx in xrange(num_nodes):
            for vertex_end_idx in xrange(num_nodes):
                #print(self.edge_matrix[vertex_start_idx][vertex_end_idx].vertex_start_idx,vertex_start_idx)
                if self.edge_matrix[vertex_start_idx][vertex_end_idx].vertex_start_idx != vertex_start_idx:
                    rospy.logerr("edge index start test failed")        
                if self.edge_matrix[vertex_start_idx][vertex_end_idx].vertex_end_idx != vertex_end_idx:
                    rospy.logerr("edge index end test failed")  

    def get_edges_out(self,vertex_idx):
        return self.edge_matrix[vertex_idx]

    def plot_world(self, ax, target_belief):
        rospy.loginfo("plotting world")        
        num_nodes = len(self.vertices)

        # plot possible edges
        for vertex_start_idx in xrange(num_nodes):
            for vertex_end_idx in xrange(num_nodes):
                if self.edge_matrix[vertex_start_idx][vertex_end_idx].potentially_exists:
                    vertex_start = self.vertices[vertex_start_idx]
                    vertex_end = self.vertices[vertex_end_idx]
                    ax.plot([vertex_start.position.x, vertex_end.position.x],[vertex_start.position.y, vertex_end.position.y],':k', zorder=1)

        # plot actual edges
        for vertex_start_idx in xrange(num_nodes):
            for vertex_end_idx in xrange(num_nodes):
                if self.edge_matrix[vertex_start_idx][vertex_end_idx].exists:
                    vertex_start = self.vertices[vertex_start_idx]
                    vertex_end = self.vertices[vertex_end_idx]
                    ax.plot([vertex_start.position.x, vertex_end.position.x],[vertex_start.position.y, vertex_end.position.y],'-r', zorder=10)

        # plot vertices
        
        xs = []
        ys = []
        size_list = []
        for vertex_idx in xrange(num_nodes):
            xs.append(self.vertices[vertex_idx].position.x)
            ys.append(self.vertices[vertex_idx].position.y)
            p = target_belief.prob_dist[vertex_idx]
            sp = 2+10*p
            size_list.append(sp)
        #ax.scatter(xs, ys, s=5, zorder=20)

        # print(size_list)
        self.h_scatter_plot = ax.scatter(xs, ys, s=size_list, zorder=20)

        # Plot goal location as blue star
        pos_target = self.vertices[self.vertex_target_idx].position
        ax.plot(pos_target.x, pos_target.y, 'b*', markersize=20, zorder=10)
        

        # labels, axis etc
        ax.set_xlabel('x')
        ax.set_ylabel('y')
        ax.set_xlim(0,self.config["environment_size"][0])
        ax.set_ylim(0,self.config["environment_size"][1])
        ax.grid(True)
        ax.set_aspect('equal', 'box')

    def plot_world_update(self, ax, target_belief):

        num_nodes = len(self.vertices)
        size_list = []
        colors_list = []
        max_p = 0
        for vertex_idx in xrange(num_nodes):
            p = target_belief.prob_dist[vertex_idx]
            if p >= max_p:
                max_p = p

        for vertex_idx in xrange(num_nodes):
            p = target_belief.prob_dist[vertex_idx]
            sp = 1+100*(p/max_p)
            size_list.append(sp)

            p /= max_p
            c = [0,p,1-p]
            colors_list.append(c)

        # size_list_round = [round(p, 1) for p in size_list]
        # print(size_list_round)
        self.h_scatter_plot.set_sizes(size_list)
        self.h_scatter_plot.set_color(colors_list)

