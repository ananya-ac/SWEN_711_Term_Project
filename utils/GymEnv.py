import gym
from gym import Env,spaces
from gym.spaces import Box,Dict
import numpy as np
from utils.sim_world import Grid, TripTracker
from utils import match
from utils.Matching import matching
from utils.Sim_Actors import Trip
from utils.config import MainParmas as cfg
from utils.config import DIST_MATRIX, TRAVEL_TIME_MATRIX
import math

class RideGrid(Env):

  def __init__(self, grid):

    self.done = False
    self.grid = grid
    self.action_space = Box(low = np.ones(shape = (self.grid.dim)) * 0.5, high = np.ones(shape = (self.grid.dim)) * 2.0)
    spaces = {"vehicle_grid": Box(low = np.zeros(shape = (self.grid.dim,self.grid.dim)), high = np.ones(shape = (self.grid.dim,grid.dim)) * 4),
              "request_grid": Box(low = np.zeros(shape = (self.grid.dim,self.grid.dim)), high = np.ones(shape = (self.grid.dim,grid.dim)) * 4),
              "zonal_revenue": Box(low = np.zeros(shape = self.grid.dim), high = np.ones(shape = self.grid.dim) * 100000000),
              "zonal_idle_time" : Box(low = np.zeros(shape = self.grid.dim), high = np.ones(shape = self.grid.dim) * 100000)}
    self.observation_space = Dict(spaces)

  def step(self, action):

    
    if self.curr_time > 3:
        self.grid.request_grid = self.trip_tracker.pop_expired_trips(self.curr_time, self.grid.request_grid)
    if self.curr_time % 3 == 0 and self.curr_time > 1 and self.curr_time < 10:
        print(f'Generating New Trips @ Curr time == {self.curr_time}!!')
        self.trip_tracker.add_new_trips(self.grid.generate_trips(self.curr_time))

    ##### match trips

    matching_info =  matching(
        u=self.grid.request_grid[:],
        v=self.grid.vehicle_grid[:],
        vehicles=self.all_vehicles,
        vehicle_engagement={}
        )

    self.grid.vehicle_grid, self.grid.request_grid = self.trip_tracker.assign_trips_new(self.curr_time,
                                    matching_info,
                                    self.all_vehicles,
                                    self.grid.request_grid,
                                    self.grid.vehicle_grid)
    # print('Request Grid post matching\n',request_grid_prime)
    # grid.vehicle_grid = vehicle_grid_prime
    # grid.request_grid = request_grid_prime

    # print(f"After matching at Time = {curr_time}",grid.request_grid.sum(axis=1), grid.vehicle_grid.diagonal())
    self.trip_tracker.update_trips(self.curr_time, self.grid.vehicle_grid, self.all_vehicles)

    # print("############# Unassigned Trips\n")
    # for i in trip_tracker.unassigned:
    #     print(i)
    # print("############# Assigned Trips\n")
    # for i in trip_tracker.assigned:
    #     print(i)


    for veh in self.all_vehicles:
        if veh.idle: #There is a problem here. When a vehicle makes a drop at this timestep, 
            veh.idle_time_increase() #it is marked as idle and it contributes to negative reward.
            self.grid.idle_time_per_zone_increase(veh.get_location())
            if veh.get_idle_time() == 1:
                self.grid.idle_car_per_zone_increase(veh.get_location())
            
            relocation_state, confidence = veh.relocate_to(self.grid.get_lambda()[veh.loc], 
                            self.grid.vehicle_transition_matrix)
            
            if relocation_state == -1:
                self.grid.idle_no_reposition_loss(veh.loc) 
            else:
                #print(f"Veh :{veh.id} Curr_loc : {veh.loc} Reloc Confidence : {confidence} State = {relocation_state}")
                reloc_trip = Trip(self.curr_time, 
                            veh.loc,
                            relocation_state,
                            DIST_MATRIX[veh.loc][relocation_state],
                            TRAVEL_TIME_MATRIX[veh.loc][relocation_state],
                            pickup_time = self.curr_time + math.ceil(
                                TRAVEL_TIME_MATRIX[veh.loc][relocation_state]))
                reloc_trip.assigned = 2
                reloc_trip.vehicle = veh.id
                #print(f"New Relocation trip created : {reloc_trip}")
                self.trip_tracker.assigned.append(reloc_trip)
                self.grid.vehicle_grid[veh.loc][relocation_state]+=1
                self.grid.vehicle_grid[veh.loc][veh.loc]-=1
                veh.idle = False
                self.grid.idle_reposition_loss(veh.loc, DIST_MATRIX[veh.loc][relocation_state], 
                                          TRAVEL_TIME_MATRIX[veh.loc][relocation_state])
                # veh_index = all_vehicles.index(veh)
                # all_vehicles[veh_index].idle = False

    try:
        a = self.grid.get_idle_time_per_zone()[:]
        b = self.grid.get_idle_vehicle_per_zone()[:]
        avg_stay_time = np.divide(a, b, out=np.zeros_like(a), where=b!=0)
        avg_stay_time = np.nan_to_num(avg_stay_time)
    except RuntimeWarning:
        print("check for 0/0")
    
     
    observation = {'vehicle_grid' : self.grid.vehicle_grid,
                  'request_grid' : self.grid.request_grid,
                  'zonal_revenue' : self.grid.zonal_profit,
                  'zonal_idle_time' : avg_stay_time}

    self.curr_time+=1
    # REWARD
    reward = self.grid.zonal_profit.sum() 
    #Check Done
    if self.curr_time == 10000:
      self.done = True

    return observation, reward, self.done

  def reset(self):

    all_vehicles = []
    curr_time = 0
    num_cars = 4

    self.grid= Grid(curr_time, dim = 4,
               lambda_trip_gen = 4,
               num_cars = num_cars,
               max_wait_time = 5)

    self.trip_tracker = TripTracker(grid=self.grid)

    self.all_vehicles = []
    self.grid.init_cars(self.all_vehicles)
    self.curr_time = 0

    return {'vehicle_grid' : self.grid.vehicle_grid,
            'request_grid' : np.zeros(shape = (self.grid.dim, self.grid.dim)),
            'zonal_revenue' : np.zeros(shape = self.grid.dim),
            'zonal_idle_time' : np.zeros(shape = self.grid.dim)}

