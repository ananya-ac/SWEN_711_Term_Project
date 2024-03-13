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
trips = TripTracker()
vehicles = []
curr_time = 0

while (curr_time<=max_time):
    curr_time+=1
    # generate Grid
    grid= Grid(curr_time,dim = 4, lambda_trip_gen = 4,num_cars = 4,
                    max_wait_time = 5)
    
    ##### init cars
    veh , is_gen =grid.init_cars(vehicles)
    if is_gen:
        vehicles.extend(veh)
    print('Cars generated : \n')
    for veh in vehicles:
        print(veh)
    
    ##### get new trips of this time instance
    ## the grid.request grid has been updated with the num of trips generated
    trips.add_new_trips(grid.generate_trips())# works like queue enqueue
    ## Any trip is expiring based on max_wait_time
    
    
    ##### match trips
    grid.request_grid, grid.vehicle_grid =  match(grid,trips)

    print(grid.request_grid)
    for i in trips['unassigned']:
        print(i)
    
    
    

