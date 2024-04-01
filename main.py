import numpy as np
from utils.sim_world import Grid, TripTracker
from utils import match
from utils.Matching_new import matching

# We need to 
# - Track time based grids
# - init the Grid
# - Populate the request & create the trips
# - match the cars
# - Update the grid matrix


# Global Trackers for all time steps
time_tensor = np.array([])
max_time = 20 # Max Simulation Time
trip_tracker = TripTracker()
all_vehicles = []
curr_time = 0

while (curr_time<=max_time):
    print(f'Current Time = {curr_time}')
    curr_time+=1
    # generate Grid
    if curr_time == 1:
        grid= Grid(curr_time,dim = 4, lambda_trip_gen = 4,num_cars = 8,
                    max_wait_time = 5)
        print(grid.dist_mat)
        ##### init cars
        veh , is_gen =grid.init_cars(all_vehicles)
        # print(f'Vehicles => {veh}, {is_gen}')
        if is_gen:
            all_vehicles.extend(veh)
        # print('Generating Vehicles   : \n')
        # for veh in all_vehicles:
        #     print(veh)
    
    ##### get new trips of this time instance
    ## the grid.request grid has been updated with the num of trips generated
    trip_tracker.add_new_trips(grid.generate_trips())# works like queue enqueue
    ## Any trip is expiring based on max_wait_time
    
    
    ##### match trips
    # matched_pairs, u, v
    # u, v, vehicles, vehicle_engagement, travel_time
    # print('---- JDSFN')
    # for veh in all_vehicles:
    #     print(veh)
    # print('---- JDSFN')
    print(f"Before matching at Time = {curr_time}",grid.request_grid.sum(axis=1), grid.vehicle_grid.diagonal(), grid.vehicle_grid.sum(axis=1))
    print('Request grid\n',grid.request_grid,'\nVehicle Grid\n',grid.vehicle_grid)
    matching_info, request_grid_prime, vehicle_grid_prime =  matching(
        u=grid.request_grid, #grgrid,trip_tracker)
        v=grid.vehicle_grid,
        vehicles=all_vehicles,
        vehicle_engagement={},
        travel_time=grid.travel_time_mat
        )
    if (grid.vehicle_grid < 0).sum() > 0:
        raise Exception('BC MC')
    # print('JDSFN')
    # for veh in all_vehicles:
    #     print(veh)
    # print('JDSFN')
    
    for kth_match in matching_info:
        trip_tracker.assign_trips(curr_time, [kth_match], all_vehicles, grid.travel_time_mat)
    grid.vehicle_grid = vehicle_grid_prime
    grid.request_grid = request_grid_prime
    
    print(f"After matching at Time = {curr_time}",grid.request_grid.sum(axis=1), grid.vehicle_grid.diagonal())
    trip_tracker.update_trips(curr_time, grid.vehicle_grid, all_vehicles, grid.travel_time_mat)
    
    # for i in trip_tracker.unassigned:
    #     print("############# END OF THIS LOOP\n",i)
    
    # for i in trip_tracker.assigned:
    #     print(i)
    
    
    

