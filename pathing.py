import battlecode as bc
from heapq import *


my_map = []
closed_nodes = []
width = 0
height = 0
planet = bc.Planet.Earth


class Node:
    def __init__ (self, myX = 0, myY = 0, end_loc = bc.MapLocation(bc.Planet.Earth, 0, 0), new_index = -1):
        self.x = myX
        self.y = myY
        self.parent_index = new_index
        if self.parent_index != -1:
            parent_node = closed_nodes[self.parent_index]
            self.distance_from_start = parent_node.distance_from_start
            self.distance_from_start += (parent_node.x-self.x)**2 + (parent_node.y-self.y)**2
        else:
            self.distance_from_start = 0
        self.cost = self.distance_from_start + (end_loc.x-self.x)**2 + (end_loc.y-self.y)**2
        
    def __lt__ (self, other):
        return self.cost < other.cost
        

def make_map(planet_map):
    global my_map, width, height, planet
    width = planet_map.width
    height = planet_map.height
    planet = planet_map.planet
    my_map = [[0 for x in range(width)] for y in range(height)]
    test_location = bc.MapLocation(planet, 0, 0)
    while test_location.y < height:
        while test_location.x < width:
            if not planet_map.is_passable_terrain_at(test_location):
                my_map[test_location.x][test_location.y] = -1
            test_location = test_location.add(bc.Direction.East)
        test_location = bc.MapLocation(planet, 0, test_location.y+1)

    
def find_path(start_loc, end_loc):
    global closed_nodes
    temp_map = [row[:] for row in my_map]
    my_node = Node(start_loc.x, start_loc.y, end_loc)
    open_nodes = []
    my_nodes = []
    
    while my_node.x != end_loc.x or my_node.y != end_loc.y:
        closed_nodes.append(my_node)
        my_index = len(closed_nodes)-1
        temp_map[my_node.x][my_node.y] = -2
        
        for j in range(my_node.y-1, my_node.y+2):
            if j >= 0 and j < height:
                for i in range(my_node.x-1, my_node.x+2):
                    if i >= 0 and i < width:
                        if(temp_map[i][j] == 0):
                            heappush(open_nodes, Node(i, j, end_loc, my_index))
                            
        while temp_map[open_nodes[0].x][open_nodes[0].y] != 0 and len(open_nodes) > 0:
            heappop(open_nodes)
        if len(open_nodes) == 0:
            print("No path could be found")
            return my_nodes
        else:
            my_node = heappop(open_nodes)
    
    while my_node.parent_index != -1:
        my_nodes.append(bc.MapLocation(planet, my_node.x, my_node.y))
        my_node = closed_nodes[my_node.parent_index]
    my_nodes.reverse()
    return my_nodes