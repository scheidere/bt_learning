
from world import distance
import numpy as np

class SensorModel():
    def __init__(self, config, num_vertices, world):
        self.config = config
        self.sensor_range = self.config["sensor_range"]
        self.num_vertices = num_vertices
        self.world = world
        self.precompute_distances()
        # self.precompute_all_likelihoods()
        self.init_all_likelihoods()

    def precompute_distances(self):
        self.distances = np.zeros([self.num_vertices,self.num_vertices])
        for x in xrange(self.num_vertices):
            for y in xrange(self.num_vertices):
                self.distances[x][y] = distance(self.world.vertices[x],self.world.vertices[y])

    def all_likelihoods(self, x, y):
        if self.precompute_likelihoods[x][y] is None:
            self.compute_all_likelihoods(x, y)
        return self.precompute_likelihoods[x][y]

    def init_all_likelihoods(self):
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
