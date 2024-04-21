import numpy as np
import math
from typing import List, Dict, Any
from .config import Trip as trip_conf
from .config import Simulation as sim_conf
from .Sim_Actors import Trip, Car
import utils.config as cfg
from utils.config import HyperParams as h
import pdb

# model defs


class Grid:
    """Grid-world"""
    def __init__(self,
                 time_stamp,
                 dim = 4,
                 lambda_trip_gen = 4,
                 num_cars = 16,
                 max_wait_time = 5) -> None:
        self.time_stamp = time_stamp
        self.lambda_trip_gen = lambda_trip_gen
        self.num_cars = num_cars
        self.dim = dim
        self.num_zones = dim 
        self.request_grid = np.zeros(shape = (dim,dim)) 
        self.vehicle_grid = np.zeros(shape = (dim, dim))
        self.max_wait_time = max_wait_time
        self.pickup_schedule = []
        self.vehicle_engagement = {}
        self.px_i = np.ones(shape=dim)
        self.total_idle_stay_time = np.zeros(shape=dim) #per zone
        self.total_idle_cars = np.zeros(shape=dim) #per zone
        self.zonal_profit = np.zeros(shape=dim)
        self.vehicle_transition_matrix =  np.zeros(shape = (dim,dim)) 

        
    def init_cars(self, vehicles)->list:
        """Num cars is fixed and uniformly distributed"""
        self.vehicle_grid = np.zeros(shape = (self.dim, self.dim))
        cars = []
        is_gen = False
        if not vehicles:
            is_gen = True
            for veh_id in range(self.num_cars):
                loc = np.random.choice(self.dim)
                car = Car(veh_id, loc)
                self.vehicle_grid[loc][loc] += 1
                cars.append(car)
            
        else:
            # implement code to decide whether based on the H(w) the driver is 
            # active or chooses to be inactive
            cars = vehicles
            is_gen = False
        
        return cars, is_gen
    
    def generate_trips(self, pickup_time):

        """A trip can be generated from any source to any destination 
            with a uniform probability. The number of trips from a zone 
            is generated using a Poisson distribution"""

        trips = []
        for source in range(self.num_zones):
            num_trips = np.random.poisson(lam=self.lambda_trip_gen)
            # print(f"Number of trips generated at request grid loc {source} == {num_trips}")
            for _ in range(num_trips):
                destination = np.random.choice([j for j in range(self.num_zones) if j!=source], 
                                      size = 1)[0]
                # print(destination,self.request_grid)
                new_trip = Trip(self.time_stamp,source=source, 
                                destination=destination, 
                                pickup_time=pickup_time, 
                                waiting_time = 0, 
                                time_taken = cfg.TRAVEL_TIME_MATRIX[source][destination], 
                                dist = cfg.DIST_MATRIX[source][destination])
                trips.append(new_trip)
                self.request_grid[source][destination]+=1
        return trips

    def get_idle_vehicle_per_zone(self):
        return self.total_idle_cars
    
    def get_idle_time_per_zone(self):
        return self.total_idle_stay_time
    
    def idle_car_per_zone_increase(self, zone):
        self.total_idle_cars[zone] += 1
    
    def idle_time_per_zone_increase(self, zone):
        self.total_idle_stay_time[zone] += 1

    def get_lambda(self):
        a = self.get_idle_time_per_zone()[:]
        b = self.get_idle_vehicle_per_zone()[:]
        avg_stay_time = np.divide(a, b, out=np.zeros_like(a), where=b!=0)
        avg_stay_time = np.nan_to_num(avg_stay_time)
        return np.reciprocal(avg_stay_time, out=np.zeros_like(a), where=b!=0)
    
    def update_transition_matrix(self):
        dist_mat = cfg.DIST_MATRIX
        for i in range(self.dim):
            total_prof_per_dist = 0
            for j in range(self.dim):
                if i==j:
                    self.vehicle_transition_matrix[i][j] = 0
                else:
                    self.vehicle_transition_matrix[i][j] = self.zonal_profit[j]/dist_mat[i][j] 
                    total_prof_per_dist += self.zonal_profit[j]/dist_mat[i][j]
            
            self.vehicle_transition_matrix[i] = np.divide(self.vehicle_transition_matrix[i], total_prof_per_dist, 
                                                          out=np.zeros_like(self.vehicle_transition_matrix[i]), 
                                                          where=total_prof_per_dist!=0)
            
    def idle_no_reposition_loss(self,loc):
        self.zonal_profit[loc] -= h.beta3

    def idle_reposition_loss(self,loc, dist, time):
        self.zonal_profit[loc] -= (h.beta3 * time + h.alpha3 * dist)    
                    
   
