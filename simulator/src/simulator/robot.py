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
from cfg import CFG, Word, Character

import numpy as np



class State():
    def __init__(self, vertex_idx):
        # describes a point along an edge
        # if two indices are equal then is at that edge
        self.vertex_from_idx = vertex_idx
        self.vertex_to_idx = vertex_idx
        self.fraction_along_edge = 0

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


class TargetBelief():
    #prob distribution over the vertices
    def __init__(self, num_vertices, sensor_model):
        #self.world = world # could do it this way too

        self.num_vertices = num_vertices

        self.sensor_model = sensor_model

        self.init_prior()

    def init_prior(self):
        ## P(Y)
        p = 1.0/self.num_vertices
        self.prob_dist = np.full(self.num_vertices, p)

    def likelihood(self, x, y, z):

        likelihoods = self.sensor_model.all_likelihoods(x, y)
        return likelihoods[z]

    def bayes_update(self, x, z):
        ## P(Y|Z)

        for y in xrange(self.num_vertices):
            self.prob_dist[y] *= self.likelihood(x, y, z)
            
        total = sum(self.prob_dist)

        # Normalize
        self.prob_dist /= total

    def found_false_update(self, vertex_false_idx):
        # You now know that the target is not where you chose, so prob = 0 there
        old_p = self.prob_dist[vertex_false_idx]
        self.prob_dist[vertex_false_idx] = 0

        # Get new total
        # Assume was normalised before...
        total = 1.0 - old_p

        # Normalize to accomodate change
        self.prob_dist /= total

    def generateRobotBeliefIdx(self):
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
        return np.argmax(self.prob_dist)

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



