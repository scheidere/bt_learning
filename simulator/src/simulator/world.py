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

from sensor_model import SensorModel
from distance import distance

'''
moved to separate file
def distance(vertex_start, vertex_end):
    # Euclidean distance, for now
    #return ( (vertex_start.position.x-vertex_end.position.x)**2 + (vertex_start.position.y-vertex_end.position.y)**2 + (vertex_start.position.z-vertex_end.position.z)**2)**0.5
    x = (vertex_start.position.x-vertex_end.position.x)
    y = (vertex_start.position.y-vertex_end.position.y)
    z = (vertex_start.position.z-vertex_end.position.z)
    return sqrt( x*x + y*y + z*z )
'''

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

    CLASS_NONTARGET = 0
    CLASS_WILDLIFE = 1
    CLASS_MINE = 2
    CLASS_BENIGN = 3

    def __init__(self, config):

        # Create a world
        self.config = config
        self.surface_level = 0

    def init_world(self, seed1, do_test=True):
        random.seed(seed1) # for repeatable trials
        self.init_world_once(do_test)
        while not self.is_connected():
            print("World graph is disconnected. Reinitializing...")
            self.init_world_once(do_test)


    def init_world_once(self, do_test=True):
        # create a blank world, PRM style
        num_nodes = self.config["num_nodes"]
        connection_radius = self.config["connection_radius"]
        environment_size = self.config["environment_size"]
        self.sensor_range = self.config["sensor_range"]

        # vertices
        self.vertices_surface = []
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
                    self.vertices_surface.append(True)
                else:
                    self.vertices_surface.append(False)


        # edges, stored as a matrix indexed as [vertex_start, vertex_end]
        self.num_nodes = len(self.vertices) #doubled the input num_nodes in creating two layers of vertices instead of one
        self.edge_matrix = [None] * self.num_nodes   
        self.edge_adjacency_idx_lists = [None] * self.num_nodes  
        self.edge_adjacency_edge_lists = [None] * self.num_nodes   
        for vertex_start_idx in xrange(self.num_nodes):
            self.edge_matrix[vertex_start_idx] = [None] * self.num_nodes
            self.edge_adjacency_idx_lists[vertex_start_idx] = []
            self.edge_adjacency_edge_lists[vertex_start_idx] = []
            for vertex_end_idx in xrange(self.num_nodes):

                cost = distance(self.vertices[vertex_start_idx], self.vertices[vertex_end_idx])
                if vertex_start_idx != vertex_end_idx and cost <= connection_radius and not (self.vertices_surface[vertex_start_idx] and self.vertices_surface[vertex_end_idx]):  
                    exists = True 
                else:
                    exists = False
                edge = Edge(vertex_start_idx, vertex_end_idx, cost, exists)
                self.edge_matrix[vertex_start_idx][vertex_end_idx] = edge

                if exists:
                    self.edge_adjacency_idx_lists[vertex_start_idx].append( vertex_end_idx )
                    self.edge_adjacency_edge_lists[vertex_start_idx].append( edge )

        if do_test:
            self.test_indices()

        #self.vertex_target_idx = self.create_target_idx() #single robot 

        # Define prior distribution
        self.num_classes = self.config["num_classes"]
        self.prob_of_class0 = self.config["prob_of_class0"]
        self.prob_of_other_classes = (1 - self.prob_of_class0)/(self.num_classes - 1)
        self.prior = np.zeros(self.num_classes) #p_y0, p_y1, ...
        for i in range(self.num_classes):
            if i == 0:
                self.prior[i] = self.prob_of_class0 
            else:
                self.prior[i] = self.prob_of_other_classes


        self.randomize_targets() 
        self.inclusive_randomize_targets() # ensure one of each target type

        # Define single random drop-off location (on surface) per world
        temp = random.randint(0,len(self.vertices)-1)
        while self.vertices_surface[temp] != True:
            temp = random.randint(0,len(self.vertices)-1)
        self.drop_off_idx = temp      

        '''
        # Set all class 2 vertices to is_armed = True
        self.is_armed_array = np.zeros(self.num_nodes, dtype=bool) #default, False for all
        for v in xrange(len(self.classes_y)):
            if self.classes_y[v] == 2: #it is a mine
                self.is_armed_array[v] = True
        '''      

        '''
        # Vertex classes
        # Each vertex has a number between 0 and n, which represents the class of the vertex
        num_v_y0 = int(self.num_nodes*self.prob_of_class0)
        num_v_other = self.num_nodes - num_v_y0
        num_v_each = num_v_other/(self.num_classes-1)
        classes_y = []
        classes_y.extend([0]*num_v_y0) # add the non-target vertex classes
        for i in range(1,self.num_classes):
            classes_y.extend([i]*num_v_each) # add the target vertex classes

        # G round truth vertex classes
        random.shuffle(classes_y) #shuffle the list to randomize location of targets
        '''

        self.comms_range = self.config["comms_range"]

        self.vertices_in_comms_range = self.generateCommsRangeVertices()

        # Setup sensor model
        self.sensor_model = SensorModel(self.config,self.num_nodes,self)

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

    def is_open_set_empty(self, open_set):
        for i in open_set:
            if i == True:
                return False
        return True

    def is_connected(self):
        num_vertices = len(self.vertices)

        open_set = [False] * num_vertices
        closed_set = [False] *num_vertices

        open_set[0] = True # Adding a vertex to open set, as our starting point

        while not self.is_open_set_empty(open_set):


            # find a vertex in open_set
            v_current = open_set.index(True)

            # remove it from the open set
            open_set[v_current] = False

            # add it to the closed set
            closed_set[v_current] = True

            # get the set of neighbours
            neighbours = self.edge_adjacency_edge_lists[v_current]

            # expand neighbouring nodes
            for e in neighbours:
                v_next = e.vertex_end_idx
                if not closed_set[v_next] == True:
                    # If not in closed set, add to open set
                    open_set[v_next] = True

        if False in closed_set: # you haven't visited at least one vertex
            return False

        return True

    def target_inclusion_test(self):
        target_inclusion_test_list = np.zeros(self.num_classes - 1) #minus 1 for the void of target class (i.e. 0)
        for vertex_class in self.classes_y:
            if vertex_class == 1:
                target_inclusion_test_list[0] = 1
            elif vertex_class == 2:
                target_inclusion_test_list[1] = 1
            elif vertex_class == 3:
                target_inclusion_test_list[2] = 1

        if 0 in target_inclusion_test_list: #one target type not included, so we should randomize again
            return False

        return True


    def randomize_targets(self):
        # Vertex classes - ground truth
        self.classes_y = np.array([]) # 0 - not target, 1 - wildlife/report, 2 - mine/disarm, 3 - benign/move
        for i in range(self.num_nodes):
            self.classes_y = np.append(self.classes_y,np.random.choice(a= len(self.prior),p = self.prior))
        #print("classes_y",self.classes_y.shape) 
        #self.original_classes = self.classes_y

    def inclusive_randomize_targets(self):
        while not self.target_inclusion_test():
            self.randomize_targets()



    def disarm_target(self, vertex_idx, scorer):
        if self.classes_y[vertex_idx] == World.CLASS_MINE:
            self.classes_y[vertex_idx] = World.CLASS_NONTARGET # Now is class 0 because target removed
            scorer.action_reward(vertex_idx, World.CLASS_MINE) # Generate score #use reward_action_to_target from scorer
            return True
        return False

    def pickup_target(self, vertex_idx, scorer):
        if self.classes_y[vertex_idx] == World.CLASS_BENIGN:
            self.classes_y[vertex_idx] = World.CLASS_NONTARGET # Now is class 0 because target removed
            scorer.action_reward(vertex_idx, World.CLASS_BENIGN) # Generate score
            return True
        return False

    def dropoff_target(self, vertex_idx, scorer, state):
        if self.drop_off_idx == vertex_idx: # Now is class 0 because target removed
            scorer.dropoff_reward(state.picked_up_target_count) # Generate score
            return True
        return False

    def report_target(self, vertex_idx, scorer, is_at_surface, is_in_comms): # Check with Graeme DONE
        #if classes_y[vertex_idx] == World.CLASS_WILDLIFE:
        response = scorer.submit_target(vertex_idx, World.CLASS_WILDLIFE, is_at_surface, is_in_comms) # Generate score
        print('reported something', response)
        if response == scorer.RESPONSE_CORRECT:
            print('report is correct')
            self.classes_y[vertex_idx] = World.CLASS_NONTARGET # Now is class 0 because target removed

        return response

    def generateCommsRangeVertices(self):
        idx_list = []
        for vertex in self.vertices:
            if distance_to_base(vertex) < self.comms_range and vertex.position.z > self.surface_level - 0.0001:
                idx_list.append(vertex.vertex_idx)

        return idx_list #list of indices of vertices in comms range (and at surface)


    def robot_env_observations(self, vertex_robot_idx): 
        #use for single target case
        #likelihoods = self.sensor_model.all_likelihoods(vertex_robot_idx, self.vertex_target_idx)
        #return a single observation, z based on the probability distribution
        #return np.random.choice(a=len(self.vertices)+1, p=likelihoods)

        v_in_range = np.array([],dtype=int)
        z_array = np.array([],dtype=int)
        for v in xrange(self.num_nodes):
            if self.sensor_model.distances[vertex_robot_idx][v] < self.sensor_range:
                likelihoods = self.sensor_model.all_likelihoods(self.classes_y[v])
                v_in_range = np.append(v_in_range,v)
                z_array = np.append(z_array, np.random.choice(a=self.num_classes,p=likelihoods))

        return z_array, v_in_range


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

                if self.edge_matrix[vertex_start_idx][vertex_end_idx].exists:
                    if vertex_end_idx not in self.edge_adjacency_idx_lists[vertex_start_idx]:
                        rospy.logerr("edge_adjacency_idx_lists test failed")

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
            #p = target_belief.prob_dist[vertex_idx] # Single target case
            #sp = 2+10*p
            #size_list.append(sp)
        #ax.scatter(xs, ys, s=5, zorder=20)

        # print(size_list)
        self.h_scatter_plot = ax.scatter(xs, ys, s=size_list, zorder=20)

        '''
        # Plot goal location as blue star
        pos_target = self.vertices[self.vertex_target_idx].position
        ax.plot(pos_target.x, pos_target.y, 'b*', markersize=20, zorder=10)
        '''

        # Plot targets as blue stars
        for v in xrange(len(self.classes_y)):
            if self.classes_y[v]: #it's not 0, hence is a target of some kind (1,2,or 3)
                pos_target = self.vertices[v].position
                ax.plot(pos_target.x, pos_target.y, 'b*', markersize=20, zorder=10)
        

        # labels, axis etc
        ax.set_xlabel('x')
        ax.set_ylabel('y')
        ax.set_xlim(0,self.config["environment_size"][0])
        ax.set_ylim(0,self.config["environment_size"][1])
        ax.grid(True)
        ax.set_aspect('equal', 'box')

    def plot_world_update(self, ax, target_belief):

        # Check with Graeme: This is for size and color changes, and is not updated to account for prob_dist[v] being a list
        # Should I use this for anything?

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

