import battlecode as bc
import random
import sys
import traceback
import os

gc = bc.GameController()
directions = list(bc.Direction)
travel_directions = {}
factory_loc = []
new_d = []
rotate_mods = [0, -1, 1, -2, 2, -3, 3, -4]


def move_fowards(unit_id):
    if unit_id not in travel_directions:
        travel_directions[unit_id] = random.choice(directions)
    d = travel_directions[unit_id]
    for mod in rotate_mods:
        if gc.can_move(unit_id, directions[(d+mod)%8]):
            gc.move_robot(unit_id, directions[(d+mod)%8])
            travel_directions[unit_id] = directions[(d+mod)%8]
            break

def find_closest(unit, myarr, threshold = 200):
    if len(myarr) > 0:
        loc = unit.location.map_location()
        closest_unit = myarr[0]
        closest_dist = 250
        for other in myarr:
            test_dist = loc.distance_squared_to(other.location.map_location()) 
            if test_dist < closest_dist:
                closest_unit = other
                closest_dist = test_dist
        if closest_dist <= threshold:   #for worker search
            return closest_unit
    return unit
            
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
    
def harvest_nearby(unit): 
    for dir in directions:
        if gc.can_harvest(unit.id, dir):
            gc.harvest(unit.id, dir)
            travel_directions[unit.id] = dir
            return True
    return False

def find_lowest(myarr):
    lowest_unit = myarr[0]
    most_missing = 0
    for other in myarr:
        missing_health = other.max_health - other.health
        if missing_health > most_missing:
            most_missing = missing_health
            lowest_unit = other
    return lowest_unit

    
random.seed(6137)

# let's start off with some research!
# we can queue as much as we want.
gc.queue_research(bc.UnitType.Rocket)
gc.queue_research(bc.UnitType.Ranger)
gc.queue_research(bc.UnitType.Ranger)
gc.queue_research(bc.UnitType.Healer)
gc.queue_research(bc.UnitType.Mage)
gc.queue_research(bc.UnitType.Healer)
gc.queue_research(bc.UnitType.Mage)

my_team = gc.team()
if my_team == bc.Team.Blue:
    other_team = bc.Team.Red
else:
    other_team = bc.Team.Blue

