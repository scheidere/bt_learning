
from world import distance
import numpy as np

class SensorModel():
    def __init__(self, config, num_vertices, world):
        self.config = config
        self.sensor_range = self.config["sensor_range"]
        self.num_vertices = num_vertices
        self.world = world
        self.precompute_distances()

    def precompute_distances(self):
        self.distances = np.zeros([self.num_vertices,self.num_vertices])
        for x in xrange(self.num_vertices):
            for y in xrange(self.num_vertices):
                self.distances[x][y] = distance(self.world.vertices[x],self.world.vertices[y])

    def all_likelihoods(self, x, y):
        ## P(Z|Y)
        likelihoods = []
        for z in xrange(self.num_vertices):
            # distance from robot to z
            # d = distance(self.world.vertices[x],self.world.vertices[z])
            d = self.distances[x][z]

            # before normalization
            if d < self.sensor_range:
                if z == y:
                    p = 0.95 - (0.95/self.sensor_range)*d #f 
                else:
                    p = 0.05 #g
                #p_none = 1 - p_correct #1-f
            else:
                p = 0
                #p_none = 1
            likelihoods.append(p)

        likelihoods.append(0.8) #none case: ~80% (before normalization) doesnt think it sees target

        # Normalize
        norm = sum(likelihoods) #same as 1 + p_false
        for i in xrange(len(likelihoods)):
            likelihoods[i] /= norm

        return likelihoods 
