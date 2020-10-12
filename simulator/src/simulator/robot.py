#!/usr/bin/env python

import rospy
import rospkg
import sys
import yaml
#from msg import RequestObservations
#from simulator.msg import SendObservations
#from simmulator.msg import RobotPosition
from geometry_msgs.msg import Point
#from simmulator.srv import GroundTruthObservation
#from simmulator.msg import EdgeObservation
#from simmulator.msg import ScoringStatistics

import matplotlib.pyplot as plt

import world
from world import World
from world import distance


from scorer import Scorer

import copy

import planners
#import communication_planner

import random

from bt_interface import *
from behavior_tree.behavior_tree import *
from cfg import CFG, Word, Character, createWord

import numpy as np

import time



class State():
    def __init__(self, vertex_idx):
        # describes a point along an edge
        # if two indices are equal then is at that edge
        self.vertex_from_idx = vertex_idx
        self.vertex_to_idx = vertex_idx
        self.fraction_along_edge = 0
        self.battery_life_count = 0
        self.picked_up_target_count = 0

    def get_position(self, world):
        vertex_start = world.vertices[self.vertex_from_idx]
        vertex_end = world.vertices[self.vertex_to_idx]
        x = vertex_start.position.x + self.fraction_along_edge*(vertex_end.position.x-vertex_start.position.x)
        y = vertex_start.position.y + self.fraction_along_edge*(vertex_end.position.y-vertex_start.position.y)
        z = vertex_start.position.z + self.fraction_along_edge*(vertex_end.position.z-vertex_start.position.z)
        return Point(x,y,z)

    def plot(self, ax, world):

        position = self.get_position(world)
        # rospy.loginfo("current location: " + str(location))
        h, = ax.plot(position.x, position.y, 'g*', markersize=15, zorder=100)
        return h

    def plot_update(self, h, world):
        position = self.get_position(world)
        h.set_xdata(position.x)
        h.set_ydata(position.y)

    def at_vertex(self):
        return self.vertex_from_idx == self.vertex_to_idx

    # Determine if robot is at the surface or not 
    def at_surface(self, world):
        position = self.get_position(world)
        at_surface = world.surface_level
        if position.z > at_surface - 0.0001:
            return True
        else:
            return False

    # Determine if robot is at a vertex in comms range
    def in_comms(self, world):
        if self.at_vertex():
            if self.vertex_from_idx in world.vertices_in_comms_range:
                return True
            else:
                return False
        else:
            return False

    def battery_life_update(self, world):
        # Battery_low criteria (10 without resurface - dead; 5+ after Full - low battery)
        if self.at_surface(world):
            self.battery_life_count = 0
        else:
            self.battery_life_count += 1


    def battery_low_check(self, config):
        return self.battery_life_count >= config['battery_low_threshold']

    def battery_dead_check(self, config):
        return self.battery_life_count >= config['battery_dead_threshold']