class Robot():

    PLANNER_TYPE_STOP = 0 # only used if the BT says to do nothing
    PLANNER_TYPE_RANDOM = 1
    PLANNER_TYPE_SHORTEST = 2
    PLANNER_TYPE_COMMSRANGE = 3  #need to use this below, want to test original shortest path planner first
    PLANNER_TYPE_PEAKBELIEF = 4

    def __init__(self, config, robot_id, num_robots, seed, bt, max_iterations, world):

        self.bt = bt
        self.config = config
        self.robot_id = robot_id
        self.speed = config["robot_speed"]
        self.planner_type = Robot.PLANNER_TYPE_RANDOM
        #self.communicate_observations = communicate_observations

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

        # Setup a set of random numbers
        # print("Setup set of random numbers")
        self.setup_random_numbers(seed)

        # Setup state belief
        # print("Setup state belief")
        self.state = []
        random_start_vertex = self.get_next_random_number()
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

        # create sensor model
        # moved within world instead
        # self.sensor_model = SensorModel(config,num_vertices,self.known_world)

        # self.known_world.set_sensor_model(self.sensor_model)

        # Generate belief of where target could be
        self.target_belief = TargetBelief(num_vertices, self.known_world.sensor_model)

        # Set up Scorer
        self.basestation_scorer = Scorer(self.known_world, max_iterations)

        # plot
        # print("plot")
        self.h_state = None
        self.robot_plot = config["robot_plot"]
        if self.robot_plot:
            rospy.loginfo("plotting robot world")
            self.plot_robot()


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

            # print("position: ")
            # pos = self.state.get_position(self.known_world)
            # print(pos.x, pos.y, pos.z)
            
            # Plan
            # print("plan")
            action_sequence = None          
            if self.state.at_vertex():
                action_sequence = self.plan()

            # Move
            # print("move")
            [new_vertex, distance_traveled, no_move] = self.move(action_sequence, distance_to_travel)
            if not no_move:
                moved = True
            if no_move or distance_traveled == 0:
                distance_to_travel = 0
            else:
                distance_to_travel -= distance_traveled

            # Observe
            if new_vertex:
                # print("observe")

                x = self.state.vertex_from_idx
                z = self.observe(x)
                self.target_belief.bayes_update(x,z)

                # default is that robot does not know answer
                #robot_has_ans = False # maybe relates to BT, BT can learn this (report action node)

                # Choose vertex idx to report as belief of target location based on prob dist
                robot_belief_idx = self.target_belief.generateRobotBeliefIdx()

                # Check if at surface, either True or False
                is_at_surface = self.state.at_surface(self.known_world)

                # Check if in comms range, True or False
                is_in_comms = self.state.in_comms(self.known_world)

                # If the robot has reported something
                response = self.basestation_scorer.submit_target(robot_belief_idx, x, is_at_surface, is_in_comms, num_iterations)

                if response == self.basestation_scorer.RESPONSE_FALSE:
                    self.target_belief.found_false_update(robot_belief_idx)

            # if no response, nothing happens

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
        #print('thinks it is in comms',is_in_comms)
        target_found_50 = self.target_belief.target_found_50()
        target_found_70 = self.target_belief.target_found_70()
        target_found_90 = self.target_belief.target_found_90()


        self.bt_interface.setConditionStatus('at_surface', is_at_surface)

        self.bt_interface.setConditionStatus('in_comms', is_in_comms)

        self.bt_interface.setConditionStatus('target_found_50', target_found_50)

        self.bt_interface.setConditionStatus('target_found_70', target_found_70)

        self.bt_interface.setConditionStatus('target_found_90', target_found_90)

        # ... more conditions


    def get_planner_type(self):
        active_actions = self.bt_interface.getActiveActions()
        #print(active_actions)

        if 'go_to_comms' in active_actions:
            self.planner_type = Robot.PLANNER_TYPE_COMMSRANGE

        elif 'go_to_belief' in active_actions:
            self.planner_type = Robot.PLANNER_TYPE_PEAKBELIEF

        elif 'random_walk' in active_actions:
            self.planner_type = Robot.PLANNER_TYPE_RANDOM

        elif 'shortest_path' in active_actions:
            self.planner_type = Robot.PLANNER_TYPE_SHORTEST
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
            elif action == 'go_to_belief':
                if self.planner_type == Robot.PLANNER_TYPE_PEAKBELIEF:
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
            else:
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

        elif self.planner_type == Robot.PLANNER_TYPE_COMMSRANGE:
            planner = planners.PlannerCommsRange(self, self.known_world)

            planner.set_parameters(self.state.vertex_from_idx)

            action_sequence = planner.plan(debug)
            return action_sequence

        elif self.planner_type == Robot.PLANNER_TYPE_SHORTEST:
            planner = planners.PlannerShortestPath(self, self.known_world)
            use_known_world = False

            # set a random goal if not already set
            try:
                self.current_goal_vertex

            except AttributeError:
                self.current_goal_vertex = self.get_next_random_number()
                while self.known_world.vertices[self.current_goal_vertex].position.z > self.known_world.surface_level - 0.0001:
                    self.current_goal_vertex = self.get_next_random_number()

            # plan shortest path to goal
            planner.set_parameters(self.state.vertex_from_idx, self.current_goal_vertex, use_known_world)
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

    def plot_robot(self):
        plt.rcParams['toolbar'] = 'None'
        fig = plt.figure(1)
        ax = plt.gca()

        if not self.h_state: #don't redraw if already drawn
            self.known_world.plot_world(ax,self.target_belief)
        else:
            self.known_world.plot_world_update(ax,self.target_belief)


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
            if action == current_state.vertex_from_idx:
                # get the next action instead
                if len(action_sequence) >= 1:
                    action = action_sequence[1]
                else:
                    distance_traveled = 0
                    no_move = True
                    rospy.logwarn("robot is idle since plan gives current index")

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
        z = self.robot.observe(x)
        self.robot.target_belief.bayes_update(x,z)

        start_time = rospy.Time.now()
        num_iterations = 0

        no_move_count = 0

        # Continue indefinitely
        while not rospy.is_shutdown():   

            # print("iteration: " + str(num_iterations))
            no_move = self.robot.do_iteration(num_iterations)       
            num_iterations += 1
            # print(num_iterations)

            self.robot.basestation_scorer.update_scorer(num_iterations)
            if self.robot.basestation_scorer.finished: #checks if answer is correct, and if so stops sim
                break

            # Exit early if the robot hasn't moved in a while
            if no_move and num_iterations >= 3:
                no_move_count += 1
                # print("no_move_count", no_move_count)
                if no_move_count >= 3:
                    # print("exiting due to robot not moving")
                    break
            else:
                no_move_count = 0

        return self.robot.basestation_scorer.score





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
        #    Character('[go_to_comms]'),Character(')'),Character(')'),Character('[random_walk]'),Character(')')]
        
        character_list = [Character('->'),Character('('),Character('[go_to_belief]'),Character(')')]
        cfg_word = Word(character_list) 
        bt_root, bt = cfg_word.createBT()

        max_iterations = 1000

        # Create the world
        world = World(config)
        do_test = True # don't error check graph

        world.init_world(seed, do_test)

        robot = Robot(config, robot_id, num_robots, seed, bt, max_iterations, world)
        # cProfile.run('RobotController(config, robot)')
        robot_controller = RobotController(config, robot)
        score = robot_controller.run()
        print('Score: ', score)
    except rospy.ROSInterruptException: pass