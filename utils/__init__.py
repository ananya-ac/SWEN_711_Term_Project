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
    def __init__(self, dim = 4, lambda_trip_gen = 4, num_cars = 4, max_wait_time = 5) -> None:
        
        self.lambda_trip_gen = lambda_trip_gen
        self.num_cars = num_cars
        self.dim = dim
        self.num_zones = dim 
        self.pending_trips = [] #not certain whether this would be useful
        self.remaining_trips = [] #not certain whether this would be useful
        self.request_grid = np.zeros(shape = (dim,dim)) 
        average_speed = 50
        self.dist_mat = np.array(np.random.randint(1,100, size=(4,4)))
        for zone in range(self.dim):
            self.dist_mat[zone][zone] = 0
        self.travel_time = self.dist_mat/average_speed
        self.vehicle_grid = np.zeros(shape = (dim, dim))
        self.max_wait_time = max_wait_time
        self.pickup_schedule = []
        self.vehicle_engagement = {}        

        
    def init_cars(self):
        
        cars_per_grid = self.num_cars // self.dim
        
        for i in range(self.dim):
            self.vehicle_grid[i][i] = cars_per_grid
        
        self.vehicle_grid[self.dim - 1][self.dim - 1] += self.num_cars % cars_per_grid
    
    def generate_trips(self):

        """A trip can be generated from any source to any destination 
            with a uniform probability. The number of trips from a zone 
            is generated using a Poisson distribution"""

        
        for source in range(self.num_zones):
            num_trips = np.random.poisson(lam=self.lambda_trip_gen)
            
            for i in range(num_trips):
                destination = np.random.choice([j for j in range(self.num_zones) if j!=source], 
                                      size = 1)[0]
                
                
                #new_trip = Trip(source=zone, destination=destination, wait_time=0)
                self.request_grid[source][destination]+=1
                #self.pending_trips.append(new_trip)

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

    

        
            
    



            

        
    
    
    
        
    
    

   