class TargetBelief():
    #prob distribution over the vertices
    def __init__(self, num_vertices, sensor_model, world):
        #self.world = world # could do it this way too

        self.num_vertices = num_vertices

        self.sensor_model = sensor_model

        self.world = world

        self.config = self.world.config

        self.confidence_threshold = self.config["confidence_threshold"]

        self.init_prior(world)

    '''
    def init_prior(self):
        ## P(Y)
        p = 1.0/self.num_vertices
        self.prob_dist = np.full(self.num_vertices, p)
        # this is prob dist for y where y is vertices - we dont have this now
        # we now have prob dist of classes at each vertex
        # need to use prior defined in the paper, and world class, need to make multiple copies (num_vertices copies copy.copy)
    '''

    def init_prior(self, world):
        #P(Y); one dist P(Y^v) each vertex v wrt all classes
        self.prob_dist = np.zeros((self.num_vertices,self.world.num_classes))
        for v in xrange(self.num_vertices):
            self.prob_dist[v] = copy.copy(self.world.prior)

    def likelihood(self, x, y, z):
        '''
        likelihoods = self.sensor_model.all_likelihoods(x, y) 
        return likelihoods[z]
        '''
        pass
    '''
    def bayes_update(self, x, z):
        ## P(Y|Z)

        for y in xrange(self.num_vertices):
            self.prob_dist[y] *= self.likelihood(x, y, z)
            
        total = sum(self.prob_dist)

        # Normalize
        self.prob_dist /= total
    '''
    def bayes_update(self, x, z_array, v_in_range):
        ## P(Y|Z)

        for i in xrange(len(v_in_range)):
            for y in xrange(self.world.num_classes):
                self.prob_dist[v_in_range[i]][y] *= self.sensor_model.compute_single_likelihood(y,z_array[i]) 

            # Normalize over y
            total = sum(self.prob_dist[v_in_range[i]])
            self.prob_dist[v_in_range[i]] /= total


    def found_false_update(self, vertex_false_idx):
        # You now know that the target is not where you chose, so prob = 0 there
        old_p = self.prob_dist[vertex_false_idx]
        self.prob_dist[vertex_false_idx] = 0

        # Get new total
        # Assume was normalised before...
        total = 1.0 - old_p

        # Normalize to accomodate change
        self.prob_dist /= total

    def generateTargetBeliefIdxClass(self): #generateRobotBeliefIdx(self):
        # Robot chooses best based on the probability that a vertex is the target's location
        '''
        idx_with_max_p = None
        for i in xrange(len(self.prob_dist)):
            p = self.prob_dist[i]
            if idx_with_max_p == None:
                max_p = p
                idx_with_max_p = i
            elif max_p < p:
                max_p = p
                idx_with_max_p = i

        return idx_with_max_p
        '''
        # This returns the location of first occurence of max_p
        # We could do distance based - i.e. closest likely target
        ## This method has an issue, would likely almost always choose non-target because class 0 starts with higher probability
        ##max_p_row, max_p_col = np.unravel_index(self.prob_dist.argmax(),self.prob_dist.shape)  #row,col
        ##return max_p_row, max_p_col


        # Check with Graeme DONE
        first = True
        for v in xrange(self.num_vertices):
            new_col = np.argmax(self.prob_dist[v][1:]) + 1 # Don't consider first prob, because that is class 0, non-target probability
            temp_max = self.prob_dist[v][new_col] #np.max(self.prob_dist[v][1:])
            if first:
                row_with_max_p, col_with_max_p = v, new_col
                max_p = temp_max
                first = False
            elif temp_max > max_p:
                row_with_max_p, col_with_max_p = v, new_col
                max_p = temp_max

        return row_with_max_p, col_with_max_p #v,y; location, class

        #return np.argmax(self.prob_dist) #this was all that was here for the single target implementation


    '''
    def target_found_50(self):
        for p in self.prob_dist:
            if p > 0.5:
                return True

        return False

    def target_found_70(self):
        for p in self.prob_dist:
            if p > 0.7:
                return True

        return False

    def target_found_90(self):
        for p in self.prob_dist:
            if p > 0.9:
                return True

        return False
    '''
    def class_y_found(self, y):
        for v in xrange(self.num_vertices):
            if self.prob_dist[v][y] > self.confidence_threshold:
                return True
        return False

    def class_y_current_vertex(self, x, y):
        if self.prob_dist[x][y] > self.confidence_threshold:
            return True
        return False

    def found_likely_target(self):
        for y in xrange(1,self.world.num_classes):
            if self.class_y_found(y):
                return True
        return False

    def update_loc_class_0(self, vertex_idx):
        if vertex_idx is not None: # Check with Graeme
            self.prob_dist[vertex_idx][0] = 1
            self.prob_dist[vertex_idx][1:] = 0

    def update_loc_not_class_y(self, vertex_idx, y):
        print('vertex_idx', vertex_idx)
        print('y',y)
        if vertex_idx is not None: # Check with Graeme
            self.prob_dist[vertex_idx][y] = 0
            total = sum(self.prob_dist[vertex_idx])
            self.prob_dist[vertex_idx] /= total

    def find_nearest_target(self, x, y): # Check with Graeme DONE
        # Find nearest location where the robot believes there to be a target of class y, given the robot is at x
        distance_to_nearest_target = None
        found_new_target = False
        nearest_target_idx = None
        for v in xrange(self.num_vertices): #num_vertices
            # Check if class y target is at v (with prob > 0.9)
            if self.prob_dist[v][y] > self.confidence_threshold:
                found_new_target = True
                new_dist = self.sensor_model.distances[x][v] # Calc dist from robot to class y target found

            if found_new_target:
                if distance_to_nearest_target == None: # if this is first found target, save it
                    distance_to_nearest_target = new_dist
                    nearest_target_idx = v
                elif distance_to_nearest_target > new_dist: # if you find another target that is closer, replace
                    distance_to_nearest_target = new_dist
                    nearest_target_idx = v
                found_new_target = False # reset

        return nearest_target_idx # returns None if a target of class y never found with prob > 0.9

    def get_all_detections(self): # Check with Graeme DONE
        detection_list = []
        for v in xrange(self.num_vertices):
            for y in xrange(1,self.world.num_classes):
                if self.prob_dist[v][y] > self.confidence_threshold:
                    detection_list.append([v,y])

        return detection_list





