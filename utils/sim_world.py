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
                    