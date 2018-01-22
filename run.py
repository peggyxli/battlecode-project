import battlecode as bc
import random
import sys
import traceback
import os
import math

gc = bc.GameController()
directions = list(bc.Direction)
travel_directions = {}
factory_loc = []
new_d = []
rotate_mods = [0, -1, 1, -2, 2, -3, 3, -4]


def move_towards(unit_id, d):
    for mod in rotate_mods:
        if gc.can_move(unit_id, directions[(d+mod)%8]):
            gc.move_robot(unit_id, directions[(d+mod)%8])
            travel_directions[unit_id] = directions[(d+mod)%8]
            break

def move_fowards(unit_id):
    if unit_id not in travel_directions:
        travel_directions[unit_id] = random.choice(directions)
    d = travel_directions[unit_id]
    for mod in rotate_mods:
        if gc.can_move(unit_id, directions[(d+mod)%8]):
            gc.move_robot(unit_id, directions[(d+mod)%8])
            travel_directions[unit_id] = directions[(d+mod)%8]
            break
            
def move_to_bp(unit):
    if len(my_blueprints) > 0:
        loc = unit.location.map_location()
        closest_bp = my_blueprints[0]
        closest_dist = 100
        for bp in my_blueprints:
            test_dist = loc.distance_squared_to(bp.location.map_location()) 
            if test_dist < closest_dist:
                closest_bp = bp
                closest_dist = test_dist
        if gc.can_build(unit.id, closest_bp.id):
            gc.build(unit.id, closest_bp.id)
            return False
        elif closest_dist <= 50:
            travel_directions[unit.id] = loc.direction_to(closest_bp.location.map_location())
            return True
    return False
    
def closest_blueprint(unit):
    if len(my_blueprints) > 0:
        loc = unit.location.map_location()
        closest_bp = my_blueprints[0]
        closest_dist = 100
        for bp in my_blueprints:
            test_dist = loc.distance_squared_to(bp.location.map_location()) 
            if test_dist < closest_dist:
                closest_bp = bp
                closest_dist = test_dist
        if closest_dist <= 50:
            return closest_bp
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
    
random.seed(6137)

# let's start off with some research!
# we can queue as much as we want.
gc.queue_research(bc.UnitType.Rocket)
gc.queue_research(bc.UnitType.Ranger)
gc.queue_research(bc.UnitType.Ranger)

my_team = gc.team()
if my_team == bc.Team.Blue:
    other_team = bc.Team.Red
else:
    other_team = bc.Team.Blue

