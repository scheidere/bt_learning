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

import copy

import planners
#import communication_planner

import random

# import cProfile


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

    # Determine if you are at the surface or not 
    def at_surface(self, world):
        position = self.get_position(world)
        at_surface = world.surface_level
        if position.z > at_surface - 0.0001:
            return True
        else:
            return False

class TargetBelief():
    #prob distribution over the vertices
    def __init__(self, world, vertex_robot):
        #self.world = world # could do it this way too

        self.x = vertex_robot ??? # location of robot
        self.y = world.create_target() # generates a random_vertex where the target is
        ###self.possible_zs = [self.y,not y, None]  # location robot believes the target is

        self.sensor_range = self.config["sensor_range"]

    def init_prior(self):
        num_vertices = len(world.vertices)
        return 1/num_vertices


    def likelihood(self,world, z):
        # distance from robot to z
        d = world.distance(self.x,z)

        # before normalization
        if d < self.sensor_range:
            p_correct = 0.95 - 0.01*d #f
            p_false = 0.2 #g
            p_none = 1 - p_correct #1-f
        else:
            p_correct = 0
            p_false = 0
            p_none = 1

        # Normalize
        norm = p_correct + p_false + p_none #same as 1 + p_false
        p_correct = p_correct/norm
        p_false = p_false/norm
        p_none = p_none/norm

        return p_correct, p_false, p_none

    def generate_distribution(self, world):
        
        prob_dist = []

        # remember to normalize again after each update

        # get robot observation
        z = world.robot_env_observation(self.x,self.y)

        is_first = True
        if is_first:
            for vertex_idx in xrange(len(world.vertices)):
                init = self.likelihood(world,z)*self.init_prior()
                prob_dist.append(init)

            is_first = False
            #NEED TO NORMALIZE AGAIN

        else:
            for prior in prob_dist:
                update = likelihood*
                prob_dist.append(update)

        return prob_dist

        





