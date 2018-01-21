import battlecode as bc
import random
import sys
import traceback
import os

gc = bc.GameController()
directions = list(bc.Direction)
unit_dir = {}
factory_loc = []
new_d = []
rotate_mods = [0, -1, 1, -2, 2, -3, 3, -4]


def move_towards(unit_id, d):
    for mod in rotate_mods:
        if gc.can_move(unit_id, directions[(d+mod)%8]):
            gc.move_robot(unit_id, directions[(d+mod)%8])
            unit_dir[unit_id] = directions[(d+mod)%8]
            break
            
            
def find_nearby_bp(unit):
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
            unit_dir[unit.id] = loc.direction_to(bp.location.map_location())
            return True
    return False

def good_bp_loc(location):
    if not gc.starting_map(bc.Planet.Earth).is_passable_terrain_at(location):
        return False
    elif len(gc.sense_nearby_units_by_type(location, 1, bc.UnitType.Factory)) > 0:
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
    
random.seed(6137)

# let's start off with some research!
# we can queue as much as we want.
gc.queue_research(bc.UnitType.Rocket)
gc.queue_research(bc.UnitType.Worker)
gc.queue_research(bc.UnitType.Knight)

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
            unit_dir[new_unit.id] = new_d[0] 
        new_d.pop(0)

    my_factories = []
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
                for d in directions:
                    if gc.can_unload(unit.id, d):
                        gc.unload(unit.id, d)
                        factory_loc.append(unit_location)
                        new_d.append(d)
                        break
            elif len(my_factories)*2 > len(my_knights) and gc.can_produce_robot(unit.id, bc.UnitType.Knight):
                gc.produce_robot(unit.id, bc.UnitType.Knight)
                #print('produced a knight!')
            elif gc.can_produce_robot(unit.id, bc.UnitType.Ranger):
                gc.produce_robot(unit.id, bc.UnitType.Ranger)
                #print('produced a ranger!')
    except Exception as e:
        print('Factory Error:', e)				
        traceback.print_exc()            
                
    try:
        for unit in my_workers:
            unit_location = unit.location.map_location()
            if find_nearby_bp(unit):
                test_loc = unit_location.add(unit_dir[unit.id])
                if gc.has_unit_at_location(test_loc):
                    test_unit = gc.sense_unit_at_location(test_loc)
                    if gc.can_build(unit.id, test_unit.id):
                        gc.build(unit.id, test_unit.id)
                    elif gc.is_move_ready(unit.id):
                        move_towards(unit.id, unit_dir[unit.id])
                elif gc.is_move_ready(unit.id):
                    move_towards(unit.id, unit_dir[unit.id])
            #elif rocket is ready
                #build one
            elif gc.karbonite() > bc.UnitType.Factory.blueprint_cost():
                nearby_workers = gc.sense_nearby_units_by_type(unit_location, 2, bc.UnitType.Worker)
                build_with_worker = False
                
                for other_worker in nearby_workers:
                    if unit_location.distance_squared_to(other_worker.location.map_location()) == 4:
                        bp_dir = unit_location.direction_to(other_worker.location.map_location())
                        if gc.can_blueprint(unit.id, bc.UnitType.Factory, bp_dir):
                            gc.blueprint(unit.id, bc.UnitType.Factory, bp_dir)
                            build_with_worker = True
                            break
                    
                if not build_with_worker:
                    adjacent_spaces = list(gc.all_locations_within(unit_location, 2))
                    adjacent_spaces.remove(unit_location)
                    print('pyround:', gc.round(), 'time left:', gc.get_time_left_ms(), 'ms')
                    print(unit_location)
                    print(adjacent_spaces)
                    adjacent_spaces[:] = [space for space in adjacent_spaces if good_bp_loc(space)]
                    print (adjacent_spaces)
                    if len(adjacent_spaces) > 0:
                        bp_space = random.choice(adjacent_spaces)
                        if gc.can_blueprint(unit.id, bc.UnitType.Factory, unit_location.direction_to(bp_space)):
                            gc.blueprint(unit.id, bc.UnitType.Factory, unit_location.direction_to(bp_space))
            #elif can clone
                #clone
            #else
                #harvest things
    except Exception as e:
        print('Worker Error:', e)				
        traceback.print_exc()
                        
    try:
        for unit in my_rangers:
            if unit.location.is_on_map():
                unit_location = unit.location.map_location()
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
                        if unit_location.distance_squared_to(enemy.location.map_location()) > 10:
                            d = unit_location.direction_to(enemy.location.map_location())                            
                            if gc.can_move(unit.id, d):
                                gc.move_robot(unit.id, d)
                                unit_dir[unit.id] = d
                                moved_this_turn = True
                                break
                    if not moved_this_turn:
                        if len(enemy_locations) > 0:
                            target_location = random.choice(enemy_locations)
                            d = unit_location.direction_to(target_location)
                            unit_dir[unit.id] = d
                        #print ("Trying to move")
                        move_towards(unit.id, unit_dir[unit.id])
    except Exception as e:
        print('Ranger Error:', e)				
        traceback.print_exc()
    
    try:           
        for unit in my_knights:
            if unit.location.is_on_map():
                unit_location = unit.location.map_location()
                nearby = gc.sense_nearby_units(unit_location, 2)
                for other in nearby:
                    if other.team != my_team and gc.is_attack_ready(unit.id) and gc.can_attack(unit.id, other.id):
                        print('attacked a thing!')
                        gc.attack(unit.id, other.id)
                        break
    except Exception as e:
        print('Knight Error:', e)				
        traceback.print_exc()


    # send the actions we've performed, and wait for our next turn.
    gc.next_turn()

    # these lines are not strictly necessary, but it helps make the logs make more sense.
    # it forces everything we've written this turn to be written to the manager.
    sys.stdout.flush()
    sys.stderr.flush()
