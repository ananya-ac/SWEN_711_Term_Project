import numpy as np
from typing import List, Dict, Any
from .config import Grid as grd_conf
from .config import Simulation as sim_conf

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
    def __init__(self, dim = grd_conf.DIM, 
                 lambda_trip_gen = grd_conf.LAMBDA_TRIP_GEN, 
                 num_cars = 16) -> None:
        
        self.lambda_trip_gen = lambda_trip_gen
        # self.num_cars = num_cars
        self.dim = dim
        self.num_zones = dim * dim
        self.request_grid = np.zeros((dim, dim)) #stores count of unserved trips from zone(i) to dest(j)
        self.active_vehicles = np.zeros((dim, dim))
        
        # self.pending_trips = [] #not certain whether this would be useful
        # self.remaining_trips = [] #not certain whether this would be useful
        
    def generate_trips(self):

        """A trip can be generated from any source to any destination 
            with a uniform probability. The number of trips from a zone 
            is generated using a Poisson distribution"""

        
        for zone in range(self.num_zones):
            num_trips = np.random.poisson(lam=self.lambda_trip_gen)
            _zone_trip = []
            for i in range(num_trips):
                destination = np.random.choice([j for j in range(self.num_zones) if j!=zone], 
                                      size = 1)[0]
                self.request_grid[zone][destination]+=1
        return True
    
    def initialize_vehicles_in_grid(self,dims, vehicle_per_zone):
        return np.ones_like((dims,dims))*vehicle_per_zone
        
    
    def get_dims(self):
        return self.dim