class Robot():

    PLANNER_TYPE_STOP = 0 # only used if the BT says to do nothing
    PLANNER_TYPE_RANDOM = 1
    PLANNER_TYPE_SHORTEST = 2
    PLANNER_TYPE_COMMSRANGE = 3  #need to use this below, want to test original shortest path planner first
    PLANNER_TYPE_PEAKBELIEF = 4
    PLANNER_TYPE_RESURFACE = 5
    PLANNER_TYPE_DROPOFF = 6
    PLANNER_TYPE_DISARM = 7
    PLANNER_TYPE_PICKUP = 8
    PLANNER_TYPE_COVERAGE = 9

    def __init__(self, config, robot_id, num_robots, seed, bt, max_iterations, world):

        self.bt = bt
        self.config = config
        self.robot_id = robot_id
        self.speed = config["robot_speed"]
        self.planner_type = Robot.PLANNER_TYPE_RANDOM
        self.has_reported = False
        self.belief_distance = 500
        self.robot_belief_idx = None #issue solved: used before do_iteration called in robot controller
        #self.communicate_observations = communicate_observations

        ##self.nearest_mine_idx = None

        '''
        self.scoring_statistics = ScoringStatistics()
        self.scoring_statistics.robot_id = robot_id
        self.scoring_statistics.goals_reached = 0
        self.scoring_statistics.count_iterations = 0
        self.scoring_statistics.count_vertices = 0
        #self.scoring_statistics.count_communication_transmit = 0
        '''

        
        # Setup publishers        
        #self.publisher_observation_request = rospy.Publisher('/request_observations', RequestObservations, queue_size=10)
        #self.publisher_observation_send = rospy.Publisher('/send_observations', SendObservations, queue_size=10)
        #self.publisher_position = rospy.Publisher('/position', RobotPosition, queue_size=10)
        #self.publisher_statistics = rospy.Publisher('/statistics', ScoringStatistics, queue_size=10)

        # Setup navigation roadmap graph
        # rospy.loginfo("robot getting base world from ground truth")
        # print("Setup navigation roadmap")
        # self.known_world = World(config)
        # do_test = False # don't error check graph
        # self.known_world.init_world(seed, do_test)
        self.known_world = world

        self.is_armed_array = np.ones(self.known_world.num_nodes, dtype=bool) # Check with Graeme DONE

        # Setup a set of random numbers
        # print("Setup set of random numbers")
        self.setup_random_numbers(seed)

        # Setup state belief
        # print("Setup state belief")
        self.state = []
        randomize_start = rospy.get_param('~randomize_start')
        if randomize_start: # want this when training
            random_start_vertex = self.get_next_random_number()
        else: # want this when plotting results (box plot stuff, plot_results.launch)
            random_start_vertex = 0 
        current_state = State(random_start_vertex) # start at a random vertex
        self.state = current_state

        '''
        # Setup listeners
        rospy.Subscriber('/request_observations', RequestObservations, self.callback_request)
        rospy.Subscriber('/send_observations', SendObservations, self.callback_receive)
        rospy.Subscriber('/position', RobotPosition, self.receive_position)
        '''

        #print(bt)
        # Set up BT interface
        self.bt_interface = BT_Interface(bt)

        num_vertices = len(self.known_world.vertices)

        # Initialize visit_tracker for coverage planner
        self.visit_tracker = np.zeros(num_vertices)
        print('VISIT TRACKER: ', self.visit_tracker)

        # create sensor model
        # moved within world instead
        # self.sensor_model = SensorModel(config,num_vertices,self.known_world)

        # self.known_world.set_sensor_model(self.sensor_model)

        # Generate belief of where target could be
        self.target_belief = TargetBelief(num_vertices, self.known_world.sensor_model, self.known_world)

        # Set up Scorer
        self.basestation_scorer = Scorer(self.known_world, max_iterations)

        self.drop_off_idx = self.known_world.drop_off_idx

        # plot
        # print("plot")
        self.h_state = None
        self.robot_plot = config["robot_plot"]
        if self.robot_plot:
            rospy.loginfo("plotting robot world")
            self.plot_robot()

        self.armed_mine_found_flag = False
        self.mine_disarmed_flag = False
        # print("finished init")

    def setup_random_numbers(self, seed):
        '''
        # sets up a persistent set of numbers
        # for repeatable tests
        n = 10000
        self.random_number_list = np.zeros(n, dtype=np.int32)

        random.seed(seed)
        
        for i in xrange(n):
            random_number = random.randint(0,len(self.known_world.vertices)-1)
            self.random_number_list[i] = random_number

        self.random_number_list_index = 0
        '''
        pass

    def get_next_random_number(self):
        '''
        number = self.random_number_list[self.random_number_list_index]
        self.random_number_list_index += 1
        if self.random_number_list_index >= len(self.random_number_list):
            self.random_number_list_index = 0
        return number
        '''
        return random.randint(0,len(self.known_world.vertices)-1)



    def do_iteration(self, num_iterations):
        #rospy.loginfo("robot do_iteration")

        #self.scoring_statistics.count_iterations += 1


        # Printing for debugging
        #r_prob_dist = [round(p, 3) for p in self.target_belief.prob_dist]
        #print("prob_dist:",r_prob_dist)
        #print('goal:',self.known_world.vertex_target_idx)
        #position_goal = self.known_world.vertices[self.known_world.vertex_target_idx].position
        #print('position of goal:', position_goal.x,position_goal.y)
        #print('prob at goal:',r_prob_dist[self.known_world.vertex_target_idx])

        moved = False

        distance_to_travel = self.speed
        # print("dist to travel", distance_to_travel)
        while distance_to_travel > 0:
            self.bt_interface.tick_bt()

            active_actions = self.bt_interface.getActiveActions()
            #print("+++++++++++++++++++++++++active_actions", active_actions)

            # Stop episode if battery is dead
            # Battery_low criteria (10 without resurface - dead; 5+ after Full - low battery)
            if self.state.battery_dead_check(self.config):
                self.condition_updates()
                self.set_action_status()
                print("battery is dead")
                break

            # print("position: ")
            # pos = self.state.get_position(self.known_world)
            # print(pos.x, pos.y, pos.z)
            
            # Plan
            # print("plan")
            action_sequence = None  
            ###print("self.state.at_vertex() 1",self.state.at_vertex())        
            if self.state.at_vertex():
                action_sequence = self.plan()
                #if action_sequence == None: #goal vertex is None, so path is empty
                    #print("action sequence is None about to break")
                    #break

            # Move
            # print("move")
            [new_vertex, distance_traveled, no_move] = self.move(action_sequence, distance_to_travel)

            if not no_move:
                moved = True
            if no_move or distance_traveled == 0:
                distance_to_travel = 0
            else:
                distance_to_travel -= distance_traveled

            self.state.battery_life_update(self.known_world)
            x = self.state.vertex_from_idx

            # Observe
            if new_vertex:
                # print("observe")

                #x = self.state.vertex_from_idx
                z_array, v_in_range = self.observe(x)
                self.target_belief.bayes_update(x,z_array,v_in_range)

                # default is that robot does not know answer
                #robot_has_ans = False # maybe relates to BT, BT can learn this (report action node)

            ###print("self.state.at_vertex() 2",self.state.at_vertex())
            if self.state.at_vertex():
                # Choose vertex idx to report as belief of target location based on prob dist
                #self.robot_belief_idx = self.target_belief.generateRobotBeliefIdx() # fix this function, then change name of it and variable
                self.nearest_wildlife_idx = self.target_belief.find_nearest_target(x, World.CLASS_WILDLIFE)
                # print('self.nearest_wildlife_idx',self.nearest_wildlife_idx)

                # Check if at surface, either True or False
                is_at_surface = self.state.at_surface(self.known_world)

                # Check if in comms range, True or False
                is_in_comms = self.state.in_comms(self.known_world)

                # If the robot has reported something
                ## Before report was an action ## response = self.basestation_scorer.submit_target(robot_belief_idx, x, is_at_surface, is_in_comms, num_iterations)
                #response = self.report_target_belief(self.nearest_wildlife_idx, World.CLASS_WILDLIFE, is_at_surface, is_in_comms, num_iterations)
                response = self.report_target_belief(self.nearest_wildlife_idx, is_at_surface, is_in_comms) #report and associated reward, if any, done here # Check with Graeme DONE
                #print("report should happen here")

                # Update robot belief based on reporting reponse
                if response == self.basestation_scorer.RESPONSE_CORRECT:
                    self.target_belief.update_loc_class_0(self.nearest_wildlife_idx)
                elif response == self.basestation_scorer.RESPONSE_FALSE and self.nearest_wildlife_idx: 
                    self.target_belief.update_loc_not_class_y(self.nearest_wildlife_idx , World.CLASS_WILDLIFE)


                '''
                # Don't need this for multi-target because prob_dist different
                if response == self.basestation_scorer.RESPONSE_FALSE:
                    self.target_belief.found_false_update(self.robot_belief_idx)
                '''                

                # Update robot belief based on results of actions
                if self.planner_type == Robot.PLANNER_TYPE_PICKUP and x == self.nearest_benign_idx:
                    successful_pickup = self.known_world.pickup_target(x,self.basestation_scorer)
                    if successful_pickup:
                        self.state.picked_up_target_count += 1
                        self.target_belief.update_loc_class_0(self.nearest_benign_idx)
                    else:
                        self.target_belief.update_loc_not_class_y(self.nearest_benign_idx, World.CLASS_BENIGN)

                if self.planner_type == Robot.PLANNER_TYPE_DROPOFF and x == self.known_world.drop_off_idx:
                    successful_dropoff = self.known_world.dropoff_target(x, self.basestation_scorer, self.state)
                    if successful_dropoff:
                        self.state.picked_up_target_count = 0 # all dropped off

                elif self.planner_type == Robot.PLANNER_TYPE_DISARM and x == self.nearest_mine_idx: # Check with Graeme DONE
                    successful_disarm = self.known_world.disarm_target(x,self.basestation_scorer)
                    if successful_disarm:
                        self.target_belief.update_loc_class_0(self.nearest_mine_idx)
                        self.is_armed_array[self.nearest_mine_idx] = False # Check with Graeme DONE
                        self.mine_disarmed_flag = True
                    else:
                        self.target_belief.update_loc_not_class_y(self.nearest_mine_idx, World.CLASS_MINE)

                # Reward for correct target detections
                detection_list = self.target_belief.get_all_detections() 
                self.basestation_scorer.detection_reward(detection_list) #give scorer +1 for all newly detected vertices in detection_list if detection is correct

                # Update visit tracker
                #if self.planner_type == Robot.PLANNER_TYPE_COVERAGE:
                self.visit_tracker[x] = 1 # Update any vertex the robot has been to from 0 to 1 in the tracker
            
            # Condition checks
            self.condition_updates()

            # Set status of active actions (running or failure, currently not considering success)
            # if a plan is executing, it is running, otherwise it is a failure (even though the action is 'active')
            self.set_action_status()

        # plot
        if self.robot_plot:
            #rospy.loginfo("plotting robot world")
            self.plot_robot()
            rospy.sleep(0.1)

        return not moved

    def condition_updates(self):

        # Set condition statuses so they can be updated each iteration
        # and used to choose actions accordingly

        is_at_surface = self.state.at_surface(self.known_world)

        is_in_comms = self.state.in_comms(self.known_world)

        needs_to_surface = self.state.battery_low_check(self.config)

        '''
        found_class_y_90_array = np.zeros()
        for y in xrange(1,self.known_world.num_classes): #dont want True for class 0 because that isn't a target
            np.append(found_class_y_90_array, self.target_belief.class_y_found_90(y))
            #self.bt_interface.setConditionStatus('class_'+y+'_found_90') #general version, instead of wildlife, mine, benign
        '''

        likely_target_found = self.target_belief.found_likely_target()

        wildlife_found = self.target_belief.class_y_found(World.CLASS_WILDLIFE)
        
        mine_found = self.target_belief.class_y_found(World.CLASS_MINE)

        #print('mine_found: ' + str(mine_found))
        self.nearest_mine_idx = self.target_belief.find_nearest_target(self.state.vertex_from_idx, World.CLASS_MINE)
        if self.nearest_mine_idx:
            is_armed = self.is_armed_array[self.nearest_mine_idx] #default is that they are always armed, unless they have been disarmed by robot
        else:
            is_armed = False
        #print('is_armed: ' + str(is_armed))

        if mine_found and is_armed:
            self.armed_mine_found_flag = True

        benign_object_found = self.target_belief.class_y_found(World.CLASS_BENIGN)

        if self.state.picked_up_target_count: # if this not 0, robot is carrying # Check with Graeme
            carrying_benign = True
        else:
            carrying_benign = False

        #target_found_50 = self.target_belief.target_found_50()
        #target_found_70 = self.target_belief.target_found_70()
        #target_found_90 = self.target_belief.target_found_90()


        self.bt_interface.setConditionStatus('at_surface', is_at_surface)

        self.bt_interface.setConditionStatus('in_comms', is_in_comms)

        self.bt_interface.setConditionStatus('battery_low', needs_to_surface) 

        self.bt_interface.setConditionStatus('likely_target_found', likely_target_found)

        self.bt_interface.setConditionStatus('wildlife_found', wildlife_found)

        self.bt_interface.setConditionStatus('mine_found', mine_found)

        self.bt_interface.setConditionStatus('is_armed', is_armed)

        self.bt_interface.setConditionStatus('benign_object_found', benign_object_found)

        self.bt_interface.setConditionStatus('carrying_benign',carrying_benign)

        #self.bt_interface.setConditionStatus('target_found_50', target_found_50)

        #self.bt_interface.setConditionStatus('target_found_70', target_found_70)

        #self.bt_interface.setConditionStatus('target_found_90', target_found_90)

        # ... more conditions

    def report_target_belief(self,target_belief_idx, is_at_surface, is_in_comms):
        active_actions = self.bt_interface.getActiveActions()
        #print(active_actions)
        #print("check if report is active action")
        #print("Is report in active_actions? ", 'report' in active_actions)
        #print("target_belief_idx: ", target_belief_idx)
        #print("active_actions", active_actions)
        if 'report' in active_actions and target_belief_idx is not None:
            #response = self.basestation_scorer.submit_target(robot_belief_idx, x, is_at_surface, is_in_comms, num_iterations)
            #response = self.basestation_scorer.submit_target(robot_belief_idx, robot_belief_y, is_at_surface, is_in_comms, num_iterations)
            #if response != self.basestation_scorer.RESPONSE_NONE:
            #print('report is active action')
            self.has_reported = True
            #return response
            response = self.known_world.report_target(target_belief_idx, self.basestation_scorer, is_at_surface, is_in_comms)
            return response
        return None


    def get_planner_type(self):
        active_actions = self.bt_interface.getActiveActions()
        #print(active_actions)

        if 'go_to_comms' in active_actions:
            self.planner_type = Robot.PLANNER_TYPE_COMMSRANGE

        elif 'resurface' in active_actions:
            self.planner_type = Robot.PLANNER_TYPE_RESURFACE

        elif 'go_to_likely_target' in active_actions:
            self.planner_type = Robot.PLANNER_TYPE_PEAKBELIEF

        elif 'coverage' in active_actions:
            self.planner_type = Robot.PLANNER_TYPE_COVERAGE

        elif 'take_to_drop_off' in active_actions:
            self.planner_type = Robot.PLANNER_TYPE_DROPOFF

        elif 'random_walk' in active_actions:
            self.planner_type = Robot.PLANNER_TYPE_RANDOM

        elif 'shortest_path' in active_actions:
            self.planner_type = Robot.PLANNER_TYPE_SHORTEST

        elif 'disarm' in active_actions:
            print('disarm is active')
            print('Current vertex (vertex_from_idx): ' + str(self.state.vertex_from_idx))
            print('Goal vertex (vertex_to_idx): ' + str(self.state.vertex_to_idx))
            #if self.nearest_mine_idx != None:
                #print('Closest mine (nearest_mine_idx): ' + str(self.nearest_mine_idx))
            #print('Actual target locations (mine = class 2): ')
            #print(self.known_world.classes_y)
            self.planner_type = Robot.PLANNER_TYPE_DISARM
        
        elif 'pick_up' in active_actions:
            self.planner_type = Robot.PLANNER_TYPE_PICKUP
    
        else:
            self.planner_type = Robot.PLANNER_TYPE_STOP
            # print("get_planner_type: No planner was picked")

        #print('planner type',self.planner_type)

        # ... more actions (planners)

    def set_action_status(self):
        active_actions = self.bt_interface.getActiveActions()

        for action in active_actions:
            if action == 'go_to_comms':
                if self.planner_type == Robot.PLANNER_TYPE_COMMSRANGE:
                    self.bt_interface.setActionStatusRunning(action)
                else:
                    self.bt_interface.setActionStatusSuccess(action)
            elif action == 'resurface':
                if self.planner_type == Robot.PLANNER_TYPE_RESURFACE:
                    self.bt_interface.setActionStatusRunning(action)
                else:
                    self.bt_interface.setActionStatusSuccess(action)
            elif action == 'go_to_likely_target':
                if self.planner_type == Robot.PLANNER_TYPE_PEAKBELIEF:
                    self.bt_interface.setActionStatusRunning(action)
                else:
                    self.bt_interface.setActionStatusSuccess(action)
            elif action == 'coverage':
                if self.planner_type == Robot.PLANNER_TYPE_COVERAGE:
                    self.bt_interface.setActionStatusRunning(action)
                else:
                    self.bt_interface.setActionStatusSuccess(action)
            elif action == 'take_to_drop_off':
                if self.planner_type == Robot.PLANNER_TYPE_DROPOFF:
                    self.bt_interface.setActionStatusRunning(action)
                else:
                    self.bt_interface.setActionStatusSuccess(action)
            elif action == 'random_walk':
                if self.planner_type == Robot.PLANNER_TYPE_RANDOM:
                    self.bt_interface.setActionStatusRunning(action)
                else:
                    self.bt_interface.setActionStatusSuccess(action)
            elif action == 'shortest_path':
                if self.planner_type == Robot.PLANNER_TYPE_SHORTEST:
                    self.bt_interface.setActionStatusRunning(action)
                else:
                    self.bt_interface.setActionStatusSuccess(action)
            elif action == 'disarm':
                if self.planner_type == Robot.PLANNER_TYPE_DISARM:
                    self.bt_interface.setActionStatusRunning(action)
                else:
                    self.bt_interface.setActionStatusSuccess(action)
            elif action == 'pick_up':
                if self.planner_type == Robot.PLANNER_TYPE_PICKUP:
                    self.bt_interface.setActionStatusRunning(action)
                else:
                    self.bt_interface.setActionStatusSuccess(action)
            elif action == 'report':
                    self.bt_interface.setActionStatusSuccess(action) #Check with Graeme
            else:
                print('action',action)
                print("set_action_status: Action does not exist")


    def plan(self, debug=False):
        #rospy.loginfo("Generating new plan")

        self.get_planner_type()

        if self.planner_type == Robot.PLANNER_TYPE_RANDOM:
            planner = planners.PlannerRandomWalk(self, self.known_world)
            action_sequence = planner.plan(debug)
            return action_sequence

        elif self.planner_type == Robot.PLANNER_TYPE_PEAKBELIEF:
            planner = planners.PlannerPeakBelief(self, self.known_world)

            planner.set_parameters(self.state.vertex_from_idx, self.target_belief)

            action_sequence = planner.plan(debug)
            return action_sequence

        elif self.planner_type == Robot.PLANNER_TYPE_COVERAGE:
            planner = planners.PlannerCoverage(self, self.known_world)

            planner.set_parameters(self.state.vertex_from_idx)

            action_sequence = planner.plan(debug)
            return action_sequence

        elif self.planner_type == Robot.PLANNER_TYPE_COMMSRANGE:
            planner = planners.PlannerCommsRange(self, self.known_world)

            planner.set_parameters(self.state.vertex_from_idx)

            action_sequence = planner.plan(debug)
            return action_sequence

        elif self.planner_type == Robot.PLANNER_TYPE_RESURFACE:
            planner = planners.PlannerResurface(self, self.known_world)

            planner.set_parameters(self.state.vertex_from_idx)

            action_sequence = planner.plan(debug)
            return action_sequence

        elif self.planner_type == Robot.PLANNER_TYPE_DROPOFF:
            planner = planners.PlannerShortestPath(self, self.known_world)

            planner.set_parameters(self.state.vertex_from_idx, self.drop_off_idx)

            action_sequence = planner.plan(debug)
            return action_sequence

        elif self.planner_type == Robot.PLANNER_TYPE_PICKUP: 
            planner = planners.PlannerShortestPath(self, self.known_world)

            self.nearest_benign_idx = self.target_belief.find_nearest_target(self.state.vertex_from_idx, World.CLASS_BENIGN)
            planner.set_parameters(self.state.vertex_from_idx, self.nearest_benign_idx) #update to nearest pick up loc

            action_sequence = planner.plan(debug)
            return action_sequence

        elif self.planner_type == Robot.PLANNER_TYPE_DISARM: 
            planner = planners.PlannerShortestPath(self, self.known_world)

            self.nearest_mine_idx = self.target_belief.find_nearest_target(self.state.vertex_from_idx, World.CLASS_MINE)
            planner.set_parameters(self.state.vertex_from_idx, self.nearest_mine_idx) # update to nearest mine loc
            ##planner.set_location_void_of_target() # Check with Graeme - why is this here? I can't find the function

            action_sequence = planner.plan(debug)
            return action_sequence

        elif self.planner_type == Robot.PLANNER_TYPE_SHORTEST:
            planner = planners.PlannerShortestPath(self, self.known_world)

            # set a random goal if not already set
            try:
                self.current_goal_vertex

            except AttributeError:
                self.current_goal_vertex = self.get_next_random_number()
                while self.known_world.vertices[self.current_goal_vertex].position.z > self.known_world.surface_level - 0.0001:
                    self.current_goal_vertex = self.get_next_random_number()

            # plan shortest path to goal
            planner.set_parameters(self.state.vertex_from_idx, self.current_goal_vertex)
            action_sequence = planner.plan(debug)

            # Check that path exists
            if not action_sequence:
                # select a new goal
                '''
                if self.state.vertex_to_idx == self.current_goal_vertex:
                    self.scoring_statistics.goals_reached += 1
                else:
                    self.scoring_statistics.goals_skipped += 1
                '''
                self.current_goal_vertex = self.get_next_random_number()
                while self.known_world.vertices[self.current_goal_vertex].position.z > self.known_world.surface_level - 0.0001:
                    self.current_goal_vertex = self.get_next_random_number()
                
                return None
            else:
                return action_sequence

    def observe(self,x):
        return self.known_world.robot_env_observations(x)
        # needs to return z_array, v_in_range

    def plot_robot(self):
        plt.rcParams['toolbar'] = 'None'
        fig = plt.figure(1)
        ax = plt.gca()

        if not self.h_state: #don't redraw if already drawn
            self.known_world.plot_world(ax,self.target_belief)
        '''
        # Check with Graeme: commented out because associated func not updated for prob_dist new size
        else:
            self.known_world.plot_world_update(ax,self.target_belief)
        '''

        if self.h_state != None:
            self.state.plot_update(self.h_state, self.known_world)
        else:
            self.h_state = self.state.plot(ax, self.known_world)

        # display the created plot
        plt.show(block=False)
        plt.draw()
        plt.pause(0.0001)

    def move(self, action_sequence, distance_to_travel):
        current_state = self.state
        new_vertex = False # publish true if a new vertex is reached
        no_move = False
        if not current_state.at_vertex():
            # move along edge
            edge_length = self.known_world.edge_matrix[current_state.vertex_from_idx][current_state.vertex_to_idx].cost
            prev_fraction_along_edge = current_state.fraction_along_edge
            current_state.fraction_along_edge += distance_to_travel/edge_length
            if current_state.fraction_along_edge >= 1.0:
                # reached the next vertex
                current_state.fraction_along_edge = 0.0
                current_state.vertex_from_idx = current_state.vertex_to_idx
                #self.scoring_statistics.count_vertices += 1
                new_vertex = True
                distance_traveled = (1-prev_fraction_along_edge)*edge_length
            else:
                distance_traveled = distance_to_travel
        elif action_sequence:
            action = action_sequence[0]
            while action == current_state.vertex_from_idx:
                # get the next action instead
                if len(action_sequence) >= 2:
                    action_sequence = action_sequence[1:]
                    action = action_sequence[0]
                else:
                    distance_traveled = 0
                    no_move = True
                    rospy.logwarn("robot is idle since plan gives current index")
                    break

            if not no_move:
                # start moving to next vertex
                current_state.vertex_to_idx = action
                edge_length = self.known_world.edge_matrix[current_state.vertex_from_idx][current_state.vertex_to_idx].cost
                if edge_length == 0:
                    current_state.fraction_along_edge = 1
                    distance_traveled = 0
                else:
                    current_state.fraction_along_edge = distance_to_travel/edge_length
                    if current_state.fraction_along_edge >= 1.0:
                        # reached the next vertex
                        current_state.fraction_along_edge = 0.0
                        current_state.vertex_from_idx = current_state.vertex_to_idx
                        #self.scoring_statistics.count_vertices += 1
                        new_vertex = True
                        distance_traveled = edge_length
                    else:
                        distance_traveled = distance_to_travel
        else:
            #rospy.logwarn("robot is idle since no plan given")
            distance_traveled = 0
            no_move = True

        return [new_vertex, distance_traveled, no_move]
    '''
    def publish_position(self):
        
        # robot id
        #int32 robot_id

        # position
        #geometry_msgs/Point position
        #int32 vertex_from_idx
        #int32 vertex_to_idx
        #float32 fraction_along_edge 

        # goal position
        #geometry_msgs/Point goal
        #int32 goal_idx
        

        if not self.real_robot:
            rospy.logerr("publish_position() should not be called for belief robots")
        else:
            position = self.state.get_position(self.known_world)
            vertex_from_idx = self.state.vertex_from_idx
            vertex_to_idx = self.state.vertex_to_idx
            fraction_along_edge = self.state.fraction_along_edge
            if self.current_goal_vertex:
                goal = self.known_world.vertices[self.current_goal_vertex].position
            else:
                goal = None
            self.publisher_position.publish(RobotPosition(robot_id=self.robot_id, position=position, vertex_from_idx=vertex_from_idx, 
                vertex_to_idx=vertex_to_idx, fraction_along_edge=fraction_along_edge, goal=goal, goal_idx=self.current_goal_vertex))

    '''

    def receive_position(self,msg):
        if msg.robot_id != self.robot_id:
            self.other_robots[msg.robot_id].set_position(msg)

    def set_position(self,msg):
        if self.real_robot:
            rospy.logerr("set_position() should not be called for real robots")
        else:
            self.state.vertex_from_idx = msg.vertex_from_idx
            self.state.vertex_to_idx = msg.vertex_to_idx
            self.state.fraction_along_edge = msg.fraction_along_edge
            self.current_goal_vertex = msg.goal_idx



