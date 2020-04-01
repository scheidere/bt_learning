
from world import distance

class SensorModel():
    def __init__(self, config, num_vertices, world):
        self.config = config
        self.sensor_range = self.config["sensor_range"]
        self.num_vertices = num_vertices
        self.world = world

    def all_likelihoods(self, x, y):
        ## P(Z|Y)
        likelihoods = []
        for z in xrange(self.num_vertices):
            # distance from robot to z
            d = distance(self.world.vertices[x],self.world.vertices[z])

            # before normalization
            if d < self.sensor_range:
                if z == y:
                    p = 0.95 - 0.01*d #f
                else:
                    p = 0.2 #g
                #p_none = 1 - p_correct #1-f
            else:
                p = 0
                #p_none = 1
            likelihoods.append(p)

        likelihoods.append(0.8) #none case: ~80% (before normalization) doesnt think it sees target

        # Normalize
        norm = sum(likelihoods) #same as 1 + p_false
        for i in xrange(len(likelihoods)):
            likelihoods[i] = likelihoods[i]/norm

        return likelihoods 
