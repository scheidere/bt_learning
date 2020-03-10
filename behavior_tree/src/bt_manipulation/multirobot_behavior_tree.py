#!/usr/bin/python
import rospy
from std_msgs.msg import Bool
from std_msgs.msg import String
from behavior_tree_msgs.msg import Status, Active
import sys
import rospkg

#================================================================================================================
# ----------------------------------------------- Return Status  ------------------------------------------------
#================================================================================================================

class ReturnStatus:
    def __init__(self, status):
        if status == Status.FAILURE or status == Status.RUNNING or status == Status.SUCCESS:
            self.status = status
        else:
            print('Invalid return status: ' + status +', defaulting to FAILURE.')
            self.status = Status.FAILURE

    def __eq__(self, other):
        return self.status == other.status
    
    def __ne__(self, other):
        return self.status != other.status
    
    def __str__(self):
        return self.status

ReturnStatus.FAILURE = ReturnStatus(Status.FAILURE)
ReturnStatus.RUNNING = ReturnStatus(Status.RUNNING)
ReturnStatus.SUCCESS = ReturnStatus(Status.SUCCESS)

#================================================================================================================
# ----------------------------------------------- Base Node Class -----------------------------------------------
#================================================================================================================

class Node(object):
    max_wait_time = 1.0
    def __init__(self, label):
        self.label = label
        self.children = []
        self.is_active = False
        self.status = ReturnStatus.FAILURE
        #self.max_wait_time = 1.0
    
    def add_child(self, node):
        self.children.append(node)

    def tick(self, active, traversal_count):
        print('tick not implemented for node ' + self.label)
    
    def init_ros(self):
        pass


#================================================================================================================
# ---------------------------------------------- Control Flow Nodes ---------------------------------------------
#================================================================================================================

class ControlFlowNode(Node):
    label = 'Unlabeled Control Flow Node'
    def __init__(self):
        Node.__init__(self, self.label)

class Fallback(ControlFlowNode):
    label = '?'
    
    def __init__(self):
        ControlFlowNode.__init__(self)
    
    def tick(self, active, traversal_count):
        if not active:
            for child in self.children:
                child.tick(False, traversal_count)
        else:
            self.status = ReturnStatus.FAILURE
            for child in self.children:
                if self.status == ReturnStatus.FAILURE:
                    child.tick(True, traversal_count)
                    self.status = child.status
                else:
                    child.tick(False, traversal_count)
        
        self.is_active = active

class Sequence(ControlFlowNode):
    label = u'\u2192' # arrow
    
    def __init__(self):
        ControlFlowNode.__init__(self)
    
    def tick(self, active, traversal_count):
        if not active:
            for child in self.children:
                child.tick(False, traversal_count)
        else:
            self.status = ReturnStatus.SUCCESS
            for child in self.children:
                if self.status == ReturnStatus.SUCCESS:
                    child.tick(True, traversal_count)
                    self.status = child.status
                else:
                    child.tick(False, traversal_count)
        
        self.is_active = active

class Parallel(ControlFlowNode):
    label = '||'

    def __init__(self, child_success_threshold):
        ControlFlowNode.__init__(self)
        self.child_success_threshold = child_success_threshold

    def tick(self, active, traversal_count):
        if not active:
            for child in self.children:
                child.tick(False, traversal_count)
        else:
            child_success_count = 0
            child_failure_count = 0
            for child in self.children:
                child.tick(True, traversal_count)
                if child.status == ReturnStatus.SUCCESS:
                    child_success_count += 1
                elif child.status == ReturnStatus.FAILURE:
                    child_failure_count += 1

            if child_success_count >= self.child_success_threshold:
                self.status = ReturnStatus.SUCCESS
            elif child_failure_count >= len(self.children) - self.child_success_threshold + 1:
                self.status = ReturnStatus.FAILURE
            else:
                self.status = ReturnStatus.RUNNING

        self.is_active = active
        
        
#================================================================================================================
# ----------------------------------------------- Execution Nodes -----------------------------------------------
#================================================================================================================

def get_condition_topic_name(name):
    topic_name = name.lower().replace(' ', '_') + '_success'
    return topic_name

