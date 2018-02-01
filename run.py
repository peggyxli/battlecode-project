import battlecode as bc
import random
import sys
import traceback
import pathing
from math import floor
from math import sqrt

random.seed(6137)
gc = bc.GameController()
directions_with_center = list(bc.Direction)
directions = directions_with_center[:-1]
rotate_mods = [0, -1, 1, -2, 2, -3, 3, -4]
forward_mods = [0, -1, 1, -2, 2]
travel_directions = {}
my_paths = {}
nearby_enemies = {}
factory_loc = []
new_d = []
earth_karbonite_locations = []
pref_enemy_types = [bc.UnitType.Ranger, bc.UnitType.Mage, bc.UnitType.Healer]

my_team = gc.team()
if my_team == bc.Team.Blue:
    other_team = bc.Team.Red
else:
    other_team = bc.Team.Blue

earth_map = gc.starting_map(bc.Planet.Earth)
pathing.make_map(earth_map)
earth_center = bc.MapLocation(bc.Planet.Earth, floor(earth_map.width/2), floor(earth_map.height/2))
while pathing.earth_map[earth_center.x][earth_center.y] == -1:
    earth_center = earth_center.add(random.choice(directions))
earth_karbonite_locations = pathing.earth_karb_loc
max_workers = len(earth_karbonite_locations)/20
if max_workers < 8:
    max_workers = 8
elif max_workers > (earth_map.height + earth_map.width)/2:
    max_workers = (earth_map.height + earth_map.width)/2
    
mars_map = gc.starting_map(bc.Planet.Mars)
pathing.make_map(gc.starting_map(bc.Planet.Mars))
mars_center = bc.MapLocation(bc.Planet.Mars, pathing.mars_center[0], pathing.mars_center[1])
        
def move_fowards(unit_id):
    if unit_id not in travel_directions:
        travel_directions[unit_id] = random.choice(directions)
    d = travel_directions[unit_id]
    for mod in rotate_mods:
        if gc.can_move(unit_id, directions[(d+mod)%8]):
            gc.move_robot(unit_id, directions[(d+mod)%8])
            travel_directions[unit_id] = directions[(d+mod)%8]
            break
            
def move_along_path(unit):
    if gc.is_move_ready(unit.id):
        unit_loc = unit.location.map_location()
        if len(my_paths[unit.id]) == 0:
            d = random.choice(directions)
        elif my_paths[unit.id][-1].planet != unit_loc.planet:
            my_paths[unit.id].clear()
            d = random.choice(directions)
        else:
            d = unit_loc.direction_to(my_paths[unit.id][-1])
        
        for mod in forward_mods:
            if gc.can_move(unit.id, directions[(d+mod)%8]):
                gc.move_robot(unit.id, directions[(d+mod)%8])
                break
                
        if len(my_paths[unit.id]) > 0:
            if my_paths[unit.id][-1].distance_squared_to(unit.location.map_location()) < 3:
                my_paths[unit.id].pop()
            else:
                adjacent_spaces = list(gc.all_locations_within(unit_loc, 2))
                adjacent_spaces.remove(unit_loc)
                adjacent_spaces[:] = [space for space in adjacent_spaces if space in my_paths[unit.id]]
                if len(adjacent_spaces) > 0:
                    while len(adjacent_spaces) > 1:
                        if my_paths[unit.id][-1] in adjacent_spaces:
                            adjacent_spaces.remove(my_paths[unit.id][-1])
                        my_paths[unit.id].pop()
                    while not my_paths[unit.id][-1] in adjacent_spaces:
                        my_paths[unit.id].pop()                       

def find_closest_unit(unit, myarr):
    if len(myarr) > 0:
        loc = unit.location.map_location()
        closest_unit = myarr[0]
        closest_dist = 250
        for other in myarr:
            test_dist = loc.distance_squared_to(other.location.map_location()) 
            if test_dist < closest_dist:
                closest_unit = other
                closest_dist = test_dist
        return closest_unit
    return unit

def find_closest_loc(unit_loc, myarr):
    if len(myarr) > 0:
        closest_loc = myarr[0]
        closest_dist = 250
        for other_loc in myarr:
            test_dist = unit_loc.distance_squared_to(other_loc) 
            if test_dist < closest_dist:
                closest_loc = other_loc
                closest_dist = test_dist
        return closest_loc
    return unit_loc
    
