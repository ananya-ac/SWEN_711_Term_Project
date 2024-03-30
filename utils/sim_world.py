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
            print(f"Number of trips generated at request grid loc {source} == {num_trips}")
            for _ in range(num_trips):
                destination = np.random.choice([j for j in range(self.num_zones) if j!=source], 
                                      size = 1)[0]
                print(destination,self.request_grid)
                new_trip = Trip(self.time_stamp,source=source, 
                                destination=destination, pickup_time=0, 
                                waiting_time = 0)
                trips.append(new_trip)
                self.request_grid[source][destination]+=1
        return trips

    def matching(self):
        
        """implements vehicle-passenger matching. First the passengers and vehicles 
        in the same zone are matched, the remaining vehicles are dispatched by casting the 
        matching problem as a Linear Sum Assignment Problem (LAP)"""
        
        
        #match the vehicles and passengers in the same zone first

        trips_per_zone = self.request_grid.sum(axis = 1)
        free_cars_per_zone = self.vehicle_grid.diagonal()
        same_per_zone = np.minimum(trips_per_zone, free_cars_per_zone).astype(int)
        
        
        #calc remaining trips and vehicles remaining after initial matching 

        trips_left = (trips_per_zone - same_per_zone).astype(int)
        vehicles_left = (free_cars_per_zone - same_per_zone).astype(int)

        #create the cost-matrix based on travel time
        if trips_left.sum() > 0 and vehicles_left.sum() > 0:
            # rlist = []
            # clist = []
            # for i in range(self.num_zones):
            #     rlist += [i]*min(sum(trips_left),vehicles_left[i])
            #     clist += [i]*min(sum(vehicles_left),trips_left[i])

            # costs = np.zeros((len(rlist), len(clist)))
            # for i in range(len(rlist)):
            #     costs[i,:] = self.travel_time[rlist[i], clist]
            # for j in range(len(clist)):
            #     costs[:, j] = self.travel_time[rlist, clist[j]]

            
            cost_matrix = np.zeros(shape = (len(vehicles_left), len(trips_left)))
            
        return

    
class TripTracker():
    def __init__(self) -> None:
        self.unassigned: list[Trip] = []
        self.assigned: list[Trip] = []
        self.active: list[Trip] = []
    
    def add_new_trips(self, trips):
        self.unassigned.extend(trips)
    
    def assign_trips(self,curr_time:int, matching_info,all_vehicles:list[Car], travel_time):
        """
        Assigns trips to vehicles, creates a delta grid to be added to existing
        grid to for both the requests and vehicle positions. Shifts Trips from 
        self.unassigned to self.assigned class
        """
        print(matching_info)
        for idx in range(len(matching_info)):
            # search vehicle
            veh_idx = -1
            for veh in range(len(all_vehicles)):
                if all_vehicles[veh].loc == matching_info[idx][0]:
                    veh_idx = veh
                    break
            if veh_idx == -1:
                raise Exception("Sorry, vehicle id not found")
            elif not all_vehicles[veh].idle:
                print('Vehicle already assigned')
                continue
            pickup_zone = matching_info[idx][1]
            for trip_idx in range(len(self.unassigned)):
                trip = self.unassigned[trip_idx]
                if trip.source == pickup_zone:
                    # update trip details
                    trip.assigned = 1
                    trip.vehicle = all_vehicles[veh_idx].id
                    trip.pickup_time = curr_time + travel_time[all_vehicles[veh_idx].loc][trip.source]
                    # update vehicle info
                    all_vehicles[veh_idx].idle =False
                    all_vehicles[veh_idx].take_trip(trip.id)
                    # remove from unassigned and append to assigned        
                    self.assigned.append(self.unassigned.pop(trip_idx))
                    print(f'Trip: {trip.id} => Status => {trip.assigned} veh => {trip.vehicle}')
                    print(trip)
                    break
            