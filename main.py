import numpy as np
from utils.sim_world import Grid, TripTracker
from utils import match
from utils.Matching import matching
from utils.Sim_Actors import Trip
from utils.config import MainParmas as cfg
from utils.config import DIST_MATRIX, TRAVEL_TIME_MATRIX
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


while(curr_time<4):#(np.sum(grid.request_grid)>0) or (np.sum(grid.vehicle_grid.diagonal())!=num_cars)) :
    
    

    if curr_time>3:
        grid.request_grid = trip_tracker.pop_expired_trips(curr_time, grid.request_grid)
    if (curr_time%3 == 0 and curr_time>1) and (
        curr_time<cfg.num_trip_gen_rounds*3+1) and cfg.generate_new_trips:
        #print(f'Generating New Trips @ Curr time == {curr_time}!!')
        trip_tracker.add_new_trips(grid.generate_trips(curr_time))
    # print("Before Matching")
    # print(grid.vehicle_grid)
    # print(grid.request_grid)
    ##### match trips
    matching_info =  matching(
        u=grid.request_grid[:],
        v=grid.vehicle_grid[:],
        vehicles=all_vehicles,
        vehicle_engagement={},
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
                                    grid.request_grid,
                                    grid.vehicle_grid)
    # print('Request Grid post matching\n',request_grid_prime)
    # grid.vehicle_grid = vehicle_grid_prime
    # grid.request_grid = request_grid_prime
    
    # print(f"After matching at Time = {curr_time}",grid.request_grid.sum(axis=1), grid.vehicle_grid.diagonal())
    trip_tracker.update_trips(curr_time, grid.vehicle_grid, all_vehicles)
    
    #print("############# Unassigned Trips\n")
    for i in trip_tracker.unassigned:
        if i.pickup_time > 600:
            print(i)
            print(i.pickup_time)
    #print("############# Assigned Trips\n")
    #print()
    for i in trip_tracker.assigned:
        if i.pickup_time > 600:
            print(i)
            print(i.pickup_time)
    
    grid.update_transition_matrix()
    
    print('after matching')
    print(grid.vehicle_grid)
    print(grid.request_grid)
    for veh in all_vehicles:
        if veh.idle: #There is a problem here. When a vehicle makes a drop at this timestep, 
            veh.idle_time_increase() #it is marked as idle and it contributes to negative reward.
            grid.idle_time_per_zone_increase(veh.get_location())
            if veh.get_idle_time() == 1:
                grid.idle_car_per_zone_increase(veh.get_location())
            
            relocation_state, confidence = veh.relocate_to(grid.get_lambda()[veh.loc], 
                            grid.vehicle_transition_matrix)
            
            if relocation_state == -1:
                grid.idle_no_reposition_loss(veh.loc) 
            else:
                #print(f"Veh :{veh.id} Curr_loc : {veh.loc} Reloc Confidence : {confidence} State = {relocation_state}")
                reloc_trip = Trip(curr_time, 
                            veh.loc,
                            relocation_state,
                            DIST_MATRIX[veh.loc][relocation_state],
                            TRAVEL_TIME_MATRIX[veh.loc][relocation_state],
                            pickup_time = curr_time + math.ceil(
                                TRAVEL_TIME_MATRIX[veh.loc][relocation_state]))
                reloc_trip.assigned = 2
                reloc_trip.vehicle = veh.id
                #print(f"New Relocation trip created : {reloc_trip}")
                trip_tracker.assigned.append(reloc_trip)
                grid.vehicle_grid[veh.loc][relocation_state]+=1
                grid.vehicle_grid[veh.loc][veh.loc]-=1
                veh.idle = False
                grid.idle_reposition_loss(veh.loc, DIST_MATRIX[veh.loc][relocation_state], 
                                          TRAVEL_TIME_MATRIX[veh.loc][relocation_state])
                # veh_index = all_vehicles.index(veh)
                # all_vehicles[veh_index].idle = False

    try:
        a = grid.get_idle_time_per_zone()[:]
        b = grid.get_idle_vehicle_per_zone()[:]
        avg_stay_time = np.divide(a, b, out=np.zeros_like(a), where=b!=0)
        avg_stay_time = np.nan_to_num(avg_stay_time)
    except RuntimeWarning:
        print("check for 0/0")
    
    curr_time+=1
    
    
    
    # print("zonal rev:", grid.zonal_profit)
    # print(f'Avg Stay Duration : {avg_stay_time}')
    #print("############# Vehicles \n")
    # for v in all_vehicles:
    #     print(v)
    # print("############# Round Ends\nRequests:\n",grid.request_grid, 
    #       '\nVehicles:\n',grid.vehicle_grid)
    
