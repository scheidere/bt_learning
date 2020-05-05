
from distance import distance
import numpy as np

class SensorModel():
    def __init__(self, config, num_vertices, world):
        self.config = config
        self.sensor_range = self.config["sensor_range"]
        self.num_classes = self.config["num_classes"]
        self.num_vertices = num_vertices
        self.world = world
        self.TP = self.config["TP"]
        self.precompute_distances()
        # self.precompute_all_likelihoods()
        self.init_all_likelihoods()

    
    def precompute_distances(self):
        self.distances = np.zeros([self.num_vertices,self.num_vertices])
        for x in xrange(self.num_vertices):
            for y in xrange(self.num_vertices):
                self.distances[x][y] = distance(self.world.vertices[x],self.world.vertices[y])
    
    '''
    def all_likelihoods(self, x, y):
        if self.precompute_likelihoods[x][y] is None: #if the likelihood hasn't be computed for this target
            self.compute_all_likelihoods(x, y) #compute likelihood
        return self.precompute_likelihoods[x][y]
    '''

    def init_all_likelihoods(self): ### Check size
        self.precompute_likelihoods = [None] * self.num_vertices
        for i in xrange(self.num_vertices):
            self.precompute_likelihoods[i] = [None] * self.num_vertices

    '''
    def precompute_all_likelihoods(self):
        self.precompute_likelihoods = [[None] * self.num_vertices] * self.num_vertices
        for x in xrange(self.num_vertices): 
            for y in xrange(self.num_vertices): 
                self.precompute_likelihoods[x][y] = self.compute_all_likelihoods(x,y)
    '''

    '''
    def compute_all_likelihoods(self, x, y):
        ## P(Z|Y)
        likelihoods = np.zeros(self.num_vertices+1)
        sensor_range = self.sensor_range
        for z in xrange(self.num_vertices):
            # distance from robot to z
            # d = distance(self.world.vertices[x],self.world.vertices[z])
            d = self.distances[x][z]

            # before normalization
            if d < sensor_range:
                if z == y:
                    p = 0.95 - (0.95/sensor_range)*d #f 
                else:
                    p = 0.05 #g
                #p_none = 1 - p_correct #1-f
            else:
                p = 0
                #p_none = 1
            likelihoods[z] = p

        likelihoods[-1] = 0.8 #none case: ~80% (before normalization) doesnt think it sees target

        # Normalize
        norm = sum(likelihoods) #same as 1 + p_false
        likelihoods /= norm

        self.precompute_likelihoods[x][y] = likelihoods
        # return likelihoods 
    '''

    def all_likelihoods(self, y):
        likelihoods = np.array([])
        for z in xrange(self.world.num_classes):
            likelihoods = np.append(likelihoods, self.compute_single_likelihood(y,z))
        return likelihoods

    def compute_single_likelihood(self, y, z):
        '''
        Input: the class of v (y), single observation (z)
        Output: Single likelihood
        Question: don't need v?
        '''
        if z == y: #at v
            p = self.TP
        else:
            p = (1 - self.TP)/(self.world.num_classes - 1)

        likelihood = p
        return likelihood

    '''
    def compute_all_likelihoods(self, x, y_array):
        
        #Input: robot location (x), classes for each vertex (y_array)
        #Output: P(Z|Y), likelihood for all possible classes at every vertex in sensor range
        #Question: y_array still confusing, how to have it not be ground truth
         

        likelihoods = np.zeros((self.num_vertices,self.world.num_classes))
        sensor_range = self.sensor_range
        for v in xrange(self.num_vertices):
            # For every vertex in sensor range
            if self.distances[x][v] < sensor_range:
                # Loop through possible observations (i.e. classes)
                for z in xrange(self.world.num_classes):
                    likelihood_p = compute_single_likelihood(y_array[v],z) 
                    likelihoods[v][z] = likelihood_p
                    #self.precompute_likelihoods[x][v][z] = likelihoods


        
        likelihoods = np.zeros((self.num_vertices,self.world.num_classes))
        sensor_range = self.sensor_range
        for v in xrange(self.num_vertices):
            # For every vertex in sensor range
            if self.distances[x][v] < sensor_range:
                # Loop through possible observations (i.e. classes)
                for z in xrange(self.world.num_classes):
                    # If observation is correct
                    if z == self.world.classes_y[v]:
                        p = self.TP
                    # If observation is incorrect
                    else:
                        p = (1 - self.TP)/(self.world.num_classes - 1)
                likelihoods[v][z] = p

                self.precompute_likelihoods[x][v][z] = likelihoods
        '''