def good_bp_loc(location):
    if not gc.starting_map(bc.Planet.Earth).is_passable_terrain_at(location):
        return False
    elif len(gc.sense_nearby_units_by_type(location, 2, bc.UnitType.Rocket)) > 0:
        return False
    elif len(gc.sense_nearby_units_by_type(location, 2, bc.UnitType.Factory)) > 0:
        return False
    else:
        more_spaces = gc.all_locations_within(location, 1)
        if len(more_spaces) < 5:
            return False
        else:
            for space2 in more_spaces:
                if not gc.starting_map(bc.Planet.Earth).is_passable_terrain_at(space2):
                    return False                
    return True

def worker_nearby(location):
    nearby_workers = gc.sense_nearby_units_by_type(location, 2, bc.UnitType.Worker)
    if len(nearby_workers) > 1:
        return True
    return False
    
def harvest_adj(unit): 
    for dir in directions_with_center:
        if gc.can_harvest(unit.id, dir):
            gc.harvest(unit.id, dir)
            travel_directions[unit.id] = dir
            return True
    return False
    
def find_most_missing(myarr):
    lowest_unit = myarr[0]
    most_missing = 0
    for other in myarr:
        missing_health = other.max_health - other.health
        if missing_health > most_missing:
            most_missing = missing_health
            lowest_unit = other
    return lowest_unit
    
def find_lowest(myarr):
    lowest_unit = myarr[0]
    for other in myarr:
        if other.health < lowest_unit.health:
            lowest_unit = other
    return lowest_unit

def find_path_to_center(unit):
    global earth_center, mars_center
    unit_loc = unit.location.map_location()
    if unit_loc.planet == bc.Planet.Earth:
        my_paths[unit.id] = pathing.find_path(unit_loc, earth_center)
    else:
        my_paths[unit.id] = pathing.find_path(unit_loc, mars_center)
    

#research
gc.queue_research(bc.UnitType.Worker)
gc.queue_research(bc.UnitType.Ranger)
gc.queue_research(bc.UnitType.Ranger)
gc.queue_research(bc.UnitType.Rocket)
gc.queue_research(bc.UnitType.Healer)
gc.queue_research(bc.UnitType.Mage)
gc.queue_research(bc.UnitType.Healer)
gc.queue_research(bc.UnitType.Mage)
gc.queue_research(bc.UnitType.Mage) #change later to add snipe
gc.queue_research(bc.UnitType.Worker)
gc.queue_research(bc.UnitType.Rocket)
gc.queue_research(bc.UnitType.Ranger)
gc.queue_research(bc.UnitType.Healer)