class Robot():

    PLANNER_TYPE_RANDOM = 1
    PLANNER_TYPE_SHORTEST = 2

    def __init__(self, config, robot_id, num_robots, seed):

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
        print("Setup navigation roadmap")
        self.known_world = World(config)
        self.known_world.init_world(seed)

        # Setup a set of random numbers
        print("Setup set of random numbers")
        self.setup_random_numbers(seed)

        # Setup state belief
        print("Setup state belief")
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

        # plot
        print("plot")
        self.h_state = None
        if config["robot_plot"]:
            rospy.loginfo("plotting robot world")
            self.plot_robot()

        print("finished init")

    def setup_random_numbers(self, seed):
        # sets up a persistent set of numbers
        # for repeatable tests
        self.random_number_list = []

        random.seed(seed)
        
        for i in xrange(10000):
            random_number = random.randint(0,len(self.known_world.vertices)-1)
            self.random_number_list.append(random_number)

        self.random_number_list_index = 0

    def get_next_random_number(self):
        number = self.random_number_list[self.random_number_list_index]
        self.random_number_list_index = self.random_number_list_index + 1
        if self.random_number_list_index >= len(self.random_number_list):
            self.random_number_list_index = 0
        return number


    def do_iteration(self):
        #rospy.loginfo("robot do_iteration")

        #self.scoring_statistics.count_iterations += 1

        distance_to_travel = self.speed
        print("dist to travel", distance_to_travel)
        while distance_to_travel > 0:

            # Plan
            print("plan")
            action_sequence = None          
            if self.state.at_vertex():
                print("plan statement")
                action_sequence = robot.plan()

            # Move
            print("move")
            [new_vertex, distance_traveled] = self.move(action_sequence, distance_to_travel)
            if distance_traveled == 0:
                print("move 1")
                distance_to_travel = 0
            else:
                print("move 2")
                distance_to_travel -= distance_traveled
            #self.publish_position() # for plotting purposes

            # Observe
            if new_vertex:
                print("observe")
                self.observe()
                '''
                # Share observation
                if self.communicate_observations == 'always':
                    self.send_observations( self.state.vertex_from_idx )
                elif self.communicate_observations == 'communication_planner':
                    debug_mode = False
                    vertex_idx = self.state.vertex_from_idx
                    do_comms = communication_planner.plan_communication(self, self.get_observations_msg(vertex_idx), debug_mode )
                    if do_comms:
                        already_communicated = vertex_idx in self.vertices_communicated
                        if already_communicated:
                            # ?? why is it being sent again!!
                            rospy.logwarn("duplicate communication??")
                            debug_mode = True
                            do_comms_check_again = communication_planner.plan_communication(self, self.get_observations_msg(vertex_idx), debug_mode )
                            if not do_comms_check_again:
                                rospy.logwarn('changed mind on second check??')
                        self.send_observations( self.state.vertex_from_idx )                        
                elif self.communicate_observations == 'on_predicted_path':
                    self.send_observations_on_predicted_path( self.state.vertex_from_idx )
                elif self.communicate_observations == 'never':
                    pass
                else:
                    rospy.logerr("communicate_observations type not specified")
                '''
        # plot
        if config["robot_plot"]:
            #rospy.loginfo("plotting robot world")
            self.plot_robot()
    '''
    def publish_statistics(self):
        self.publisher_statistics.publish(self.scoring_statistics)
    
    def publish_statistics_event(self,event):
        # wraper for timer event
        self.publish_statistics()
    '''
    def plan(self, debug=False):
        #rospy.loginfo("Generating new plan")

        if self.planner_type == Robot.PLANNER_TYPE_RANDOM:
            planner = planners.PlannerRandomWalk(self, self.known_world)
            action_sequence = planner.plan()
            return action_sequence

        elif self.planner_type == Robot.PLANNER_TYPE_SHORTEST:
            planner = planners.PlannerShortestPath(self, self.known_world)
            use_known_world = False

            # set a random goal if not already set
            try:
                self.current_goal_vertex

            except AttributeError:
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
                
                return None
            else:
                return action_sequence

    def observe(self):
        pass
        # need to observe targets instead of observing graph itself

    '''            
    def observe(self):
        # ask the ground truth for an observation
        # rospy.loginfo("Making an observation")
        rospy.wait_for_service('get_ground_truth_observation')
        get_ground_truth_observation = rospy.ServiceProxy('get_ground_truth_observation', GroundTruthObservation)
        observed_edges = get_ground_truth_observation(self.state.vertex_from_idx).observed_edges

        # merge this into the world belief
        self.known_world.merge_observations(observed_edges)
    '''

    def plot_robot(self):
        plt.rcParams['toolbar'] = 'None'
        fig = plt.figure(1)
        ax = plt.gca()

        if not self.h_state: #don't redraw if already drawn
            self.known_world.plot_world(ax)


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
                    rospy.logwarn("robot is idle since plan gives current index")
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
            pass

        return [new_vertex, distance_traveled]
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
        # Give an initial observation
        print("Give an initial observation")
        robot.observe()

        # periodically publish statistics/scores etc
        #rospy.Timer(rospy.Duration(0.1), robot.publish_statistics_event, oneshot=False)

        # use_sleep = config["ground_truth_plot"] or config["robot_plot"] 

        iteration_rate = config["iteration_rate"]
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
                iteration_start_time = rospy.Time.now()
                robot.do_iteration()       
                num_iterations += 1   
                iteration_end_time = rospy.Time.now()
                work_time += iteration_end_time - iteration_start_time
                print("num iterations <= expected num interations")
                if ( current_time - start_time ).to_sec() != 0: #don't divide by zero
                    current_rate = num_iterations / ( current_time - start_time ).to_sec()
                    cpu_usage = work_time.to_sec() / (current_time - start_time).to_sec()
                    
                    if num_iterations <= expected_num_iterations * 0.9:                    
                        rospy.logerr("rate control lagging: num_iterations: " + str(num_iterations) + " expected: " + str(expected_num_iterations))
                        rospy.logwarn("current rate: " + str(current_rate) + " cpu usage: " + str(cpu_usage)) 

            # if use_sleep:
            #     rospy.sleep(0.01)
            # else:
            #     # rate.sleep()
            #     



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
        real_robot = True
        robot = Robot(config, robot_id, num_robots, seed)
        # cProfile.run('RobotController(config, robot)')
        robot_controller = RobotController(config, robot)
    except rospy.ROSInterruptException: pass