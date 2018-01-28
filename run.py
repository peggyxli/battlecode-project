import battlecode as bc
import random
import sys
import traceback
import pathing

random.seed(6137)
gc = bc.GameController()
directions = list(bc.Direction)
rotate_mods = [0, -1, 1, -2, 2, -3, 3, -4]
travel_directions = {}
my_paths = {}
nearby_enemies = {}
factory_loc = []
new_d = []
earth_karbonite_locations = []

my_team = gc.team()
if my_team == bc.Team.Blue:
    other_team = bc.Team.Red
else:
    other_team = bc.Team.Blue

earth_map = gc.starting_map(bc.Planet.Earth)
pathing.make_map(earth_map)
pathing.make_map(gc.starting_map(bc.Planet.Mars))

test_location = bc.MapLocation(bc.Planet.Earth, 0, 0)
while test_location.y < earth_map.height:
    while test_location.x < earth_map.width:
        if earth_map.initial_karbonite_at(test_location) > 0:
            earth_karbonite_locations.append(test_location)
        test_location = test_location.add(bc.Direction.East)
    test_location = bc.MapLocation(bc.Planet.Earth, 0, test_location.y+1)

print (len(earth_karbonite_locations))
        
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
    unit_loc = unit.location.map_location()
    if len(my_paths[unit.id]) == 0:
        d = random.choice(directions)
    elif my_paths[unit.id][-1].planet != unit_loc.planet:
        my_paths[unit.id].clear()
        d = random.choice(directions)
    else:
        d = unit_loc.direction_to(my_paths[unit.id][-1])
    
    for mod in rotate_mods:
        if gc.can_move(unit.id, directions[(d+mod)%8]):
            gc.move_robot(unit.id, directions[(d+mod)%8])
            break
            
    if unit.id in my_paths:
        if len(my_paths[unit.id]) > 0:
            if unit.location.map_location() == my_paths[unit.id][-1]:
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
    for dir in directions:
        if gc.can_harvest(unit.id, dir):
            gc.harvest(unit.id, dir)
            travel_directions[unit.id] = dir
            return True
    return False
    