while True:
    #print('pyround:', gc.round(), 'time left:', gc.get_time_left_ms(), 'ms')
    vis_karb_locations = [loc for loc in earth_karbonite_locations if gc.can_sense_location(loc)]
    if len(vis_karb_locations) > 0:
        empty_karb_loc = [loc for loc in vis_karb_locations if gc.karbonite_at(loc) == 0]
        for loc in empty_karb_loc:
            vis_karb_locations.remove(loc)
            earth_karbonite_locations.remove(loc)
    
    my_units = [[] for x in range(len(bc.UnitType))]
    my_blueprints = []
    mars_rockets = []
    all_vis_enemies = []
    move_to_mars = False
    
    for unit in gc.my_units():
        if unit.location.is_on_map():
            unit_loc = unit.location.map_location()
            nearby_enemies[unit.id] = list(gc.sense_nearby_units_by_team(unit_loc, unit.vision_range, other_team))
            enemies_to_add = [enemy for enemy in nearby_enemies[unit.id] if enemy not in all_vis_enemies]
            all_vis_enemies.extend(enemies_to_add)
            
            if unit.unit_type == bc.UnitType.Factory:
                if unit.structure_is_built():
                    my_units[unit.unit_type].append(unit)
                else:
                    my_blueprints.append(unit)
            elif unit.unit_type == bc.UnitType.Rocket:
                if unit.location.is_on_planet(bc.Planet.Mars):
                    mars_rockets.append(unit)
                elif unit.structure_is_built():
                    my_units[unit.unit_type].append(unit)
                else:
                    my_blueprints.append(unit)
            else:
                if unit.id not in my_paths:
                    my_paths[unit.id] = []
                my_units[unit.unit_type].append(unit)
    
    if (gc.round() > 250 and len(all_vis_enemies) > 0) or gc.get_time_left_ms() < 2000:
        move_to_mars = True
    
    try:    #factory code
        for unit in my_units[bc.UnitType.Factory]:
            unit_loc = unit.location.map_location()
            garrison = unit.structure_garrison()
            if len(garrison) > 0:
                for d in directions:
                    if gc.can_unload(unit.id, d):
                        gc.unload(unit.id, d)
                        break
            
            if len(my_units[bc.UnitType.Worker]) < 8 and gc.can_produce_robot(unit.id, bc.UnitType.Worker):
                gc.produce_robot(unit.id, bc.UnitType.Worker)
            elif not move_to_mars:
                if len(my_units[bc.UnitType.Ranger]) <= len(my_units[bc.UnitType.Healer])*4 and gc.can_produce_robot(unit.id, bc.UnitType.Ranger):
                    gc.produce_robot(unit.id, bc.UnitType.Ranger)
                elif len(my_units[bc.UnitType.Healer]) <= len(my_units[bc.UnitType.Mage]) and gc.can_produce_robot(unit.id, bc.UnitType.Healer):
                    gc.produce_robot(unit.id, bc.UnitType.Healer)
                elif gc.can_produce_robot(unit.id, bc.UnitType.Mage):
                    gc.produce_robot(unit.id, bc.UnitType.Mage)            
    except Exception as e:
        print('Factory Error:', e)				
        traceback.print_exc()            
    
    
    try:    #mars rocket code
        for unit in mars_rockets:
            garrison = unit.structure_garrison()
            if len(garrison) > 0:
                for friend in garrison:
                    for dir in directions:
                        if gc.can_unload(unit.id, dir):
                            gc.unload(unit.id, dir)
                            break
    except Exception as e:
        print('Rocket Error:', e)				
        traceback.print_exc()   
    
    
    try:    #worker code
        for unit in my_units[bc.UnitType.Worker]:
            unit_loc = unit.location.map_location()            
            if unit_loc.planet == bc.Planet.Earth:
                keep_moving = True
                harvest_stuff = True
                if len(my_units[bc.UnitType.Worker]) < max_workers:
                    for dir in directions:
                        if gc.can_replicate(unit.id, dir):
                            gc.replicate(unit.id, dir)
                            break
                
                #build nearby blueprints first
                nearby_blueprints = [bp for bp in my_blueprints if unit_loc.distance_squared_to(bp.location.map_location()) < 20]
                if len(nearby_blueprints) > 0:
                    my_bp = find_closest_unit(unit, nearby_blueprints)
                    if gc.can_build(unit.id, my_bp.id):
                        gc.build(unit.id, my_bp.id)
                        keep_moving = False
                    else:
                        nearby_workers = gc.sense_nearby_units_by_type(my_bp.location.map_location(), 2, bc.UnitType.Worker)
                        if len(nearby_workers) < 4:
                            target_loc = my_bp.location.map_location()
                            my_paths[unit.id] = pathing.find_path(unit_loc, target_loc)
                            harvest_stuff = False
                
                #then try to blueprint
                elif gc.karbonite() > bc.UnitType.Factory.blueprint_cost():
                    adjacent_spaces = list(gc.all_locations_within(unit_loc, 2))
                    adjacent_spaces.remove(unit_loc)
                    adjacent_spaces[:] = [space for space in adjacent_spaces if good_bp_loc(space) and gc.is_occupiable(space)]
                  
                    if len(adjacent_spaces) > 0:
                        spaces_near_worker = [space for space in adjacent_spaces if worker_nearby(space)]
                        if len(spaces_near_worker) > 0:
                            bp_space = random.choice(spaces_near_worker)
                        else:
                            bp_space = random.choice(adjacent_spaces)
                            
                        if len(my_units[bc.UnitType.Factory]) + len(my_blueprints) < 5:
                            if gc.can_blueprint(unit.id, bc.UnitType.Factory, unit_loc.direction_to(bp_space)):
                                gc.blueprint(unit.id, bc.UnitType.Factory, unit_loc.direction_to(bp_space))
                                keep_moving = False
                        elif gc.research_info().get_level(bc.UnitType.Rocket) > 0:
                            if gc.can_blueprint(unit.id, bc.UnitType.Rocket, unit_loc.direction_to(bp_space)):
                                gc.blueprint(unit.id, bc.UnitType.Rocket, unit_loc.direction_to(bp_space))
                                keep_moving = False
                
                #then try to harvest            
                if harvest_stuff and keep_moving:   #priority: adjacent, visible, then known
                    for dir in directions_with_center:
                        if gc.can_harvest(unit.id, dir):
                            gc.harvest(unit.id, dir)
                            keep_moving = False
                            break
                    
                    if keep_moving and len(my_paths[unit.id]) == 0:
                        if len(vis_karb_locations) > 0:
                            target_loc = find_closest_loc(unit_loc, vis_karb_locations)
                            my_paths[unit.id] = pathing.find_path(unit_loc, target_loc)
                        elif len(earth_karbonite_locations) > 0:
                            target_loc = find_closest_loc(unit_loc, earth_karbonite_locations)
                            my_paths[unit.id] = pathing.find_path(unit_loc, target_loc)
                    
                if keep_moving and gc.is_move_ready(unit.id):
                    harvest_adj(unit)
                    move_along_path(unit)
            
            elif not harvest_adj(unit) and gc.is_move_ready(unit.id):
                move_fowards(unit.id)
    except Exception as e:
        print('Worker Error:', e)				
        traceback.print_exc()
    
    # try:    #knight code
        # for unit in my_units[bc.UnitType.Knight]:
            # unit_loc = unit.location.map_location()
            # for enemy in nearby_enemies[unit.id]:
                # if gc.is_attack_ready(unit.id) and gc.can_attack(unit.id, enemy.id):
                    # gc.attack(unit.id, enemy.id)
                    # break
            # if gc.is_move_ready(unit.id):
                # nearby_friends = gc.sense_nearby_units_by_team(unit_loc, 1, my_team)
                # for friend in nearby_friends:
                    # if (friend.unit_type == bc.UnitType.Knight) and (friend.id != unit.id): #spread out
                        # travel_directions[unit.id] = friend.location.map_location().direction_to(unit_loc)
                        # move_fowards(unit.id)
                        # break                        
    # except Exception as e:
        # print('Knight Error:', e)				
        # traceback.print_exc()
                        
    try:    #ranger code
        for unit in my_units[bc.UnitType.Ranger]:
            unit_loc = unit.location.map_location()
            keep_moving = True
            
            if len(nearby_enemies[unit.id]) > 0:
                if gc.is_attack_ready(unit.id):
                    attackable_enemies = [enemy for enemy in nearby_enemies[unit.id] if gc.can_attack(unit.id, enemy.id)]
                    if len(attackable_enemies) > 0:
                        lowest_enemy = find_lowest(attackable_enemies)
                        gc.attack(unit.id, lowest_enemy.id)
                        keep_moving = False
                if keep_moving and gc.is_move_ready(unit.id):
                    closest_enemy = find_closest_unit(unit, nearby_enemies[unit.id])
                    if unit_loc.distance_squared_to(closest_enemy.location.map_location()) < 11:    #move backwards to be in range
                        travel_directions[unit.id] = closest_enemy.location.map_location().direction_to(unit_loc)
                        move_fowards(unit.id)
                    else:   #move closer
                        my_paths[unit.id] = pathing.find_path(unit_loc, closest_enemy.location.map_location())
                        move_along_path(unit)
                        
                    if gc.is_attack_ready(unit.id):
                        attackable_enemies = [enemy for enemy in nearby_enemies[unit.id] if gc.can_attack(unit.id, enemy.id)]
                        if len(attackable_enemies) > 0:
                            pref_enemies = [enemy for enemy in attackable_enemies if enemy.unit_type in pref_enemy_types]
                            if len(pref_enemies) > 0:
                                lowest_enemy = find_lowest(pref_enemies)
                            else:
                                lowest_enemy = find_lowest(attackable_enemies)
                            gc.attack(unit.id, lowest_enemy.id)
                            keep_moving = False
                        
            elif gc.is_move_ready(unit.id):
                if len(my_paths[unit.id]) == 0:
                    if len(all_vis_enemies) > 0:
                        closest_enemy = find_closest_unit(unit, all_vis_enemies)
                        my_paths[unit.id] = pathing.find_path(unit_loc, closest_enemy.location.map_location())
                    else:
                        find_path_to_center(unit)
                move_along_path(unit)
    except Exception as e:
        print('Ranger Error:', e)				
        traceback.print_exc()
    
    try:    #healer code
        for unit in my_units[bc.UnitType.Healer]:
            unit_loc = unit.location.map_location()
            
            nearby_friends = list(gc.sense_nearby_units_by_team(unit_loc, unit.vision_range, my_team))
            nearby_friends[:] = [friend for friend in nearby_friends if friend.health < friend.max_health]
            if unit in nearby_friends:
                nearby_friends.remove(unit)
                
            if gc.is_heal_ready(unit.id) and len(nearby_friends) > 0:
                healable_friends = [friend for friend in nearby_friends if gc.can_heal(unit.id, friend.id)]
                if len(healable_friends) > 0:
                    lowest_friend = find_most_missing(healable_friends)
                    gc.heal(unit.id, lowest_friend.id)
                        
            if gc.is_move_ready(unit.id):
                if len(my_paths[unit.id]) == 0:
                    if len(nearby_friends) > 0:        
                        lowest_friend = find_most_missing(nearby_friends)
                        my_paths[unit.id] = pathing.find_path(unit_loc, lowest_friend.location.map_location())
                    else:
                        front_line = [friend for friend in my_units[bc.UnitType.Ranger] if friend.health < friend.max_health or len(nearby_enemies[friend.id]) > 0]
                        if len(front_line) > 0:
                            lowest_friend = find_most_missing(front_line)
                            my_paths[unit.id] = pathing.find_path(unit_loc, lowest_friend.location.map_location())
                        else:
                            find_path_to_center(unit)
                move_along_path(unit)
    except Exception as e:
        print('Healer Error:', e)				
        traceback.print_exc()
          
    try:    #mage code
        for unit in my_units[bc.UnitType.Mage]:
            unit_loc = unit.location.map_location()
            nearby_enemies[unit.id][:] = [enemy for enemy in nearby_enemies[unit.id] if gc.can_sense_unit(enemy.id)]
            
            if len(nearby_enemies[unit.id]) > 0:
                if gc.is_attack_ready(unit.id):
                    lowest_enemy = find_lowest(nearby_enemies[unit.id])
                    gc.attack(unit.id, lowest_enemy.id)
                    
                if gc.is_move_ready(unit.id):
                    nearby_friends = gc.sense_nearby_units_by_team(unit_loc, unit.vision_range, my_team) 
                    closest_enemy = find_closest_unit(unit, nearby_enemies[unit.id])
                    if len(nearby_enemies[unit.id]) > len(nearby_friends):    
                        travel_directions[unit.id] = closest_enemy.location.map_location().direction_to(unit_loc)
                        move_fowards(unit.id)
                    else:
                        my_paths[unit.id] = pathing.find_path(unit_loc, closest_enemy.location.map_location())
                        move_along_path(unit)
                        
            elif gc.is_move_ready(unit.id):
                if len(my_paths[unit.id]) == 0:
                    if len(all_vis_enemies) > 0:
                        closest_enemy = find_closest_unit(unit, all_vis_enemies)
                        my_paths[unit.id] = pathing.find_path(unit_loc, closest_enemy.location.map_location())
                    else:
                        find_path_to_center(unit)
                move_along_path(unit)
    except Exception as e:
        print('Mage Error:', e)				
        traceback.print_exc()
        
    
    try:    #earth rocket code
        for unit in my_units[bc.UnitType.Rocket]:
            unit_loc = unit.location.map_location()
            garrison = unit.structure_garrison()
            if len(garrison) < unit.structure_max_capacity():
                nearby_friends = gc.sense_nearby_units_by_team(unit_loc, 2, my_team)
                for friend in nearby_friends:
                    if gc.can_load(unit.id, friend.id) and len(garrison) < unit.structure_max_capacity():
                        gc.load(unit.id, friend.id)
                        my_paths[friend.id] = []
            if len(garrison) == unit.structure_max_capacity() or gc.round() == 725 or unit.health < unit.max_health:
                destination = random.choice(pathing.mars_spaces)
                if gc.can_launch_rocket(unit.id, bc.MapLocation(bc.Planet.Mars, destination[0], destination[1])):
                    gc.launch_rocket(unit.id, bc.MapLocation(bc.Planet.Mars, destination[0], destination[1]))
    except Exception as e:
        print('Rocket Error:', e)				
        traceback.print_exc()    
    
        
    # send the actions we've performed, and wait for our next turn.
    gc.next_turn()
    sys.stdout.flush()
    sys.stderr.flush()
