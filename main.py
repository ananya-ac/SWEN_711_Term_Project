import numpy as np
from utils.sim_world import Grid, TripTracker
from utils import match
from utils.Matching import matching

# We need to 
# - Track time based grids
# - init the Grid
# - Populate the request & create the trips
# - match the cars
# - Update the grid matrix


# Global Trackers for all time steps
time_tensor = np.array([])
max_time = 100 # Max Simulation Time
trip_tracker = TripTracker()
all_vehicles = []
curr_time = 0
num_cars =4
grid= Grid(curr_time,dim = 4, lambda_trip_gen = 4,num_cars = num_cars,
            max_wait_time = 5)
print(grid.travel_time_mat)
##### init cars
veh , is_gen =grid.init_cars(all_vehicles)
# print(f'Vehicles => {veh}, {is_gen}')
if is_gen:
    all_vehicles.extend(veh)
print('Generating Vehicles   : \n')
for veh in all_vehicles:
    print(veh)

##### get new trips of this time instance
## the grid.request grid has been updated with the num of trips generated
trip_tracker.add_new_trips(grid.generate_trips(curr_time))# works like queue enqueue

while  ((np.sum(grid.request_grid)>0) or (np.sum(grid.vehicle_grid.diagonal())!=num_cars)) :
    curr_time+=1
    print(f'Current Time = {curr_time}')
    
    # trip_tracker.add_new_trips(grid.generate_trips())# works like queue enqueue
    
    if curr_time>3:
        grid.request_grid = trip_tracker.pop_expired_trips(curr_time, grid.request_grid)
    if curr_time%3 == 0 and curr_time>1 and curr_time<10:
        print(f'Generating New Trips @ Curr time == {curr_time}!!')
        trip_tracker.add_new_trips(grid.generate_trips(curr_time))
    ##### match trips

    # print(f"Before matching at Time = {curr_time}",grid.request_grid.sum(axis=1), grid.vehicle_grid.diagonal(), grid.vehicle_grid.sum(axis=1))
    print('\n1.Vehicle Grid\n',grid.vehicle_grid)
    # u,v = grid.request_grid[:], grid.vehicle_grid[:]
    matching_info =  matching(
        u=grid.request_grid[:], #grid,trip_tracker)
        v=grid.vehicle_grid[:],
        vehicles=all_vehicles,
        vehicle_engagement={},
        travel_time=grid.travel_time_mat
        )
    print('1st in Main\n', grid.vehicle_grid )
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
    
    print("############# Unassigned Trips\n")
    for i in trip_tracker.unassigned:
        print(i)
    print("############# Assigned Trips\n")
    for i in trip_tracker.assigned:
        print(i)
    # print("############# Vehicles \n")
    # for v in all_vehicles:
    #     print(v)
    # print("############# Round Ends\nRequests:\n",grid.request_grid, 
    #       '\nVehicles:\n',grid.vehicle_grid)
    
    

print('1st in Main\n', grid.vehicle_grid , '\n request grid below\n', grid.request_grid)