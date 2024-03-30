import numpy as np
from typing import List, Dict, Any
from .config import Grid as grd_conf
from .config import Simulation as sim_conf
from .Sim_Actors import Trip, Car

# model defs

class Simulation():
    def __init__(self, grid, vehicles_per_zone = sim_conf.VEHICLES_PER_ZONE) -> None:
        self.grid:Grid = None
        dims = self.grid.get_dims()
        self.dist_mat = np.array(np.random.randint(1,100, size=(dims,dims)))
        self.average_speed = 50
        self.travel_time = self.dist_mat/self.average_speed
        self.price_mult = np.ones((dims*dims))
        self.vehicles_per_zone = vehicles_per_zone
    
    def init_grid(self):
        self.grid.generate_trips()

class Grid:
    """Grid-world"""
    def __init__(self,
                 time_stamp,
                 dim = 4,
                 lambda_trip_gen = 4,
                 num_cars = 4,
                 max_wait_time = 5) -> None:
        self.time_stamp = time_stamp
        self.lambda_trip_gen = lambda_trip_gen
        self.num_cars = num_cars
        self.dim = dim
        self.num_zones = dim 
        # self.pending_trips = [] #not certain whether this would be useful
        # self.remaining_trips = [] #not certain whether this would be useful
        self.request_grid = np.zeros(shape = (dim,dim)) 
        average_speed = 50
        self.dist_mat = np.array(np.random.randint(1,100, size=(4,4)))
        for zone in range(self.dim):
            self.dist_mat[zone][zone] = 0
        self.travel_time_mat = self.dist_mat/average_speed
        self.vehicle_grid = np.zeros(shape = (dim, dim))
        self.max_wait_time = max_wait_time
        self.pickup_schedule = []
        self.vehicle_engagement = {}

        
    def init_cars(self, vehicles)->list:
        """Num cars is fixed and uniformly distributed"""
        if vehicles==[]:
            is_gen = True
            print(f"===>> New trips generated for ")
            cars = []
            cars_per_grid = self.num_cars // self.dim
            car_no = 0
            for i in range(self.dim):
                self.vehicle_grid[i][i] = cars_per_grid
                for k in range(cars_per_grid):
                    cars.append(Car(len(vehicles)+car_no, i))
                    car_no+=1
            self.vehicle_grid[self.dim - 1][self.dim - 1] += self.num_cars % cars_per_grid
        else:
            # implement code to decide whether based on the H(w) the driver is 
            # active or chooses to be inactive
            cars =vehicles
            is_gen =False
        return cars, is_gen
    
    def generate_trips(self):

        """A trip can be generated from any source to any destination 
            with a uniform probability. The number of trips from a zone 
            is generated using a Poisson distribution"""

        trips = []
        for source in range(self.num_zones):
            num_trips = np.random.poisson(lam=self.lambda_trip_gen)
            
            for i in range(num_trips):
                destination = np.random.choice([j for j in range(self.num_zones) if j!=source], 
                                      size = 1)[0]
                new_trip = Trip(self.time_stamp,source=source, 
                                destination=destination, pickup_time=0, 
                                waiting_time = 0)
                trips.append(new_trip)
                self.request_grid[source][destination]+=1
        return trips

    def matching(u, v, vehicles, vehicle_engagement, travel_time):
        
        """implements vehicle-passenger matching. First the passengers and vehicles 
        in the same zone are matched, the remaining vehicles are dispatched by casting the 
        matching problem as a Linear Sum Assignment Problem (LAP)
        
        Params:
        - u : np.ndarray, shape = (num_zones,num_zones) : request_grid at a given timestamp
        - v : np.ndarray, shape = (num_zones,num_zones) : vehicle_grid at a given timestamp
        - vehicle_engagement : dict(car_id(int):bool) : something that keeps track of whether a vehicle is currently serving a trip
        - travel_time : np.ndarray, shape = (num_zones,num_zones) : matrix where i,j element denotes time of travel from zone i to zone j
       
         """
        
        
        #match the vehicles and passengers in the same zone first

        matched_pairs = []
        trips_per_zone = u.sum(axis = 1)
        free_cars_per_zone = v.diagonal()
        same_per_zone = np.minimum(trips_per_zone, free_cars_per_zone).tolist()
        for i in range(len(same_per_zone)):
            trips_left = same_per_zone[i]
            while trips_left > 0:
                for car in vehicles:
                    if car.cur_zone == i:
                        car.on_trip = True
                        vehicle_engagement[car.id] = True
                        destination = np.random.choice([k for k in range(len(u)) if u[i][k] != 0])
                        matched_pairs.append((i, i))
                        v[i][i] -= 1
                        
                        u[i][destination] -= 1
                        trips_left -= 1
                        if trips_left == 0:
                            break
            same_per_zone[i] = trips_left
        
        #calc remaining trips and vehicles remaining after initial matching 

        trips_remaining = u.sum(axis = 1).astype(int)
        vehicles_left = (free_cars_per_zone - same_per_zone).astype(int)

        #create the cost-matrix based on travel time
        
        if trips_remaining.sum() > 0 and vehicles_left.sum() > 0:
            row_dict = {}
            sources = []
            for source in range(len(v.diagonal())):
                rem_vehicles = v.diagonal()[source]
                if rem_vehicles>0:    
                    row_dict[source] = []
                    sources.append(source)
                while rem_vehicles > 0:
                    cost_row = travel_time[source]
                    cost_row[u.sum(axis=1) == 0] = INF
                    row_dict[source].append(cost_row)
                    rem_vehicles -= 1
            rows = []
            for _,val in row_dict.items():
                rows.append(val[0])
            cost_matrix = np.zeros_like(v)
            cost_matrix[sources] = np.array(rows)
            cost_matrix[cost_matrix == 0] = INF
            rids, cids = linear_sum_assignment(cost_matrix)
            for t in list(zip(rids,cids)):
                
                if cost_matrix[t] != INF:
                    i = min(len(row_dict[t[0]]), u.sum(axis = 1)[t[1]])
                    
                    while i > 0:
                        i -= 1    
                        matched_pairs.append(t)
                        v[t[0]][t[0]] -= 1
                        v[t[0]][t[1]] += 1
                        dest = np.random.choice(np.argwhere(u[t[1]]>0).flatten())
                        u[t[1]][dest] -= 1 
                        row_dict[t[0]].pop()
                        if len(row_dict[t[0]]) == 0:
                            row_dict.pop(t[0])

            #At this stage, same zone and least time cost traveller-passenger matching has 
            #been completed. If there are remaining cabs and trips, those are being matched
            #by the least time cost of the remaining potential trips.
                
            for source in row_dict:
                if u.sum() > 0:
                    possible_dests = np.argwhere(u.sum(axis = 1) > 0).flatten()
                    min_time = np.inf
                    dest = 0
                    for pd in possible_dests:
                        if travel_time[source][pd] < min_time:
                            min_time = travel_time[source][pd]
                            dest = pd
                    #dest = np.random.choice(np.argwhere(u.sum(axis = 1) > 0).flatten())
                    matched_pairs.append((source,dest))
                    dest2 = np.random.choice(np.argwhere(u[dest]>0).flatten())
                    u[dest][dest2] -= 1
                    v[source][source] -= 1
                    v[source][dest] += 1
                    
                
        return matched_pairs, u, v

    