def find_adj_karb(unit_loc): 
    adj_spaces = gc.all_locations_within(unit_loc, 2)
    for space in adj_spaces:
        if gc.karbonite_at(space) > 0:
            return space
    return unit_loc
    
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
    print('pyround:', gc.round(), 'time left:', gc.get_time_left_ms(), 'ms')
    vis_karb_locations = [loc for loc in earth_karbonite_locations if gc.can_sense_location(loc)]
    if len(vis_karb_locations) > 0:
        empty_karb_loc = [loc for loc in vis_karb_locations if gc.karbonite_at(loc) == 0]
        for loc in empty_karb_loc:
            vis_karb_locations.remove(loc)
            earth_karbonite_locations.remove(loc)
    
    
    while len(factory_loc) > 0: #adding travel directions to new units
        new_location = factory_loc[0].add(new_d[0])
        factory_loc.pop(0)
        if gc.has_unit_at_location(new_location):
            new_unit = gc.sense_unit_at_location(new_location)
            travel_directions[new_unit.id] = new_d[0] 
        new_d.pop(0)
    
    
    my_units = [[] for x in range(len(bc.UnitType))]
    my_blueprints = []
    mars_rockets = []
    enemy_locations = []
    all_vis_enemies = []
    
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
    
    try:    #factory code
        for unit in my_units[bc.UnitType.Factory]:
            unit_loc = unit.location.map_location()
            garrison = unit.structure_garrison()
            if len(garrison) > 0:
                for d in directions:
                    if gc.can_unload(unit.id, d):
                        gc.unload(unit.id, d)
                        factory_loc.append(unit_loc)
                        new_d.append(d)
                        break
            
            if len(my_units[bc.UnitType.Worker]) < 8 and gc.can_produce_robot(unit.id, bc.UnitType.Worker):
                gc.produce_robot(unit.id, bc.UnitType.Worker)
            elif gc.round() < 250 or len(all_vis_enemies) > 0:
                if len(my_units[bc.UnitType.Ranger]) <= len(my_units[bc.UnitType.Healer])*4 and gc.can_produce_robot(unit.id, bc.UnitType.Ranger):
                    gc.produce_robot(unit.id, bc.UnitType.Ranger)
                elif len(my_units[bc.UnitType.Healer]) <= len(my_units[bc.UnitType.Mage]) and gc.can_produce_robot(unit.id, bc.UnitType.Healer):
                    gc.produce_robot(unit.id, bc.UnitType.Healer)
                elif gc.can_produce_robot(unit.id, bc.UnitType.Mage):
                    gc.produce_robot(unit.id, bc.UnitType.Mage)            
    except Exception as e:
        print('Factory Error:', e)				
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
            if len(garrison) == unit.structure_max_capacity() or gc.round() == 740:
                maxX = gc.starting_map(bc.Planet.Mars).width - 1
                maxY = gc.starting_map(bc.Planet.Mars).height - 1
                testX = random.randint(0, maxX)
                testY = random.randint(0, maxY)
                while not gc.can_launch_rocket(unit.id, bc.MapLocation(bc.Planet.Mars, testX, testY)):
                    testX = random.randint(0, maxX)
                    testY = random.randint(0, maxY)
                gc.launch_rocket(unit.id, bc.MapLocation(bc.Planet.Mars, testX, testY))
    except Exception as e:
        print('Rocket Error:', e)				
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
                if len(my_units[bc.UnitType.Worker]) < 8 or len(my_units[bc.UnitType.Worker]) < len(earth_karbonite_locations)/20:
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
                    target_loc = find_adj_karb(unit_loc)
                    if gc.karbonite_at(target_loc) != 0:    #if there is karbonite at an adjacent space
                        if gc.can_harvest(unit.id, unit_loc.direction_to(target_loc)):
                            gc.harvest(unit.id, unit_loc.direction_to(target_loc))
                        keep_moving = False
                    elif len(vis_karb_locations) > 0:
                        target_loc = find_closest_loc(unit_loc, vis_karb_locations)
                        my_paths[unit.id] = pathing.find_path(unit_loc, target_loc)
                        while len(my_paths[unit.id]) == 0 and len(vis_karb_locations) > 0:
                            print(unit_loc, "no path to vis", target_loc)
                            vis_karb_locations.remove(target_loc)
                            earth_karbonite_locations.remove(target_loc)
                            target_loc = find_closest_loc(unit_loc, vis_karb_locations)
                            my_paths[unit.id] = pathing.find_path(unit_loc, target_loc)
                    elif len(earth_karbonite_locations) > 0:
                        target_loc = find_closest_loc(unit_loc, earth_karbonite_locations)
                        my_paths[unit.id] = pathing.find_path(unit_loc, target_loc)
                        while len(my_paths[unit.id]) == 0 and len(earth_karbonite_locations) > 0:
                            print("no path to global", target_loc)
                            earth_karbonite_locations.remove(target_loc)
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
    
    try:    #knight code
        for unit in my_units[bc.UnitType.Knight]:
            unit_loc = unit.location.map_location()
            for enemy in nearby_enemies[unit.id]:
                if gc.is_attack_ready(unit.id) and gc.can_attack(unit.id, enemy.id):
                    gc.attack(unit.id, enemy.id)
                    break
            if gc.is_move_ready(unit.id):
                nearby_friends = gc.sense_nearby_units_by_team(unit_loc, 1, my_team)
                for friend in nearby_friends:
                    if (friend.unit_type == bc.UnitType.Knight) and (friend.id != unit.id): #spread out
                        travel_directions[unit.id] = friend.location.map_location().direction_to(unit_loc)
                        move_fowards(unit.id)
                        break                        
    except Exception as e:
        print('Knight Error:', e)				
        traceback.print_exc()
                        
    try:    #ranger code
        for unit in my_units[bc.UnitType.Ranger]:
            unit_loc = unit.location.map_location()
            keep_moving = True
            
            if len(nearby_enemies[unit.id]) > 0:
                for enemy in nearby_enemies[unit.id]:
                    enemy_locations.append(enemy.location.map_location())
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
                            lowest_enemy = find_lowest(attackable_enemies)
                            gc.attack(unit.id, lowest_enemy.id)
                            keep_moving = False
                        
            elif gc.is_move_ready(unit.id):
                if len(enemy_locations) > 0:
                    target_loc = find_closest_loc(unit_loc, enemy_locations)
                    my_paths[unit.id] = pathing.find_path(unit_loc, target_loc)
                    move_along_path(unit)
                else:
                    move_fowards(unit.id)
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
                if len(nearby_friends) > 0:        
                    lowest_friend = find_most_missing(nearby_friends)
                    my_paths[unit.id] = pathing.find_path(unit_loc, lowest_friend.location.map_location())
                    move_along_path(unit)             
                elif len(my_units[bc.UnitType.Ranger]) > 0:
                    lowest_friend = find_most_missing(my_units[bc.UnitType.Ranger])
                    my_paths[unit.id] = pathing.find_path(unit_loc, lowest_friend.location.map_location())
                    move_along_path(unit)
                else:
                    move_fowards(unit.id)
    except Exception as e:
        print('Healer Error:', e)				
        traceback.print_exc()
          
    try:    #mage code
        for unit in my_units[bc.UnitType.Mage]:
            unit_loc = unit.location.map_location()
            nearby_enemies[unit.id][:] = [enemy for enemy in nearby_enemies[unit.id] if gc.can_sense_unit(enemy.id)]
            
            if len(nearby_enemies[unit.id]) > 0:
                for enemy in nearby_enemies[unit.id]:
                    enemy_locations.append(enemy.location.map_location())
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
                if len(enemy_locations) > 0:
                    target_loc = find_closest_loc(unit_loc, enemy_locations)
                    my_paths[unit.id] = pathing.find_path(unit_loc, target_loc)
                    move_along_path(unit)
                else:
                    move_fowards(unit.id)
    except Exception as e:
        print('Mage Error:', e)				
        traceback.print_exc()
        
    # send the actions we've performed, and wait for our next turn.
    gc.next_turn()
    sys.stdout.flush()
    sys.stderr.flush()