class TripTracker(): 
    def __init__(self, grid:Grid) -> None:
        self.unassigned: list[Trip] = []
        self.assigned: list[Trip] = []
        self.active: list[Trip] = []
        self.completed: list[Trip] = []
        self.grid = grid
    
    def add_new_trips(self, trips):
        self.unassigned.extend(trips)
        for trp in self.unassigned:
            if trp.source==trp.destination:
                print(trp)

    def pop_expired_trips(self, curr_time, request_grid_prime):
        """Returns the request grid after popping from the unassigned list"""
        #print(f'>>>>>>>>Unassigned _trips : {len(self.unassigned)} Request_grid = \n',f'{request_grid_prime}')
        to_pop = []
        for trip in self.unassigned:
            if curr_time-trip.trip_gen_time>=trip_conf.MAX_REQUEST_WAITING_TIME:
                   # print(f"@@@@@@@@@@@\n\nLOSS: TRIP {trip.id} waited for ",
                    #      f"too long and now no more wanting a ride ",
                    #      f"--{(trip.source, trip.destination)}\n\n@@@@@@@@@@@",
                    #      trip)
                    to_pop.append(trip)
                    request_grid_prime[trip.source][trip.destination]-=1
        for t in to_pop:
            self.unassigned.pop(self.unassigned.index(t))
       # print(f'>>>>>>>>Unassigned _trips : {len(self.unassigned)} Request_grid = \n',f'{request_grid_prime}')
        return request_grid_prime
    
    def update_trips(self, curr_time, veh_grid ,all_vehicles):
        """
        Check if the vehicle has reached the pickup zone by comparing the 
        current time to the pickup time, change status of trip.assigned if 
        pickup is done else wait. If the vehicle has reached destination time, 
        end trip free vehicle.
        """
        #print(f'>> Current Time = {curr_time}')
        to_pop = []
        for trip in self.assigned:
            vehicle = all_vehicles[trip.vehicle]
            if trip.pickup_time>curr_time and trip.assigned==1:
                #print(0,trip.id)
                pass # yet to reach the pickup zone; do NOTHING
            elif trip.pickup_time==curr_time and trip.assigned ==1:
                # reached pickup
                #print(1, trip)
                trip.assigned = 2
                i = vehicle.loc
                j = trip.source
                veh_grid[i][j] -= 1
                if (veh_grid < 0).sum() > 0:
                    pdb.set_trace()
                #print(f'1. Subtracting from{(i,j)}')
                k = trip.destination
                veh_grid[j][k] += 1
                #print(f'1. Adding to {(j,k)}')
                vehicle.loc = j
                trip.pickup_time = curr_time + cfg.TRAVEL_TIME_MATRIX[j][k]
                if trip.pickup_time > 600:
                    pdb.set_trace()
                #print(f"Trip({trip.id}) status changed: \n\t\tStatus: Passenger Pickup Up\n\t\tVeh Loc:{j}\n\t\tDrop Time:{trip.pickup_time}\n\t\tDrop Loc : {j}")
            elif trip.pickup_time>curr_time and trip.assigned ==2:
                #print(0.1,trip)
                pass # yet to reach the drop of zone; do NOTHING
            elif trip.pickup_time == curr_time and trip.assigned == 2:
               # print(2, trip)
                trip.assigned = 0
                i = vehicle.loc
                # print(trip)
                j = trip.destination
                veh_grid[i][j] -= 1
                if (veh_grid < 0).sum() > 0:
                    pdb.set_trace()
                veh_grid[j][j] += 1
                #print(f'2. Subtracting from{(i,j)}')
                #print(f'2. Adding to {(j,j)}')
                vehicle.idle = True
                vehicle.loc = j
                vehicle.trip = None
                to_pop.append(trip)
                #print(f"Trip({trip.id}) status changed: \n\t\tStatus: Passenger Dropped\n\t\tVeh Loc:{j}\n\t\tDrop Time:{trip.pickup_time}\n\t\tDrop Loc : {j}")
                vehicle.end_trip(curr_time)
            
            else:
                #print(4, trip)
                continue
            
        
        for t in to_pop:
            self.completed.append(self.assigned.pop(self.assigned.index(t)))
        
    def assign_trips_new(self,curr_time:int, matching_info,all_vehicles:list[Car] ,request_grid, vehicle_grid):
            
            
            for matches in matching_info:
                vehicle_loc, pickup_loc = matches
                # print('tre', vehicle_loc, pickup_loc)
                pickup_car = None
                trip = None
                
                for vehicle in all_vehicles:
                    if vehicle.loc == vehicle_loc and vehicle.idle:
                        pickup_car = vehicle
                        
                        break
                if pickup_car is None:
                    #print('No Vehicle')
                    continue
                
                for tr in self.unassigned:
                    if tr.source == pickup_loc:
                        trip = tr
                        break
                if trip is None:
                    #print('No Trip matching reqs')
                    continue
                    
                dest = trip.destination
                
                # print('12,',vehicle_grid[vehicle_loc][vehicle_loc])
                if vehicle_grid[vehicle_loc][vehicle_loc]:
                    trip.vehicle = pickup_car.id
                    pickup_car.take_trip(trip.id,self.grid,curr_time)
                    pickup_car.reset_idle_time()
                    vehicle_grid[vehicle_loc][vehicle_loc] -= 1
                    if vehicle_loc != pickup_loc:
                        vehicle_grid[vehicle_loc][pickup_loc] += 1
                        trip.pickup_time = curr_time + cfg.TRAVEL_TIME_MATRIX[vehicle_loc][pickup_loc]
                        if trip.pickup_time>600:
                            pdb.set_Trace()
                        trip.assigned = 1
                    else: 
                        vehicle_grid[vehicle_loc][dest] += 1
                        trip.pickup_time = curr_time + cfg.TRAVEL_TIME_MATRIX[vehicle_loc][dest]
                        if trip.pickup_time > 600:
                            pdb.set_trace()
                        trip.assigned = 2
                        request_grid[pickup_loc][dest] -= 1
                        self.grid.zonal_profit[trip.source] += trip.cal_amount()
                    assigned_trip = self.unassigned.pop(self.unassigned.index(trip))
                    self.assigned.append(assigned_trip)
                    
                
            return vehicle_grid[:], request_grid[:]
                
            