class TripTracker():
    def __init__(self) -> None:
        self.unassigned: list[Trip] = []
        self.assigned: list[Trip] = []
        self.active: list[Trip] = []
    
    def add_new_trips(self, trips):
        self.unassigned.extend(trips)
    
    def assign_trips(self, matched_trips, vehicleInfo):
        """
        Assigns trips to vehicles, creates a delta grid to be added to existing
        grid to for both the requests and vehicle positions. Shifts Trips from 
        self.unassigned to self.assigned class
        """
        [vehicles, zone_info] = matched_trips
        vehicle_delta = np.zeros((grd_conf.DIM, grd_conf.DIM))
        request_delta = np.zeros((grd_conf.DIM, grd_conf.DIM))
        for idx in range(vehicles):
            # search vehicle
            veh_found = False
            for veh in vehicleInfo:
                if veh.id == idx:
                    vehicle = veh
                    veh_found = not veh_found
            if not veh_found:
                raise Exception("Sorry, vehicle id not found")
            veh_loc, pickup_zone = zone_info[idx]
            for trip_idx in range(len(self.unassigned)):
                trip = self.unassigned[trip_idx]
                if trip.source == pickup_zone:
                    # update trip details
                    trip.assigned = 1
                    trip.vehicle = vehicle
                    
                    self.assigned.append()
                    