class RobotController():
    def __init__(self, config, robot):
        self.config = config
        self.robot = robot

    def run(self):
        # Give an initial observation
        # print("Give an initial observation")
        x = self.robot.state.vertex_from_idx
        z_array, v_in_range = self.robot.observe(x)
        self.robot.target_belief.bayes_update(x,z_array,v_in_range)

        start_time = rospy.Time.now()
        num_iterations = 0

        no_move_count = 0

        # Continue indefinitely
        while not rospy.is_shutdown():   

            # print("iteration: " + str(num_iterations))
            no_move = self.robot.do_iteration(num_iterations)       
            num_iterations += 1
            # print(num_iterations)

            #belief_idx, belief_y = self.robot.target_belief.generateTargetBeliefIdxClass() #self.robot.target_belief.generateRobotBeliefIdx() 

            #self.robot.basestation_scorer.update_scorer(num_iterations, belief_idx) Check with Graeme DONE
            self.robot.basestation_scorer.update_scorer(num_iterations) # Now just updates self.finished to be True if done, does not change score

            if self.robot.basestation_scorer.finished: #checks if answer is correct, and if so stops sim
                break

            # Exit early if the robot hasn't moved in a while
            if no_move and num_iterations >= 10:
                no_move_count += 1
                #print("no_move_count", no_move_count)
                if no_move_count >= 10: 
                    print("Exiting due to robot not moving")
                    print("========Performing error check========")
                    print('self.robot.armed_mine_found_flag', self.robot.armed_mine_found_flag)
                    print('self.robot.mine_disarmed_flag', self.robot.mine_disarmed_flag)
                    if self.robot.armed_mine_found_flag and not self.robot.mine_disarmed_flag:
                        print('Armed mine found, but not disarmed')
                        print('+++++++++++++ERROR FOUND+++++++++++++')
                        #time.sleep(10000)
                    break
            else:
                no_move_count = 0


        return self.robot.basestation_scorer.score, self.robot.has_reported, self.robot.basestation_scorer.belief_distance






        '''
        # periodically publish statistics/scores etc
        #rospy.Timer(rospy.Duration(0.1), robot.publish_statistics_event, oneshot=False)

        # use_sleep = config["ground_truth_plot"] or config["robot_plot"] 

        iteration_rate = self.config["iteration_rate"]
        # rate = rospy.Rate( config["iteration_rate"] )
        start_time = rospy.Time.now()
        num_iterations = 0
        work_time = rospy.Time() # for cpu usage measurements

        # Continue indefinitely
        while not rospy.is_shutdown():   

            # use smart rate control 
            #print("use smart rate control")
            current_time = rospy.Time.now()   
            expected_num_iterations = ( current_time - start_time ).to_sec() * iteration_rate

            #print("num iterations", num_iterations)
            #print("exp num iterations", expected_num_iterations)
            if num_iterations <= expected_num_iterations:
                print("iteration: " + str(num_iterations))
                iteration_start_time = rospy.Time.now()
                self.robot.do_iteration(num_iterations)       
                num_iterations += 1   
                iteration_end_time = rospy.Time.now()
                work_time += iteration_end_time - iteration_start_time
                #print("num iterations <= expected num interations")
                if ( current_time - start_time ).to_sec() != 0: #don't divide by zero
                    current_rate = num_iterations / ( current_time - start_time ).to_sec()
                    cpu_usage = work_time.to_sec() / (current_time - start_time).to_sec()
                    
                    # if num_iterations <= expected_num_iterations * 0.9:                    
                    #     rospy.logerr("rate control lagging: num_iterations: " + str(num_iterations) + " expected: " + str(expected_num_iterations))
                    #     rospy.logwarn("current rate: " + str(current_rate) + " cpu usage: " + str(cpu_usage)) 

                self.robot.basestation_scorer.update_scorer(num_iterations)
                if self.robot.basestation_scorer.finished: #checks if answer is correct, and if so stops sim
                    break

        return self.robot.basestation_scorer.score
        '''
    




