from math import sqrt

def distance(vertex_start, vertex_end):
    # Euclidean distance, for now
    #return ( (vertex_start.position.x-vertex_end.position.x)**2 + (vertex_start.position.y-vertex_end.position.y)**2 + (vertex_start.position.z-vertex_end.position.z)**2)**0.5
    x = (vertex_start.position.x-vertex_end.position.x)
    y = (vertex_start.position.y-vertex_end.position.y)
    z = (vertex_start.position.z-vertex_end.position.z)
    return sqrt( x*x + y*y + z*z )