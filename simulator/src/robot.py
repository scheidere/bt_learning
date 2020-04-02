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

from sensor_model import SensorModel
from scorer import Scorer

import copy

import planners
#import communication_planner

import random

from bt_interface import *
from behavior_tree.behavior_tree import *
from cfg import CFG, Word, Character

import behavior_tree.behavior_tree_graphviz as gv
import zlib


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

        self.prob_dist = []
        for i in xrange(self.num_vertices):
            self.prob_dist.append(1.0/self.num_vertices)

    def likelihood(self, x, y, z):

        likelihoods = self.sensor_model.all_likelihoods(x, y)
        return likelihoods[z]

    def bayes_update(self, x, z):
        ## P(Y|Z)

        total = 0
        for y in xrange(len(self.prob_dist)):
            self.prob_dist[y] = self.likelihood(x, y, z)*self.prob_dist[y]
            total += self.prob_dist[y]

        # Normalize
        for y in xrange(len(self.prob_dist)):
            self.prob_dist[y] = self.prob_dist[y]/total

    def found_false_update(self, vertex_false_idx):
        # You now know that the target is not where you chose, so prob = 0 there
        self.prob_dist[vertex_false_idx] = 0

        # Get new total
        total = 0
        for y in xrange(len(self.prob_dist)):
            total += self.prob_dist[y]

        # Normalize to accomodate change
        for y in xrange(len(self.prob_dist)):
            self.prob_dist[y] = self.prob_dist[y]/total

    def generateRobotBeliefIdx(self):
        # Robot chooses best based on the probability that a vertex is the target's location
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

    PLANNER_TYPE_RANDOM = 1
    PLANNER_TYPE_SHORTEST = 2
    PLANNER_TYPE_COMMSRANGE = 3  #need to use this below, want to test original shortest path planner first

    def __init__(self, config, robot_id, num_robots, seed, bt):

        self.bt = bt

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

        #print(bt)
        # Set up BT interface
        self.bt_interface = BT_Interface(bt)

        num_vertices = len(self.known_world.vertices)

        # create sensor model
        self.sensor_model = SensorModel(config,num_vertices,self.known_world)

        self.known_world.set_sensor_model(self.sensor_model)

        # Generate belief of where target could be
        self.target_belief = TargetBelief(num_vertices, self.sensor_model)

        # Set up Scorer
        self.basestation_scorer = Scorer(self.known_world)

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


    def do_iteration(self, num_iterations):
        #rospy.loginfo("robot do_iteration")

        #self.scoring_statistics.count_iterations += 1

        tick_bt(self.bt)

        distance_to_travel = self.speed
        #print("dist to travel", distance_to_travel)
        while distance_to_travel > 0:
            tick_bt(self.bt)
            
            # Plan
            #print("plan")
            action_sequence = None          
            if self.state.at_vertex():
                #print("plan statement")
                action_sequence = robot.plan()

            # Move
            #print("move")
            [new_vertex, distance_traveled] = self.move(action_sequence, distance_to_travel)
            if distance_traveled == 0:
                #print("move 1")
                distance_to_travel = 0
            else:
                #print("move 2")
                distance_to_travel -= distance_traveled
            #self.publish_position() # for plotting purposes

            # Observe
            if new_vertex:
                #print("observe")

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
        if config["robot_plot"]:
            #rospy.loginfo("plotting robot world")
            self.plot_robot()

    def condition_updates(self):

        # Set condition statuses so they can be updated each iteration
        # and used to choose actions accordingly

        is_at_surface = self.state.at_surface(self.known_world)
        is_in_comms = self.state.in_comms(self.known_world)
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
        print(active_actions)

        if 'go_to_comms' in active_actions:
            self.planner_type == Robot.PLANNER_TYPE_COMMSRANGE

        elif 'random_walk' in active_actions:
            self.planner_type == Robot.PLANNER_TYPE_RANDOM

        elif 'shortest_path' in active_actions:
            self.planner_type == Robot.PLANNER_TYPE_SHORTEST
        else:
            print("get_planner_type: No planner was picked")


        # ... more actions (planners)

    def set_action_status(self):
        active_actions = self.bt_interface.getActiveActions()

        for action in active_actions:
            if action == 'go_to_comms':
                if self.planner_type == Robot.PLANNER_TYPE_COMMSRANGE:
                    self.bt_interface.setActionStatusRunning(action)
                else:
                    self.bt_interface.setActionStatusFailure(action)
            elif action == 'random_walk':
                if self.planner_type == Robot.PLANNER_TYPE_RANDOM:
                    self.bt_interface.setActionStatusRunning(action)
                else:
                    self.bt_interface.setActionStatusFailure(action)
            elif action == 'shortest_path':
                if self.planner_type == Robot.PLANNER_TYPE_SHORTEST:
                    self.bt_interface.setActionStatusRunning(action)
                else:
                    self.bt_interface.setActionStatusFailure(action)
            else:
                print("set_action_status: Action does not exist")


    def plan(self, debug=False):
        #rospy.loginfo("Generating new plan")

        self.get_planner_type()

        if self.planner_type == Robot.PLANNER_TYPE_RANDOM:
            planner = planners.PlannerRandomWalk(self, self.known_world)
            action_sequence = planner.plan()
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

    def observe(self,x):
        return self.known_world.robot_env_observations(x)

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
        x = robot.state.vertex_from_idx
        z = robot.observe(x)
        robot.target_belief.bayes_update(x,z)


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
                robot.do_iteration(num_iterations)       
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

                if robot.basestation_scorer.finished: #checks if answer is correct, and if so stops sim
                    break

        return robot.basestation_scorer.score
      
def init_bt(bt):
    for node in bt.nodes:
        node.init_ros()

def tick_bt(bt):
    bt.tick()#root.tick(True)

    source = gv.get_graphviz(bt)
    source_msg = String()
    source_msg.data = source
    graphviz_pub.publish(source_msg)

    compressed = String()
    compressed.data = zlib.compress(source)
    compressed_pub.publish(compressed)


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
        character_list = [Character('?'),Character('('), Character('->'),Character('('),\
            Character('(target_found_90)'),Character('?'),Character('('),Character('(in_comms)'),\
            Character('[go_to_comms]'),Character(')'),Character(')'),Character('[random_walk]'),Character(')')]
        cfg_word = Word(character_list) 
        bt_root, bt = cfg_word.createBT()
        init_bt(bt)

        graphviz_pub = rospy.Publisher('behavior_tree_graphviz', String, queue_size=1)
        compressed_pub = rospy.Publisher('behavior_tree_graphviz_compressed', String, queue_size=1)

        tick_bt(bt)

        robot = Robot(config, robot_id, num_robots, seed, bt)
        # cProfile.run('RobotController(config, robot)')
        robot_controller = RobotController(config, robot)
    except rospy.ROSInterruptException: pass