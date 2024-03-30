import numpy as np
from utils.sim_world import Grid, TripTracker
from utils import match


# We need to 
# - Track time based grids
# - init the Grid
# - Populate the request & create the trips
# - match the cars
# - Update the grid matrix


# Global Trackers for all time steps
time_tensor = np.array([])
max_time = 1 # Max Simulation Time
trip_tracker = TripTracker()
all_vehicles = []
curr_time = 0

while (curr_time<=max_time):
    curr_time+=1
    # generate Grid
    if curr_time == 1:
        grid= Grid(curr_time,dim = 4, lambda_trip_gen = 4,num_cars = 4,
                    max_wait_time = 5)
    
        ##### init cars
        veh , is_gen =grid.init_cars(all_vehicles)
        if is_gen:
            all_vehicles.extend(veh)
        print('Generating Vehicles   : \n')
        for veh in all_vehicles:
            print(veh)
    
    ##### get new trips of this time instance
    ## the grid.request grid has been updated with the num of trips generated
    trip_tracker.add_new_trips(grid.generate_trips())# works like queue enqueue
    ## Any trip is expiring based on max_wait_time
    
    
    ##### match trips
    request_grid_prime, vehicle_grid_prime, matching_info =  match(grid,trip_tracker)
    for kth_match in matching_info:
        trip_tracker.assign_trips(curr_time, [kth_match], all_vehicles, grid.travel_time_mat)
    grid.vehicle_grid = vehicle_grid_prime
    grid.request_grid = request_grid_prime
    
    print(grid.request_grid)
    #
    for i in trip_tracker.unassigned:
        print("############# END OF THIS LOOP\n",i)
    
    for i in trip_tracker.assigned:
        print(i)
    
    
    