class ExecutionNode(Node):
    def __init__(self, label):
        Node.__init__(self, label)
        self.publisher = None
        self.subscriber = None
        self.status_modification_time = None
    
    def init_ros(self):
        self.init_publisher()
        self.init_subscriber()

    def get_publisher_name(self):
        pass
    
    def init_publisher(self):
        pass

    def get_subscriber_name(self):
        raise NotImplementedError
        
    def init_subscriber(self):
        raise NotImplementedError

    def set_status(self, status):
        self.status = status
        self.status_modification_time = rospy.Time.now()
    
    def get_status_age(self):
        if self.status_modification_time == None:
            return float('inf')
        else:
            return (rospy.Time.now() - self.status_modification_time).to_sec()

class Condition(ExecutionNode):
    def __init__(self, label):
        ExecutionNode.__init__(self, label)
        self.current_traversal_count = -1

    def tick(self, active, traversal_count):
        if self.current_traversal_count != traversal_count:
            self.current_traversal_count = traversal_count
        else:
            if self.is_active:
                return
        
        if self.is_active == False and active == True and self.status == ReturnStatus.FAILURE:
            self.set_status(ReturnStatus.FAILURE)#RUNNING)
        if self.get_status_age() > self.max_wait_time:
            self.set_status(ReturnStatus.FAILURE)
        
        self.is_active = active
        
    def get_subscriber_name(self):
        #sub_name = self.label.lower().replace(' ', '_') + '_success'
        sub_name = get_condition_topic_name(self.label)
        return sub_name
    
    def init_subscriber(self):
        self.subscriber = rospy.Subscriber(self.get_subscriber_name(), Bool, self.callback)

    def callback(self, msg):
        if msg.data:
            self.set_status(ReturnStatus.SUCCESS)
        else:
            self.set_status(ReturnStatus.FAILURE)

class Action(ExecutionNode):
    def __init__(self, label):
        ExecutionNode.__init__(self, label)
        self.current_traversal_count = -1
        self.is_newly_active = False
        self.current_id = 0

    def tick(self, active, traversal_count):
        #print(self.label + ' ticked ' + str(self.current_traversal_count) + ' ' + str(self))
        if self.current_traversal_count != traversal_count:
            self.current_traversal_count = traversal_count
        else:
            if self.is_active:
                return
        
        # if we have just become active, set the status to running
        if self.is_active == False and active == True:# and self.status == ReturnStatus.FAILURE:
            self.set_status(ReturnStatus.RUNNING)
            self.is_newly_active = True
        else:
            self.is_newly_active = False
        # if we haven't received a message within the timeout period, set the status to failed
        if self.get_status_age() > self.max_wait_time:
            self.set_status(ReturnStatus.FAILURE)
        
        self.is_active = active

    def get_publisher_name(self):
        pub_name = self.label.lower().replace(' ', '_') + '_active'
        return pub_name
    
    def init_publisher(self):
        #self.publisher = rospy.Publisher(self.get_publisher_name(), Bool, queue_size=1)
        self.publisher = rospy.Publisher(self.get_publisher_name(), Active, queue_size=1)
    
    def get_subscriber_name(self):
        sub_name = self.label.lower().replace(' ', '_') + '_status'
        return sub_name
    
    def init_subscriber(self):
        self.subscriber = rospy.Subscriber(self.get_subscriber_name(), Status, self.callback)
    
    def callback(self, msg):
        if self.is_active:
            if msg.id != self.current_id:
                print(self.label + ' Incorrect ID', msg.id, self.current_id, self.is_active)
                return
            self.set_status(ReturnStatus(msg.status))
            if msg.status != self.status.status:
                print('Invalid return status "' + msg.status + '" for node ' + self.label)

    def publish_active_msg(self, active_id):
        if self.publisher != None:
            #active_msg = Bool()
            #active_msg.data = self.is_active
            active_msg = Active()
            active_msg.active = self.is_active
            active_msg.id = active_id
            self.current_id = active_id
            self.publisher.publish(active_msg)
        else:
            rospy.logerr('')

#================================================================================================================
# ----------------------------------------------- Decorator Nodes -----------------------------------------------
#================================================================================================================

class Decorator(Node):
    def __init__(self, label):
        Node.__init__(self, label)
    
    def add_child(self, node):
        if len(self.children) == 0:
            self.children.append(node)
        else:
            raise Exception('A Decorator can have only one child.')


class NotDecorator(Decorator):
    def __init__(self):
        Decorator.__init__(self, '!')

    def add_child(self, node):
        if isinstance(node, Condition):
            super(NotDecorator, self).add_child(node)
        else:
            raise Exception('Not Decorators must have a Condition node child.')
    
    def tick(self, active, traversal_count):
        child = self.children[0]
        child.tick(active, traversal_count)
        if child.status == ReturnStatus.SUCCESS:
            self.status = ReturnStatus.FAILURE
        elif child.status == ReturnStatus.FAILURE:
            self.status = ReturnStatus.SUCCESS
        
        self.is_active = active

