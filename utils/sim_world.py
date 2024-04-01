import numpy as np
import math
from typing import List, Dict, Any
from .config import Trip as trip_conf
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
                 num_cars = 16,
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
        self.travel_time_mat = self.dist_mat/average_speed + np.ones(self.dist_mat.shape)
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
            # print(f"Number of trips generated at request grid loc {source} == {num_trips}")
            for _ in range(num_trips):
                destination = np.random.choice([j for j in range(self.num_zones) if j!=source], 
                                      size = 1)[0]
                # print(destination,self.request_grid)
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
        self.completed: list[Trip] = []
    
    def add_new_trips(self, trips):
        self.unassigned.extend(trips)
        for trp in self.unassigned:
            if trp.source==trp.destination:
                print(trp)
    
    def assign_trips(self,curr_time:int, matching_info,all_vehicles:list[Car], travel_time):
        """
        Assigns trips to vehicles, creates a delta grid to be added to existing
        grid to for both the requests and vehicle positions. Shifts Trips from 
        self.unassigned to self.assigned class
        """
        print(matching_info)
        
        # for veh in all_vehicles:
        #     print(veh)
        for idx in range(len(matching_info)):
            # search vehicle
            veh_idx = -1
            for veh in range(len(all_vehicles)):
                if all_vehicles[veh].loc == matching_info[idx][0] and all_vehicles[veh].idle:
                    veh_idx = veh
                    break
            if veh_idx == -1:
                print('No Free vehicles RN!!')
                return True
            elif not all_vehicles[veh].idle:
                print('Vehicle already assigned')
                continue
            pickup_zone = matching_info[idx][1]
            # trimming down the unassigned req
            for trip_idx in range(len(self.unassigned)):
                trip = self.unassigned[trip_idx]
                if curr_time-trip.trip_gen_time>trip_conf.MAX_REQUEST_WAITING_TIME:
                        # print(f"@@@@@@@@@@@\n\nLOSS: TRIP {trip.id} waited for too long and now no more wanting a ride \n\n@@@@@@@@@@@")
                        self.unassigned.pop(trip_idx)
            for trip_idx in range(len(self.unassigned)):
                trip = self.unassigned[trip_idx]
                if trip.source == pickup_zone and matching_info[idx][0]!=matching_info[idx][1]:
                    # update trip details
                    trip.assigned = 1
                    trip.vehicle = all_vehicles[veh_idx].id
                    # print(f"{travel_time}\nTravel Time added = {travel_time[all_vehicles[veh_idx].loc][trip.source]}")
                    trip.pickup_time = curr_time + math.ceil(travel_time[all_vehicles[veh_idx].loc][trip.source])
                    # update vehicle info
                    all_vehicles[veh_idx].idle =False
                    all_vehicles[veh_idx].take_trip(trip.id)
                    # remove from unassigned and append to assigned        
                    self.assigned.append(self.unassigned.pop(trip_idx))
                    # print(f'**********\n\nINFO:Trip: {trip.id} \nStatus => {trip.assigned} \nveh => {trip.vehicle}, \nDestination => {trip.destination}\nNext Drop Time => {trip.pickup_time}\nVehicle => {all_vehicles[veh_idx].__dict__}')
                    # print(trip)
                    break
                elif trip.source == pickup_zone and matching_info[idx][0]==matching_info[idx][1]:
                    # update trip details
                    trip.assigned = 2
                    trip.vehicle = all_vehicles[veh_idx].id
                    trip.pickup_time = curr_time + math.ceil(travel_time[all_vehicles[veh_idx].loc][trip.source])
                    # update vehicle info
                    all_vehicles[veh_idx].idle =False
                    all_vehicles[veh_idx].take_trip(trip.id)
                    # remove from unassigned and append to assigned        
                    self.assigned.append(self.unassigned.pop(trip_idx))
                    break

    def update_trips(self, curr_time, veh_grid ,all_vehicles, travel_time):
        """
        Check if the vehicle has reached the pickup zone by comparing the 
        current time to the pickup time, change status of trip.assigned if 
        pickup is done else wait. If the vehicle has reached destination time, 
        end trip free vehicle.
        """
        # print(self.active)
        for trip in self.assigned:
            vehicle = all_vehicles[trip.vehicle]
            if trip.pickup_time>curr_time and trip.assigned==1:
                pass # yet to reach the pickup zone; do NOTHING
            elif trip.pickup_time==curr_time and trip.assigned ==1:
                # reached pickup
                trip.assigned = (trip.assigned+1)%3
                i = vehicle.loc
                j = trip.source
                veh_grid[i][j] -= 1
                k = trip.destination
                veh_grid[j][k] += 1
                vehicle.loc = j
                trip.pickup_time = curr_time + math.ceil(travel_time[j][k])
                print(f"Trip({trip.id}) status changed: \n\t\tStatus: Passenger Pickup Up\n\t\tVeh Loc:{j}\n\t\tDrop Time:{trip.pickup_time}\n\t\tDrop Loc : {j}")
            elif trip.pickup_time>curr_time and trip.assigned ==2:
                pass # yet to reach the drop of zone; do NOTHING
            else:
                trip.assigned = (trip.assigned+1)%3
                i = vehicle.loc
                j = trip.destination
                veh_grid[i][j] -= 1
                veh_grid[j][j] += 1
                vehicle.idle = True
                self.completed.append(self.assigned.pop(self.assigned.index(trip)))
                print(f"Trip({trip.id}) status changed: \n\t\tStatus: Passenger Dropped\n\t\tVeh Loc:{j}\n\t\tDrop Time:{trip.pickup_time}\n\t\tDrop Loc : {j}")
                
                pass# reached the final drop off zone 
                
            
            