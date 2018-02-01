import battlecode as bc
from heapq import *
from math import floor


earth_map = []
earth_dim = (0,0)
earth_karb_loc = []
mars_map = []
mars_dim = (0,0)
mars_center = (0,0)
mars_spaces = []
closed_nodes = []


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
        
    def __eq__ (self, other):
        return (self.x == other.x and self.y == other.y)
        
    def __ne__ (self, other):
        return (self.x != other.x or self.y != other.y)

        
def fill_inaccessible(planet_map):
    global earth_map, mars_map
    width = planet_map.width
    height = planet_map.height
    if planet_map.planet == bc.Planet.Earth:
        temp_map = [row[:] for row in earth_map]    
    else:
        temp_map = [row[:] for row in mars_map]
    
    border_spaces = []
    my_units = planet_map.initial_units
    for unit in my_units:
        unit_loc = unit.location.map_location()
        temp_map[unit_loc.x][unit_loc.y] = -2
        border_spaces.append((unit_loc.x, unit_loc.y))
                    
    while len(border_spaces) > 0:
        new_spaces = []
        for space in border_spaces:
            for j in range(space[1]-1, space[1]+2):
                if j >= 0 and j < height:
                    for i in range(space[0]-1, space[0]+2):
                        if i >= 0 and i < width:
                            if(temp_map[i][j] == 0):
                                temp_map[i][j] = -2
                                new_spaces.append((i,j))
        border_spaces = new_spaces[:]
    
    if planet_map.planet == bc.Planet.Earth:
        for j in range(height):
            for i in range(width):
                if temp_map[i][j] == 0:
                    earth_map[i][j] = -1
    else:
        for j in range(height):
            for i in range(width):
                if temp_map[i][j] == 0:
                    mars_map[i][j] = -1
                

def fill_non_contiguous(my_map, width, height):
    global mars_center, mars_spaces
    temp_map = [row[:] for row in my_map]
    all_spaces = []
    contiguous_spaces = []
    
    for j in range(height):
        for i in range(width):
            if temp_map[i][j] == 0:
                all_spaces.append((i, j))
                
    while len(all_spaces) > 0:
        new_contiguous = [all_spaces[-1]]
        border_spaces = new_contiguous[:]
        temp_map[all_spaces[-1][0]][all_spaces[-1][1]] = -2
                        
        while len(border_spaces) > 0:
            new_spaces = []
            for space in border_spaces:
                for j in range(space[1]-1, space[1]+2):
                    if j >= 0 and j < height:
                        for i in range(space[0]-1, space[0]+2):
                            if i >= 0 and i < width:
                                if(temp_map[i][j] == 0):
                                    temp_map[i][j] = -2
                                    new_spaces.append((i,j))
            border_spaces = new_spaces[:]
            new_contiguous.extend(border_spaces)
        
        for space in new_contiguous:
            all_spaces.remove(space)
        contiguous_spaces.append(new_contiguous)
    
    max_space = contiguous_spaces[0]    
    for space in contiguous_spaces:
        if len(space) > len(max_space):
            max_space = space
            
    for space in max_space:
        temp_map[space[0]][space[1]] = 0
        
    for j in range(height):
        for i in range(width):
            if temp_map[i][j] == -2:
                my_map[i][j] = -1
                
    max_space.sort()
    mars_center = max_space[floor(len(max_space)/2)]
    mars_spaces = max_space
    
def make_map(planet_map):
    global earth_map, earth_dim, earth_karb_loc, mars_map, mars_dim
    planet = planet_map.planet
    
    if planet == bc.Planet.Earth:
        earth_dim = (planet_map.width, planet_map.height)
        earth_map = [[0 for y in range(planet_map.height)] for x in range(planet_map.width)]
        
        test_location = bc.MapLocation(planet, 0, 0)
        while test_location.y < planet_map.height:
            while test_location.x < planet_map.width:
                if not planet_map.is_passable_terrain_at(test_location):
                    earth_map[test_location.x][test_location.y] = -1
                test_location = test_location.add(bc.Direction.East)
            test_location = bc.MapLocation(planet, 0, test_location.y+1)
        fill_inaccessible(planet_map)
        
        for j in range(planet_map.height):
            for i in range(planet_map.width):
                if earth_map[i][j] != -1:
                    test_location = bc.MapLocation(bc.Planet.Earth, i, j)
                    if planet_map.initial_karbonite_at(test_location) > 0:
                        earth_karb_loc.append(test_location)
    
    elif planet == bc.Planet.Mars:
        mars_dim = (planet_map.width, planet_map.height)
        mars_map = [[0 for y in range(planet_map.height)] for x in range(planet_map.width)]
        test_location = bc.MapLocation(planet, 0, 0)
        while test_location.y < planet_map.height:
            while test_location.x < planet_map.width:
                if not planet_map.is_passable_terrain_at(test_location):
                    mars_map[test_location.x][test_location.y] = -1
                test_location = test_location.add(bc.Direction.East)
            test_location = bc.MapLocation(planet, 0, test_location.y+1)
        fill_non_contiguous(mars_map, planet_map.width, planet_map.height)
            
def find_path(start_loc, end_loc):
    my_nodes = []
    if start_loc.planet != end_loc.planet:
        return my_nodes
    
    global closed_nodes
    my_node = Node(start_loc.x, start_loc.y, end_loc)
    open_nodes = []
    
    planet = start_loc.planet
    if planet == bc.Planet.Earth:
        if earth_map[end_loc.x][end_loc.y] != 0:
            return my_nodes
        temp_map = [row[:] for row in earth_map]
        width = earth_dim[0]
        height = earth_dim[1]
    else:
        if end_loc.x >= mars_dim[0] or end_loc.y >= mars_dim[1]:
            return my_nodes
        elif end_loc.x < 0 or end_loc.y < 0:
            return my_nodes
        elif mars_map[end_loc.x][end_loc.y] != 0:
            return my_nodes
        temp_map = [row[:] for row in mars_map]
        width = mars_dim[0]
        height = mars_dim[1]
    
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
                            
        while len(open_nodes) > 0:
            if temp_map[open_nodes[0].x][open_nodes[0].y] == 0:
                break
            else:
                temp_node = heappop(open_nodes)
                
        if len(open_nodes) == 0:
            print("No path could be found")
            print("unit loc:", start_loc)
            print("target loc:", end_loc)
            return my_nodes
        else:
            my_node = heappop(open_nodes)
    
    while my_node.parent_index != -1:
        my_nodes.append(bc.MapLocation(planet, my_node.x, my_node.y))
        my_node = closed_nodes[my_node.parent_index]
    
    closed_nodes.clear()
    return my_nodes