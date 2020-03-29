#!/usr/bin/env python

import rospy
import rospkg
import roslaunch
from comms_planning.msg import ScoringStatisticsArray
from comms_planning.msg import ScoringStatistics

import scipy.io as sio # to save matlab .mat files
import os

from shutil import copyfile



def run_scenario(seed,communicate_observations):

    rospy.loginfo("scenario_launcher: beginning scenario with seed " + str(seed) )

    # Get the config file etc
    config = rospy.get_param('~config')
    num_robots = rospy.get_param('~num_robots')
    time_per_scenario = rospy.get_param('~time_per_scenario')

    # setup results
    results = []

    # startup roslaunch
    launch = roslaunch.scriptapi.ROSLaunch()
    launch.start()
    processes = []

    # launch the ground truth world
    rospy.loginfo("scenario_launcher: launch ground truth")
    args_list = [["config", config],["num_robots", num_robots],["seed1", seed],["seed2", seed+1]]
    seed = seed + 2
    args_string = args_list_to_string(args_list)
    print args_string
    node_ground_truth = roslaunch.core.Node('comms_planning', 'ground_truth.py', output='screen', args=args_string)

    process_gt = launch.launch(node_ground_truth)
    #print process.is_alive()

    # launch the robots
    rospy.loginfo("scenario_launcher: launching robots")
    for r in xrange(num_robots):
        robot_id = r        

        args_list = [["config", config],["num_robots", num_robots],["robot_id", robot_id],["seed", seed],["communicate_observations",communicate_observations]]
        seed = seed+1
        args_string = args_list_to_string(args_list)
        node_ground_truth = roslaunch.core.Node('comms_planning', 'robot.py', output='screen', args=args_string)

        processes.append(launch.launch(node_ground_truth))
        #print process.is_alive()

    # wait until timeout
    rospy.loginfo("scenario_launcher: waiting")
    start_time = rospy.Time.now()
    end_time = start_time + rospy.Duration(time_per_scenario)
    rate = rospy.Rate(0.2)
    time_left = end_time - rospy.Time.now()
    while not rospy.is_shutdown() and time_left > rospy.Duration(0):                
        rate.sleep()
        time_left = end_time - rospy.Time.now()
        rospy.loginfo("scenario time remaining: %.1f" % time_left.to_sec() )

        # compile results
        #rospy.loginfo("scenario_launcher: compiling results")
        result = dict()
        result["runtime"] = (rospy.Time.now() - start_time).to_sec()
        result["results"] = scoring_statistics_to_dict( rospy.wait_for_message('/statistics_array', ScoringStatisticsArray) )
        results.append(result)

    # close processes
    rospy.loginfo("scenario_launcher: shutting down nodes")
    for p in xrange(len(processes)):
        processes[p].stop()
    rospy.sleep(1)
    process_gt.stop()

    # return results
    return results

def args_list_to_string(args_list):
    # since the API can't do this itself???
    string = ""
    for i in xrange(len(args_list)):
        name = args_list[i][0]
        value = args_list[i][1]
        string = string + "_" + name + ":=\"" + str(value) + "\" " 
    return string

def scoring_statistics_to_dict(msg):
    # surely there's a better way of doing this??
    out_list = []
    for i in range(len(msg.stats)):
        out = dict()
        stat = msg.stats[i]
        out["robot_id"] = stat.robot_id
        out["goals_reached"] = stat.goals_reached
        out["goals_skipped"] = stat.goals_skipped
        out["count_iterations"] = stat.count_iterations
        out["count_vertices"] = stat.count_vertices
        out["count_communication_transmit"] = stat.count_communication_transmit
        out_list.append(out)
    return out_list

def run_tests():

    num_tests = rospy.get_param('~num_tests')

    communicate_observations_list = ['communication_planner', 'on_predicted_path', 'always', 'never']

    time_string = str(rospy.Time.now()) 
    name = "results_" + time_string
    results_directory = "/home/graeme/comms_planning_log/" + name + "/"
    results_filename = results_directory + name
    os.mkdir(results_directory)
    file_count = 0

    rospack = rospkg.RosPack()
    config_filepath = rospack.get_path('comms_planning') + "/config/" + rospy.get_param('~config')
    config_filepath_cp = results_directory + rospy.get_param('~config')
    copyfile(config_filepath, config_filepath_cp)

    results = []

    for test_number in xrange(num_tests):
        rospy.loginfo("scenario_launcher: test_number " + str(test_number) + " of " + str(num_tests))
        results.append([])
        for list_idx in xrange(len(communicate_observations_list)):
            rospy.loginfo("scenario_launcher: list_idx " + str(list_idx))
            communicate_observations = communicate_observations_list[list_idx]
            seed = test_number
            results[test_number].append( run_scenario(seed,communicate_observations) )

            # save to file
            results_dict = dict()
            results_dict["results"] = results
            results_dict["communicate_observations_list"] = communicate_observations_list
            results_dict["time"] = str(rospy.Time.now())
            results_filename_append = results_filename + "_" + str(file_count).zfill(4) + ".mat"
            file_count = file_count + 1
            sio.savemat(results_filename_append, results_dict)

    rospy.loginfo("scenario_launcher: finished!!")
    rospy.loginfo("results_directory: " + results_directory)

# Main function.
if __name__ == '__main__':
    
    # Initialise the node
    rospy.init_node('scenario_launcher')

    try:
        run_tests()
    except rospy.ROSInterruptException: pass
