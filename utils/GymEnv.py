import gymnasium as gym
from gymnasium import Env
from gymnasium.spaces import Box,Dict
import numpy as np
from utils.sim_world import Grid, TripTracker
from utils.Matching import matching
from utils.Sim_Actors import Trip
from utils.config import MainParmas as cfg
from utils.config import DIST_MATRIX, TRAVEL_TIME_MATRIX
import math, pickle

class RideGrid(Env):

  def __init__(self, saved_trips:str):

    self.done = False
    self.action_space = Box(low = np.ones(shape = (4)) * 0.5, high = np.ones(shape = (4)) * 2.0)
    spaces = {"vehicle_grid": Box(low = np.zeros(shape = (4,4)), high = np.ones(shape = (4,4)) * 4),
              "request_grid": Box(low = np.zeros(shape = (4,4)), high = np.ones(shape = (4,4)) * 4),
              "zonal_revenue": Box(low = np.zeros(shape = 4), high = np.ones(shape = 4) * 100000000),
              "zonal_idle_time" : Box(low = np.zeros(shape = 4), high = np.ones(shape = 4) * 100000)}
    self.observation_space = Dict(spaces)
    self.trip_tracker = None
    self.all_vehicles = None
    with open(saved_trips, "rb") as f:
        self.trips = pickle.load(f)
    

  def step(self, action):

    self.grid.px_i = action
    if self.curr_time > 3:
        self.grid.request_grid = self.trip_tracker.pop_expired_trips(self.curr_time, self.grid.request_grid)
    # if self.curr_time % 3 == 0:  #and self.curr_time < 10:
    #     print(f'Generating New Trips @ Curr time == {self.curr_time}!!')
    if self.curr_time<950:
        to_be_added = [t for t in self.trips if t.pickup_time == self.curr_time and t.source!=t.destination ]
        for t in to_be_added:
            self.trips.pop(self.trips.index(t))
            # print(t)
        for t in to_be_added:
            self.grid.request_grid[t.source][t.destination] += 1
        # print(f"new_trips_added = {len(to_be_added)}")
        self.trip_tracker.add_new_trips(to_be_added)
    # delete = []
    # for tr in range(len(self.trip_tracker.assigned)):
    #     if self.trip_tracker.assigned[tr].pickup_time < self.curr_time:
    #         delete.append(self.trip_tracker.assigned[tr])
    
    
        
            


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

    count_repos = 0
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
                count_repos+=1
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

    
    # REWARD
    reward = self.grid.zonal_profit.sum() 
    #Check Done
    if self.curr_time == 1000:
      self.done = True
    print('Step-{0} Price Mult avg -{1:.2f} Repositioned Vehicles -{2} REWARD - {3}'.format(
        self.curr_time,
        float(np.sum(self.grid.px_i)/self.grid.px_i.shape[0]), count_repos, reward))
    # print(f'Reward- {reward}')
    # print(len(self.trip_tracker.assigned))
    # for i in self.trip_tracker.assigned:
    #     print(i)
    # print('\n')
    # for i in self.trip_tracker.unassigned:
    #     print(i)
    # print(len(self.trip_tracker.unassigned))
    # print(action)
    # print(self.grid.request_grid)
    self.curr_time+=1
    return observation, reward, self.done, False, {}

  def reset(self, seed = None):

    all_vehicles = []
    curr_time = 0
    num_cars = 4

    self.grid= Grid(curr_time, dim = 4,
               lambda_trip_gen = 4,
               num_cars = num_cars,
               max_wait_time = 5)

    self.trip_tracker = TripTracker(grid=self.grid)
    self.grid.zonal_profit = np.ones(shape=self.grid.dim)
    self.all_vehicles = []
    self.done = False
    veh, _ = self.grid.init_cars(self.all_vehicles)
    self.all_vehicles.extend(veh)
    self.curr_time = 0

    return ({'vehicle_grid' : self.grid.vehicle_grid,
            'request_grid' : np.zeros(shape = (self.grid.dim, self.grid.dim)),
            'zonal_revenue' : np.zeros(shape = self.grid.dim),
            'zonal_idle_time' : np.zeros(shape = self.grid.dim)}, {})