while True:
    #print('pyround:', gc.round(), 'time left:', gc.get_time_left_ms(), 'ms')
    
    #adding travel directions to new units
    while len(factory_loc) > 0:
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
    enemy_locations = []
    
    for unit in gc.my_units():
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
    
    try:
        for unit in my_factories:
            unit_location = unit.location.map_location()
            garrison = unit.structure_garrison()
            if len(garrison) > 0:
                print('pyround:', gc.round())
                print (unit_location)
                print (len(garrison))
                for d in directions:
                    if gc.can_unload(unit.id, d):
                        gc.unload(unit.id, d)
                        factory_loc.append(unit_location)
                        new_d.append(d)
                        break
            elif len(my_factories)*2 > len(my_knights) and gc.can_produce_robot(unit.id, bc.UnitType.Knight):
                gc.produce_robot(unit.id, bc.UnitType.Knight)
            elif len(my_rangers)/4 > len(my_healers) and gc.can_produce_robot(unit.id, bc.UnitType.Ranger):
                gc.produce_robot(unit.id, bc.UnitType.Ranger)
            elif gc.can_produce_robot(unit.id, bc.UnitType.Healer):
                gc.produce_robot(unit.id, bc.UnitType.Healer)
    except Exception as e:
        print('Factory Error:', e)				
        traceback.print_exc()            
                
    try:
        for unit in my_workers:
            unit_location = unit.location.map_location()
            doing_action = False
            
            test_bp = closest_blueprint(unit)
            if test_bp != unit: #if there's a blueprint nearby
                if gc.can_build(unit.id, test_bp.id):
                    gc.build(unit.id, test_bp.id)
                    doing_action = True
                else:
                    travel_directions[unit.id] = unit_location.direction_to(test_bp.location.map_location())
                    harvest_nearby(unit)

            #elif gc.research_info().get_level(bc.UnitType.Rocket) > 0 and len(my_rockets) < math.floor(len(my_factories)/4):
            #    adjacent_spaces = list(gc.all_locations_within(unit_location, 2))
            #    adjacent_spaces.remove(unit_location)
            #    adjacent_spaces[:] = [space for space in adjacent_spaces if good_bp_loc(space)]
            #    if len(adjacent_spaces) > 0:
            #        bp_space = random.choice(adjacent_spaces)
            #        if gc.can_blueprint(unit.id, bc.UnitType.Rocket, unit_location.direction_to(bp_space)):
            #            gc.blueprint(unit.id, bc.UnitType.Rocket, unit_location.direction_to(bp_space))
            #    elif gc.is_move_ready(unit.id): #move to a better spot
            #        move_towards(unit.id, random.choice(directions))
            
            elif (gc.karbonite()/2 > bc.UnitType.Factory.blueprint_cost()) or (len(my_factories) < 4):
                adjacent_spaces = list(gc.all_locations_within(unit_location, 2))
                adjacent_spaces.remove(unit_location)
                adjacent_spaces[:] = [space for space in adjacent_spaces if good_bp_loc(space)]
              
                if len(adjacent_spaces) > 0:
                    spaces_near_worker = [space for space in adjacent_spaces if worker_nearby(space)]
                    if len(spaces_near_worker) > 0:
                        bp_space = random.choice(spaces_near_worker)
                    else:
                        bp_space = random.choice(adjacent_spaces)
                    if gc.can_blueprint(unit.id, bc.UnitType.Factory, unit_location.direction_to(bp_space)):
                        gc.blueprint(unit.id, bc.UnitType.Factory, unit_location.direction_to(bp_space))
                        doing_action = True
            #elif can clone
                #clone
            elif harvest_nearby(unit):
                doing_action = True
                   
            if not doing_action and gc.is_move_ready(unit.id):
                move_fowards(unit.id)

    except Exception as e:
        print('Worker Error:', e)				
        traceback.print_exc()
    
    try:           
        for unit in my_knights:
            if unit.location.is_on_map():
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
                            direction = friend.location.map_location().direction_to(unit_location)
                            move_towards(unit.id, travel_directions[unit.id])
                            break                        
    except Exception as e:
        print('Knight Error:', e)				
        traceback.print_exc()
                        
    try:
        for unit in my_rangers:
            if unit.location.is_on_map():
                unit_location = unit.location.map_location()
                if gc.research_info().get_level(bc.UnitType.Ranger) > 1:
                    nearby_enemies = gc.sense_nearby_units_by_team(unit_location, 100, other_team)
                else:
                    nearby_enemies = gc.sense_nearby_units_by_team(unit_location, 70, other_team)
                    
                if gc.is_attack_ready(unit.id):
                    for enemy in nearby_enemies:
                        if gc.can_attack(unit.id, enemy.id):
                            gc.attack(unit.id, enemy.id)
                            break
                if gc.is_move_ready(unit.id):
                    moved_this_turn = False
                    for enemy in nearby_enemies:
                        enemy_locations.append(enemy.location.map_location())
                        if unit_location.distance_squared_to(enemy.location.map_location()) > 50:
                            d = unit_location.direction_to(enemy.location.map_location())                            
                            if gc.can_move(unit.id, d):
                                gc.move_robot(unit.id, d)
                                travel_directions[unit.id] = d
                                moved_this_turn = True
                                break
                        elif unit_location.distance_squared_to(enemy.location.map_location()) < 10:
                            d = enemy.location.map_location().direction_to(unit_location)                            
                            if gc.can_move(unit.id, d):
                                gc.move_robot(unit.id, d)
                                travel_directions[unit.id] = d
                                moved_this_turn = True
                                break
                    if not moved_this_turn:
                        if len(enemy_locations) > 0:
                            target_location = random.choice(enemy_locations)
                            d = unit_location.direction_to(target_location)
                            travel_directions[unit.id] = d
                        #print ("Trying to move")
                        move_towards(unit.id, travel_directions[unit.id])
    except Exception as e:
        print('Ranger Error:', e)				
        traceback.print_exc()
        
    # send the actions we've performed, and wait for our next turn.
    gc.next_turn()
    sys.stdout.flush()
    sys.stderr.flush()
