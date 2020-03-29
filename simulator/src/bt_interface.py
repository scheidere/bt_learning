
import yaml
import rospkg
import rospy
from behavior_tree import *
from behavior_tree_msgs.msg import Status, Active

def getActionsConditions():
    # Read in the list of actions and conditions from the bt_list file
    rospack = rospkg.RosPack()
    filepath = rospack.get_path('simulator') + "/config/" + rospy.get_param('~bt_list')
    with open(filepath, 'r') as stream:
        bt_list = yaml.safe_load(stream)

    return bt_list["actions"], bt_list["conditions"]

class BT_Interface():
    def __init__(self, bt):

        self.bt = bt

        # Get my actions and conditions
        self.actions, self.conditions = getActionsConditions()

        # Precompute dict of nodes in BT
        # Each label (key) contains a list of nodes (value)
        self.defineActionNodes()        
        self.defineConditionNodes()

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
                    if n.label not in self.condition_nodes:

                        # Create empty list
                        self.condition_nodes[n.label] = []

                    # Add it to the dictionary
                    self.condition_nodes[n.label].append(n)
    

    def getActiveActions(self):

        active_actions = []
        
        for n in self.actions_nodes.values():
            is_active = False
            for node in n:
                if node.is_active:
                    is_active = True
            if is_active:
                active_actions.append(n.label)

        return active_actions

    def setConditionStatus(self, condition, success):

        try:
            nodes = self.condition_nodes[condition]
        except KeyError:
            print("setConditionStatus condition " + condition + " does not exist in BT")
        else:

            # Set the status of a condition to SUCCESS or FAILURE
            if success == True:
                for node in nodes:
                    node.set_status(Status.SUCCESS)
            elif success == False:
                for node in nodes:
                    node.set_status(Status.FAILURE)
            else:
                print("setConditionStatus: incorrect argument")

    def setActionStatusFailure(self, action):
        try:
            nodes = self.action_nodes[action]
        except KeyError:
            print("setActionStatusFailure action " + action + " does not exist in BT")
        else:
            for node in nodes:
                node.set_status(Status.FAILURE)

    def setActionStatusRunning(self, action):
        try:
            nodes = self.action_nodes[action]
        except KeyError:
            print("setActionStatusFailure action " + action + " does not exist in BT")
        else:
            for node in nodes:
                node.set_status(Status.RUNNING)

    def setActionStatusSuccess(self, action):
        try:
            nodes = self.action_nodes[action]
        except KeyError:
            print("setActionStatusFailure action " + action + " does not exist in BT")
        else:
            for node in nodes:
                node.set_status(Status.SUCCESS)
