
import yaml
import rospkg
import rospy
from behavior_tree.behavior_tree import *
from behavior_tree_msgs.msg import Status, Active

import behavior_tree.behavior_tree_graphviz as gv
import zlib

from cfg import exportBT, getSubtreeIndices

'''
def getActionsConditions():

    ?? this function should be identical to the getActionsConditions() in cfg, after changes are made there

    # Read in the list of actions and conditions from the bt_list file
    rospack = rospkg.RosPack()
    filepath = rospack.get_path('simulator') + "/config/" + rospy.get_param('~bt_list')
    with open(filepath, 'r') as stream:
        bt_list = yaml.safe_load(stream)

    return bt_list["actions"], bt_list["conditions"]
'''
def getActionsConditions():
    # Read in the list of actions and conditions from the bt_list file
    rospack = rospkg.RosPack()
    filepath = rospack.get_path('simulator') + "/config/" + rospy.get_param('~bt_list')
    with open(filepath, 'r') as stream:
        bt_list = yaml.safe_load(stream)

    # Extract conditions and actions
    conditions = []
    actions = []

    # Loop over all groups
    for g in bt_list['groups']:
        conditions.extend(g['conditions'])
        actions.extend(g['actions'])

    # remove duplicates
    conditions = list(set(conditions))
    actions = list(set(actions))

    return actions, conditions
    #return bt_list["actions"], bt_list["conditions"]

class BT_Interface():
    def __init__(self, bt):

        self.bt = bt

        self.graphviz_pub = rospy.Publisher('behavior_tree_graphviz', String, queue_size=1)
        self.compressed_pub = rospy.Publisher('behavior_tree_graphviz_compressed', String, queue_size=1)

        self.init_bt()

        # Get my actions and conditions
        self.actions, self.conditions = getActionsConditions()

        # Precompute dict of nodes in BT
        # Each label (key) contains a list of nodes (value)
        self.defineActionNodes()        
        self.defineConditionNodes()

        self.initActiveTest()

    def init_bt(self):
        # print("BT_Interface initialising BT...")
        for node in self.bt.nodes:
            node.init_ros()
            # print(node.label)
        # print("BT finished init")

    def tick_bt(self):
        self.bt.tick()#root.tick(True)

        self.activeTest()

        source = gv.get_graphviz(self.bt)
        source_msg = String()
        source_msg.data = source
        self.graphviz_pub.publish(source_msg)

        compressed = String()
        compressed.data = zlib.compress(source)
        self.compressed_pub.publish(compressed)

    def defineActionNodes(self):

        self.action_nodes = dict()

        if not self.bt.nodes:
            print("defineActionNodes: bt empty!")
        else:
            for n in self.bt.nodes:
                if n.__class__ == Action:
                    if n.label not in self.action_nodes:

                        # Create empty list
                        self.action_nodes[n.label] = []

                    # Add it to the dictionary
                    self.action_nodes[n.label].append(n)


    def defineConditionNodes(self):

        self.condition_nodes = dict()

        if not self.bt.nodes:
            print("defineConditionNodes: bt empty!")
        else:
            for n in self.bt.nodes:
                if n.__class__ == Condition:
                    #print(n.label,"n.label")
                    if n.label not in self.condition_nodes:

                        # Create empty list
                        self.condition_nodes[n.label] = []

                    # Add it to the dictionary
                    self.condition_nodes[n.label].append(n)

    def initActiveTest(self):

        self.node_activated = [False]*len(self.bt.nodes)

    def activeTest(self):

        for n_idx in xrange(len(self.bt.nodes)):            
            n = self.bt.nodes[n_idx]
            if n.is_active:
                self.node_activated[n_idx] = True

    def generateActiveCFGWord(self):
        '''
        print("len(self.bt.nodes)", len(self.bt.nodes))
        self.bt.print_BT()
        for n_idx in xrange(len(self.bt.nodes)):            
            n = self.bt.nodes[n_idx]
            print(n.__class__.__name__)
        '''
        return exportBT(self.bt, self.node_activated)

    def getActiveSubtreeIndices(self):

        return getSubtreeIndices(self.bt, self.node_activated)
    

    def getActiveActions(self):
        # returns list of all actions that are active currently as a list of strings (i.e. names)

        active_actions = []
        
        for n in self.action_nodes.values():
            is_active = False
            for node in n:
                if node.is_active:
                    is_active = True
            if is_active:
                active_actions.append(n[0].label)

        return active_actions

    def setConditionStatus(self, condition, success):
        # it takes as input a condition label ex. 'at surface'
        # also takes success, which is boolean: True or False
        # if you call this function with success = True and that label
        # then it tells BT that 'at surface' is successful
        
        #print(self.condition_nodes.keys())

        try:
            nodes = self.condition_nodes[condition]
        except KeyError:
            pass
            #print("setConditionStatus condition " + condition + " does not exist in BT")
        else:

            # Set the status of a condition to SUCCESS or FAILURE
            if success == True:
                for node in nodes:
                    node.set_status(ReturnStatus(Status.SUCCESS))
            elif success == False:
                for node in nodes:
                    node.set_status(ReturnStatus(Status.FAILURE))
            else:
                print("setConditionStatus: incorrect argument")

    def setActionStatusFailure(self, action):
        try:
            nodes = self.action_nodes[action]
        except KeyError:
            print("setActionStatusFailure action " + action + " does not exist in BT")
        else:
            for node in nodes:
                node.set_status(ReturnStatus(Status.FAILURE))

    def setActionStatusRunning(self, action):
        try:
            nodes = self.action_nodes[action]
        except KeyError:
            print("setActionStatusFailure action " + action + " does not exist in BT")
        else:
            for node in nodes:
                node.set_status(ReturnStatus(Status.RUNNING))

    def setActionStatusSuccess(self, action):
        try:
            nodes = self.action_nodes[action]
        except KeyError:
            print("setActionStatusFailure action " + action + " does not exist in BT")
        else:
            for node in nodes:
                node.set_status(ReturnStatus(Status.SUCCESS))
