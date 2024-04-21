import numpy as np
from utils.sim_world import Grid, TripTracker
from utils import match
from utils.Matching import matching
from utils.repositioning import update_avg_stay_time
from utils.Sim_Actors import Trip
from utils.config import MainParmas as cfg
import math
# We need to 
# - Track time based grids
# - init the Grid
# - Populate the request & create the trips
# - match the cars
# - Update the grid matrix


# Global Trackers for all time steps
time_tensor = np.array([])
max_time = 100 # Max Simulation Time

all_vehicles = []
curr_time = 0
num_cars = 4
grid= Grid(curr_time,dim = 4, lambda_trip_gen = 4,num_cars = num_cars,
            max_wait_time = 5)
trip_tracker = TripTracker(grid=grid)
#print(grid.travel_time_mat)
#print(grid.dist_mat)
##### init cars
veh , is_gen = grid.init_cars(all_vehicles)
#print(f'Vehicles => {veh}, {is_gen}')
if is_gen:
    all_vehicles.extend(veh)
# print('Generating Vehicles   : \n')
# for veh in all_vehicles:
#     print(veh)


##### get new trips of this time instance
## the grid.request grid has been updated with the num of trips generated
trip_tracker.add_new_trips(grid.generate_trips(curr_time))# works like queue enqueue

while  ((np.sum(grid.request_grid)>0) or (np.sum(grid.vehicle_grid.diagonal())!=num_cars)) or curr_time<500 :
    # if grid.travel_time_mat.all() != grid.travel_time_mat_cp.all():
    print(grid.travel_time_mat)
    if (curr_time>3):
        grid.request_grid = trip_tracker.pop_expired_trips(curr_time, grid.request_grid)
    if (curr_time%3 == 0 and curr_time>1) and (
        curr_time<cfg.num_trip_gen_rounds*3+1) and cfg.generate_new_trips:
        print(f'Generating New Trips @ Curr time == {curr_time}!!')
        trip_tracker.add_new_trips(grid.generate_trips(curr_time))
    
    ##### match trips
    matching_info =  matching(
        u=grid.request_grid[:],
        v=grid.vehicle_grid[:],
        vehicles=all_vehicles,
        vehicle_engagement={},
        travel_time=grid.travel_time_mat
        )
    #print('Matching info', matching_info )
    if ((grid.vehicle_grid < 0).sum()) > 0 and ((grid.request_grid < 0).sum()> 0):
        raise Exception('BC MC')
    # for kth_match in matching_info:
    # print("YOOO")
    # print('Request grid\n',grid.request_grid,'\nVehicle Grid\n',grid.vehicle_grid)
    # u,v = grid.request_grid[:], grid.vehicle_grid[:]
    grid.vehicle_grid, grid.request_grid = trip_tracker.assign_trips_new(curr_time, 
                                    matching_info,
                                    all_vehicles, 
                                    grid.travel_time_mat,
                                    grid.request_grid,
                                    grid.vehicle_grid)
    # print('Request Grid post matching\n',request_grid_prime)
    # grid.vehicle_grid = vehicle_grid_prime
    # grid.request_grid = request_grid_prime
    
    # print(f"After matching at Time = {curr_time}",grid.request_grid.sum(axis=1), grid.vehicle_grid.diagonal())
    trip_tracker.update_trips(curr_time, grid.vehicle_grid, all_vehicles, grid.travel_time_mat)
    
    # print("############# Unassigned Trips\n")
    # for i in trip_tracker.unassigned:
    #     print(i)
    # print("############# Assigned Trips\n")
    # for i in trip_tracker.assigned:
    #     print(i)
    
    grid.update_transition_matrix()
    
    for veh in all_vehicles:
        if veh.idle:
            veh.idle_time_increase()
            grid.idle_time_per_zone_increase(veh.get_location())
            if veh.get_idle_time() == 1:
                grid.idle_car_per_zone_increase(veh.get_location())
            
            relocation_state, confidence = veh.relocate_to(grid.get_lambda()[veh.loc], 
                            grid.vehicle_transition_matrix)
            
            print(f"Veh :{veh.id} Curr_loc : {veh.loc} Reloc Confidence : {confidence} State = {relocation_state}")
            if relocation_state!=-1:
                reloc_trip = Trip(curr_time, 
                            veh.loc,
                            relocation_state,
                            grid.dist_mat[veh.loc][relocation_state],
                            grid.travel_time_mat[veh.loc][relocation_state],
                            pickup_time=curr_time + math.ceil(
                                grid.travel_time_mat[veh.loc][relocation_state]))
                reloc_trip.assigned = 2
                reloc_trip.vehicle = veh.id
                print(f"New Relocation trip created : {reloc_trip}")
                trip_tracker.assigned.append(reloc_trip)
                grid.vehicle_grid[veh.loc][relocation_state]+=1
                grid.vehicle_grid[veh.loc][veh.loc]-=1
                veh_index = all_vehicles.index(veh)
                all_vehicles[veh_index].idle = False
                # trip = relocate_vehicle(veh, relocation_state)

        
    avg_stay_time = grid.get_idle_time_per_zone() / grid.get_idle_vehicle_per_zone()
    avg_stay_time = np.nan_to_num(avg_stay_time)
    
    print(grid.vehicle_grid)
    print(f'Avg Stay Duration : {avg_stay_time}')
    # print("############# Vehicles \n")
    # for v in all_vehicles:
    #     print(v)
    # print("############# Round Ends\nRequests:\n",grid.request_grid, 
    #       '\nVehicles:\n',grid.vehicle_grid)
    
    curr_time+=1