while True:
    #print('pyround:', gc.round(), 'time left:', gc.get_time_left_ms(), 'ms')
    while len(factory_loc) > 0: #adding travel directions to new units
        new_location = factory_loc[0].add(new_d[0])
        factory_loc.pop(0)
        if gc.has_unit_at_location(new_location):
            new_unit = gc.sense_unit_at_location(new_location)
            travel_directions[new_unit.id] = new_d[0] 
        new_d.pop(0)

    my_factories = []
    my_rockets = []
    my_blueprints = []
    my_workers = []
    my_knights = []
    my_rangers = []
    my_mages = []
    my_healers = []
    enemy_locations = []
    
    for unit in gc.my_units():
        if unit.location.is_on_map():
            if unit.unit_type == bc.UnitType.Factory:
                if unit.structure_is_built():
                    my_factories.append(unit)
                else:
                    my_blueprints.append(unit)
            elif unit.unit_type == bc.UnitType.Rocket:
                if unit.structure_is_built():
                    my_rockets.append(unit)
                else:
                    my_blueprints.append(unit)
            elif unit.unit_type == bc.UnitType.Worker:
                my_workers.append(unit)
            elif unit.unit_type == bc.UnitType.Knight:
                my_knights.append(unit)
            elif unit.unit_type == bc.UnitType.Ranger:
                my_rangers.append(unit)
            elif unit.unit_type == bc.UnitType.Healer:
                my_healers.append(unit)
            elif unit.unit_type == bc.UnitType.Mage:
                my_mages.append(unit)
    
    try:    #factory code
        for unit in my_factories:
            unit_location = unit.location.map_location()
            garrison = unit.structure_garrison()
            if len(garrison) > 0:
                for d in directions:
                    if gc.can_unload(unit.id, d):
                        gc.unload(unit.id, d)
                        factory_loc.append(unit_location)
                        new_d.append(d)
                        break
            elif len(my_workers) < 3 and gc.can_produce_robot(unit.id, bc.UnitType.Worker):
                gc.produce_robot(unit.id, bc.UnitType.Worker)
            elif len(my_factories)*2 > len(my_knights) and gc.can_produce_robot(unit.id, bc.UnitType.Knight):
                gc.produce_robot(unit.id, bc.UnitType.Knight)
            elif len(my_rangers)/4 < len(my_healers) and gc.can_produce_robot(unit.id, bc.UnitType.Ranger):
                gc.produce_robot(unit.id, bc.UnitType.Ranger)
            elif len(my_healers) <= len(my_mages) and gc.can_produce_robot(unit.id, bc.UnitType.Healer):
                gc.produce_robot(unit.id, bc.UnitType.Healer)
            elif gc.can_produce_robot(unit.id, bc.UnitType.Mage):
                gc.produce_robot(unit.id, bc.UnitType.Mage)            
    except Exception as e:
        print('Factory Error:', e)				
        traceback.print_exc()            
    
    try:    #rocket code
        for unit in my_rockets:
            unit_location = unit.location.map_location()
            garrison = unit.structure_garrison()
            if unit_location.planet == bc.Planet.Earth:
                if len(garrison) < unit.structure_max_capacity():
                    nearby_friends = gc.sense_nearby_units_by_team(unit_location, 2, my_team)
                    for friend in nearby_friends:
                        if gc.can_load(unit.id, friend.id) and len(garrison) < unit.structure_max_capacity():
                            gc.load(unit.id, friend.id)
                if len(garrison) == unit.structure_max_capacity():
                    maxX = gc.starting_map(bc.Planet.Mars).width - 1
                    maxY = gc.starting_map(bc.Planet.Mars).height - 1
                    testX = random.randint(0, maxX)
                    testY = random.randint(0, maxY)
                    while not gc.can_launch_rocket(unit.id, bc.MapLocation(bc.Planet.Mars, testX, testY)):
                        testX = random.randint(0, maxX)
                        testY = random.randint(0, maxY)
                    gc.launch_rocket(unit.id, bc.MapLocation(bc.Planet.Mars, testX, testY))
            elif len(garrison) > 0:
                for friend in garrison:
                    for dir in directions:
                        if gc.can_unload(unit.id, dir):
                            gc.unload(unit.id, dir)
                            break

    except Exception as e:
        print('Factory Error:', e)				
        traceback.print_exc()
    
    try:    #worker code
        for unit in my_workers:
            unit_location = unit.location.map_location()
            if unit_location.planet == bc.Planet.Earth:
                doing_action = False
                if len(my_workers) < len(my_factories)*2 or len(my_workers) < 3:
                    for dir in directions:
                        if gc.can_replicate(unit.id, dir):
                            gc.replicate(unit.id, dir)
                            break
                
                test_bp = find_closest(unit, my_blueprints, 50)
                if test_bp != unit: #if there's a blueprint nearby
                    if gc.can_build(unit.id, test_bp.id):
                        gc.build(unit.id, test_bp.id)
                        doing_action = True
                    else:
                        travel_directions[unit.id] = unit_location.direction_to(test_bp.location.map_location())
                
                elif gc.karbonite() > len(my_factories)*25 and gc.karbonite() > bc.UnitType.Factory.blueprint_cost():
                    adjacent_spaces = list(gc.all_locations_within(unit_location, 2))
                    adjacent_spaces.remove(unit_location)
                    adjacent_spaces[:] = [space for space in adjacent_spaces if good_bp_loc(space) and gc.is_occupiable(space)]
                  
                    if len(adjacent_spaces) > 0:
                        spaces_near_worker = [space for space in adjacent_spaces if worker_nearby(space)]
                        if len(spaces_near_worker) > 0:
                            bp_space = random.choice(spaces_near_worker)
                        else:
                            bp_space = random.choice(adjacent_spaces)
                        
                        if gc.research_info().get_level(bc.UnitType.Rocket) > 0 and (len(my_factories)/4 > len(my_rockets)):
                            if gc.can_blueprint(unit.id, bc.UnitType.Rocket, unit_location.direction_to(bp_space)):
                                gc.blueprint(unit.id, bc.UnitType.Rocket, unit_location.direction_to(bp_space))
                                doing_action = True
                        elif gc.can_blueprint(unit.id, bc.UnitType.Factory, unit_location.direction_to(bp_space)):
                            gc.blueprint(unit.id, bc.UnitType.Factory, unit_location.direction_to(bp_space))
                            doing_action = True
                    
                elif harvest_nearby(unit):
                    doing_action = True
                    
                if not doing_action and gc.is_move_ready(unit.id):
                    harvest_nearby(unit)
                    move_fowards(unit.id)
            
            elif not harvest_nearby(unit) and gc.is_move_ready(unit.id):
                move_fowards(unit.id)
    except Exception as e:
        print('Worker Error:', e)				
        traceback.print_exc()
    
    try:    #knight code
        for unit in my_knights:
            unit_location = unit.location.map_location()
            nearby_enemies = gc.sense_nearby_units_by_team(unit_location, 2, other_team)
            for enemy in nearby_enemies:
                if gc.is_attack_ready(unit.id) and gc.can_attack(unit.id, enemy.id):
                    gc.attack(unit.id, enemy.id)
                    break
            if gc.is_move_ready(unit.id):
                nearby_friends = gc.sense_nearby_units_by_team(unit_location, 1, my_team)
                for friend in nearby_friends:
                    if (friend.unit_type == bc.UnitType.Knight) and (friend.id != unit.id): #spread out
                        travel_directions[unit.id] = friend.location.map_location().direction_to(unit_location)
                        move_fowards(unit.id)
                        break                        
    except Exception as e:
        print('Knight Error:', e)				
        traceback.print_exc()
                        
    try:    #ranger code
        for unit in my_rangers:
            unit_location = unit.location.map_location()
            nearby_enemies = gc.sense_nearby_units_by_team(unit_location, unit.vision_range, other_team)
            
            if len(nearby_enemies) > 0:
                for enemy in nearby_enemies:
                    enemy_locations.append(enemy.location.map_location())
                if gc.is_attack_ready(unit.id):
                    attackable_enemies = [enemy for enemy in nearby_enemies if gc.can_attack(unit.id, enemy.id)]
                    if len(attackable_enemies) > 0:
                        gc.attack(unit.id, random.choice(attackable_enemies).id)
                if gc.is_move_ready(unit.id):
                    closest_enemy = find_closest(unit, nearby_enemies)
                    if unit_location.distance_squared_to(closest_enemy.location.map_location()) < 11:
                        travel_directions[unit.id] = closest_enemy.location.map_location().direction_to(unit_location)
                    else:
                        travel_directions[unit.id] = unit_location.direction_to(closest_enemy.location.map_location())                            
                    move_fowards(unit.id)
            elif gc.is_move_ready(unit.id):
                if len(enemy_locations) > 0:
                    target_location = random.choice(enemy_locations)
                    travel_directions[unit.id] = unit_location.direction_to(target_location)
                move_fowards(unit.id)
    except Exception as e:
        print('Ranger Error:', e)				
        traceback.print_exc()
    
    try:    #healer code
        for unit in my_healers:
            unit_location = unit.location.map_location()
            
            nearby_friends = list(gc.sense_nearby_units_by_team(unit_location, unit.vision_range, my_team))
            nearby_friends[:] = [friend for friend in nearby_friends if friend.health < friend.max_health]
            if unit in nearby_friends:
                nearby_friends.remove(unit)
                
            if gc.is_heal_ready(unit.id) and len(nearby_friends) > 0:
                healable_friends = [friend for friend in nearby_friends if gc.can_heal(unit.id, friend.id)]
                if len(healable_friends) > 0:
                    lowest_friend = find_lowest(healable_friends)
                    gc.heal(unit.id, lowest_friend.id)
                        
            if gc.is_move_ready(unit.id):           
                if len(nearby_friends) > 0:        
                    lowest_friend = find_lowest(nearby_friends)
                    travel_directions[unit.id] = unit_location.direction_to(lowest_friend.location.map_location())               
                elif len(my_rangers) > 0:
                    lowest_friend = find_lowest(my_rangers)
                    travel_directions[unit.id] = unit_location.direction_to(lowest_friend.location.map_location())
                move_fowards(unit.id)
    except Exception as e:
        print('Healer Error:', e)				
        traceback.print_exc()
          
    try:    #mage code
        for unit in my_mages:
            unit_location = unit.location.map_location()
            nearby_enemies = gc.sense_nearby_units_by_team(unit_location, unit.vision_range, other_team)
            
            if len(nearby_enemies) > 0:
                for enemy in nearby_enemies:
                    enemy_locations.append(enemy.location.map_location())
                if gc.is_attack_ready(unit.id):
                    gc.attack(unit.id, random.choice(nearby_enemies).id)
                if gc.is_move_ready(unit.id):
                    if len(nearby_enemies) == 1:
                        travel_directions[unit.id] = unit_location.direction_to(nearby_enemies[0].location.map_location())   
                    else:
                        enemy = random.choice(nearby_enemies)
                        travel_directions[unit.id] = enemy.location.map_location().direction_to(unit_location)                         
                    move_fowards(unit.id)
            elif gc.is_move_ready(unit.id):
                if len(enemy_locations) > 0:
                    target_location = random.choice(enemy_locations)
                    travel_directions[unit.id] = unit_location.direction_to(target_location)
                move_fowards(unit.id)
    except Exception as e:
        print('Mage Error:', e)				
        traceback.print_exc()
        
    # send the actions we've performed, and wait for our next turn.
    gc.next_turn()
    sys.stdout.flush()
    sys.stderr.flush()