def get_decorator(label):
    if label == '!':
        return NotDecorator()

#================================================================================================================
# ------------------------------------------------ Behavior Tree ------------------------------------------------
#================================================================================================================

class BehaviorTree:
    def __init__(self, config_filename):
        self.root = None
        self.nodes = []
        self.node_text = []
        self.active_ids = {}
        self.traversal_count = 0

        #self.flag = 1
        self.num_child = ''

        # Parse the input file
        # Leave tree empty if no filename given
        if config_filename != '':
            self.parse_config(config_filename)

        Node.max_wait_time = rospy.get_param('~timeout', 1.0)

        self.active_actions_pub = rospy.Publisher('active_actions', String, queue_size=1)

    def generate_nodes_list(self):
        # This function fills in self.nodes
        # Note that if parse_config is used, this is not necessary (done internally)
        # But if the tree is generated by other means, it might be easier to use this function
        #
        # self.root should already be defined!
        #
        # Depth-first traversal to produce pre-ordering

        # Empty the list, since it's going to be completed regenerated here
        self.nodes = []

        # Setup a stack data structure (similar to nodes_worklist)
        nodes_stack = []
        nodes_stack.append(self.root) #push

        # Do the traversal, using the stack to help
        while len(nodes_stack) != 0:
            current_node = nodes_stack.pop()
            self.nodes.append(current_node)
            for child_idx in reversed(range(len(current_node.children))):
                nodes_stack.append(current_node.children[child_idx]) #push


    def parse_config(self, config_filename):
        rospack = rospkg.RosPack()
        
        fin = open(config_filename)
        nodes_worklist = []
        prev_tabs = 0
        
        lines = fin.read().split('\n')
        
        include = 'include'
        did_include = True

        while did_include:
            did_include = False
            for i in range(len(lines)):
                line = lines[i]
                tabs = len(line) - len(line.lstrip('\t'))
                label = line.strip()
            
                if len(label) >= len(include) and label[:len(include)] == include:
                    did_include = True
                    filename = label.split(include)[-1].strip()
                    while True:
                        try:
                            start = filename.index('$(')
                            end = filename.index(')')
                        except:
                            break
                        find_statement = filename[start:end]
                        package_name = find_statement.split('find')[-1].strip()
                        filename = filename[0:start] + rospack.get_path(package_name) + filename[end+1:]
                        subtree_lines = open(filename).read().split('\n')
                        add_tabs = tabs*'\t'
                        subtree_lines = map(lambda x:add_tabs+x, subtree_lines)
                        del lines[i]
                        lines = lines[:i] + subtree_lines + lines[i:]
        
        for line in lines:
            if len(line) == 0:
                continue
            
            tabs = len(line) - len(line.lstrip('\t'))
            label = line.strip()
            node = None

            if label[:2] == '->':
                node = Sequence()
            elif label[0] == '?':
                node = Fallback()   
            elif label[0] == '|':
                arguments = map(lambda x:x.strip(), label[3:].split(','))
                node = Parallel(int(arguments[0]))
                self.num_child = int(arguments[0])
            elif label[0] == '(':
                node_label = label.replace('(', '').replace(')', '')
                node = Condition(node_label)
                self.node_text = node_label
            elif label[0] == '[':
                node_label = label.replace('[', '').replace(']', '')
                node = Action(node_label)
                self.node_text = node_label
                self.active_ids[node_label] = 0
            elif label[0] == '<':
                node_label = label.replace('<', '').replace('>', '')
                node = get_decorator(node_label)
                self.node_text = node_label

            self.nodes.append(node)
            
            if self.root == None:
                self.root = node
                nodes_worklist.append(node)
                continue
            
            if tabs == prev_tabs+1:
                parent = nodes_worklist[-1]
                parent.add_child(node)
            else:
                for i in range(prev_tabs - tabs + 1):
                    nodes_worklist.pop()
                parent = nodes_worklist[-1]
                parent.add_child(node)
                
            nodes_worklist.append(node)
            prev_tabs = tabs
            # self.write_config(nodes_worklist, prev_tabs, self.node_text)


    # def write_config(self, nodes_worklist, prev_tabs, node_text):
        
    #     rootnode = self.which_node(nodes_worklist[0].__class__.__name__,node_text)
    #     #change the file name each time you want to generate a new config
    #     f = open("test.tree","a")
    #     if self.flag == 1:
    #         self.flag = 0
    #         f.write(rootnode + '\n')
    #     for object in nodes_worklist[prev_tabs:]:
    #         node_type = object.__class__.__name__
    #         node = self.which_node(node_type, node_text)
    #         indent = ''
    #         for i in range(prev_tabs):
    #             indent = indent + '\t'
    #         f.write(indent + node + '\n')
    #     f.close()

    
    def write_config(self, output_filename):
        # Method: Do a depth-first traversal over the tree
        # to produce a pre-ordering
        # Implementation: iteration not recursion
        #
        # pseudocode adapted from https://en.wikipedia.org/wiki/Depth-first_search :
        '''
        open file
        let S be a stack
        S.push(root)
        while S is not empty
            current_node = S.pop()
            file.write( current_node.tabs )
            file.write( current_node.label )
            file.write( '\n' )
            for child in current_node.children in !reverse! order
                S.push(child)
        close file
        '''

        # Open the output file
        f = open(output_filename,"w")

        # Setup a stack data structure (similar to nodes_worklist)
        # Do this for both keeping track of nodes and for number of tabs
        nodes_stack = []
        tabs_stack = []
        nodes_stack.append(self.root) #push
        tabs_stack.append(0) #push

        # Do the traversal, using the stack to help
        while len(nodes_stack) != 0:

            # Pop a node off the stack
            current_node = nodes_stack.pop() #pop
            tabs = tabs_stack.pop() #pop

            # Write a line to the file
            indent = ''
            for i in range(tabs):
                indent = indent + '\t'
            
            label = self.get_node_text(current_node) 

            f.write( indent + label + '\n' )

            # Add all children to the stack
            for child_idx in reversed(range(len(current_node.children))):
                nodes_stack.append(current_node.children[child_idx]) #push
                tabs_stack.append(tabs + 1) #push

        # Close the file
        f.close()

    # def which_node(self, node_type, node_text):

    #     node = node_type
    #     if node == 'Sequence':
    #         node = '->'
    #     elif node == 'Fallback':
    #         node = '?'
    #     elif node == 'Parallel': 
    #         node = '|| ' + str(self.num_child)
    #     elif node == 'Condition':
    #         node = '(' + node_text + ')'
    #     elif node == 'Action':
    #         node = '[' + node_text + ']'
    #     elif node == 'Decorator':
    #         node = '<' + node_text + '>'
    #     return node

    def get_node_text(self, node):

        node_type = node.__class__.__name__

        if node_type == 'Sequence':
            node_label = '->'
        elif node_type == 'Fallback':
            node_label = '?'
        elif node_type == 'Parallel': 
            node_label = '|| ' + str( node.child_success_threshold )
        elif node_type == 'Condition':
            node_text = node.label
            node_label = '(' + node_text + ')'
        elif node_type == 'Action':
            node_text = node.label
            node_label = '[' + node_text + ']'
        elif node_type == 'Decorator':
            node_text = node.label
            node_label = '<' + node_text + '>'
        else:
            node_label = ''
        return node_label

    def tick(self):
        if self.root != None:
            #print('begin tick')
            self.root.tick(True, self.traversal_count)
            #print()
            self.traversal_count += 1
            active_actions = String()
            active_actions.data = ''

            # Make sure that if there are more than one of the same action, if any are active, then active should be published
            unique_action_nodes = {}
            for node in self.nodes:
                if isinstance(node, Action):
                    if node.label not in unique_action_nodes.keys() or node.is_active:
                        #if node.is_active:
                        unique_action_nodes[node.label] = node
                        if node.is_newly_active:
                            self.active_ids[node.label] += 1
                    #else:
                    #    unique_action_nodes[node.label] = node
                        
            for label, node in unique_action_nodes.iteritems():
                #active_msg = Bool()
                #active_msg.data = node.is_active
                #node.publisher.publish(active_msg)
                node.publish_active_msg(self.active_ids[node.label])

                if node.is_active:
                    active_actions.data += label + ', '
            active_actions.data = active_actions.data[:-2] # strip the final comma and space
            self.active_actions_pub.publish(active_actions)
            
if __name__ == '__main__':
    pass
    #BehaviorTree(sys.argv[1])
    
    #Change the path to the config file you want to parse and then convert back
    #BehaviorTree("../../../behavior_executive/config/search_rescue3.tree")
    
    #For the test config file I included if in the same directory
    #BehaviorTree("config_filename.tree")