# Main function.
if __name__ == '__main__':
    
    # Initialise the node
    rospy.init_node('robot')
    # Get the config file etc
    rospack = rospkg.RosPack()
    filepath = rospack.get_path('simulator') + "/config/" + rospy.get_param('~config')
    with open(filepath, 'r') as stream:
        config = yaml.safe_load(stream)
    robot_id = rospy.get_param('~robot_id')
    num_robots = rospy.get_param('~num_robots')
    seed = rospy.get_param('~seed')

    try:

        # Setup a simple BT
        #character_list = [Character('?'),Character('('), Character('->'),Character('('),\
        #    Character('(target_found_90)'),Character('?'),Character('('),Character('(in_comms)'),\
        #    Character('[go_to_comms]'),Character(')'),Character('[report]'),Character(')'),Character('[go_to_belief]'),Character(')')]
        
        #test
        #character_list = [Character('->'),Character('('),Character('[report]'),Character('[go_to_belief]'),Character('[random_walk]'),Character(')')]

        #character_list = [Character('->'),Character('('),Character('[resurface]'),Character(')')]

        #character_list = [Character('?'),Character('('),Character('->'),Character('('),Character('(likely_target_found)'),Character('?'),Character('('),Character('(in_comms'),Character('[go_to_comms]'),Character(')'),Character('[report]'),Character(')'),Character('[random_walk]'),Character(')')]
        #character_list = [Character('?'),Character('('),Character('->'),Character('('),\
            #Character('(battery_low)'),Character('[resurface]'),Character(')'),Character('->'),Character('('),Character('[report]'),\
            #Character('[random_walk]'),Character(')'),Character(')')]
        '''
        character_list = [Character('?'),Character('('),\
            Character('->'),Character('('),\
            Character('(battery_low)'),Character('[resurface]'),Character(')'),\
            Character('->'),Character('('),\
            Character('(wildlife_found)'),Character('?'),Character('('),\
            Character('(in_comms)'),Character('[go_to_comms]'),Character(')'),Character('[report]'),Character(')'),\
            Character('[random_walk]'),\
            Character(')')]
        '''
        '''
        # our tree
        character_list = [Character('?'),Character('('),\
            Character('->'),Character('('),\
            Character('(battery_low)'),Character('[resurface]'),Character(')'),\
            Character('->'),Character('('),\
            Character('(wildlife_found)'),Character('?'),Character('('),\
            Character('(in_comms)'),Character('[go_to_comms]'),Character(')'),Character('[report]'),Character(')'),\
            Character('->'),Character('('),\
            Character('(mine_found)'),Character('?'),Character('('),\
            Character('<!>'),Character('('),\
            Character('(is_armed)'),Character(')'),Character('[disarm]'),Character(')'),Character(')'),\
            Character('->'),Character('('),\
            Character('(benign_object_found)'),Character('[pick_up]'),Character(')'),\
            Character('->'),Character('('),\
            Character('(carrying_benign)'),Character('[take_to_drop_off]'),Character(')'),\
            Character('->'),Character('('),\
            Character('(likely_target_found)'),Character('[go_to_likely_target]'),Character(')'),\
            Character('[random_walk]'),\
            Character(')')]
        '''
        '''
        character_list = [Character('?'),Character('('),\
            Character('->'),Character('('),\
            Character('->'),Character('('),\
            Character('?'),Character('('),\
            Character('<!>'),Character('('),\
            Character('(likely_target_found)'),Character(')'),\
            Character('(is_armed)'), Character(')'),\
            Character('[random_walk]'),Character(')'),\
            Character('(carrying_benign)'),Character(')'),\
            Character('[pick_up]'),Character(')')]
        '''
        '''
        character_list = [Character('?'),Character('('),\
            Character('?'),Character('('),\
            Character('->'),Character('('),\
            Character('(mine_found)'),Character('[disarm]'),Character(')'),\
            Character('[shortest_path]'),Character(')'),\
            Character('[go_to_comms]'),Character(')')]



        cfg_word = Word(character_list) 
        '''
        # cfg_word = createWord('?  (  ->  (  (in_comms)  ?  (  (battery_low)  [random_walk]  )  )  ->  (  ?  (  [go_to_comms]  [report]  )  [report]  ?  (  (at_surface)  (benign_object_found)  [take_to_drop_off]  )  )  )')
        # bt_root, bt = cfg_word.createBT()

        cfg_word = createWord('?  (  ->  (  (is_armed)  [disarm]  )  ->  (  ?  (  [shortest_path]  [shortest_path]  [shortest_path]  )  ?  (  [shortest_path]  [shortest_path]  [shortest_path]  [shortest_path]  )  )  ) ')
        bt_root, bt = cfg_word.createBT()

        

        max_iterations = 1000

        # Create the world
        world = World(config)
        do_test = True # don't error check graph

        world.init_world(seed, do_test)

        robot = Robot(config, robot_id, num_robots, seed, bt, max_iterations, world)
        # cProfile.run('RobotController(config, robot)')
        robot_controller = RobotController(config, robot)
        score, target_reported, distance = robot_controller.run()
        print('Score: ', score)
        if target_reported:
            print('Has reported:', target_reported, 'not necessarily correctly')
        else:
            print('Has reported:', target_reported)
    except rospy.ROSInterruptException: pass