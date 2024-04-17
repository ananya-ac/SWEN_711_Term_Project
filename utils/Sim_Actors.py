import uuid
import numpy as np
from utils.repositioning import update_avg_stay_time
from utils.config import HyperParams as h
class Car:
    """
    A car maybe assigned a trip, otherwise it idles or repositions to a new zone

    Arguments:
    - id : int: unique identifier
    - string : bool : is car active based on current price multiplier
    - idle : bool : True if no trip assigned else False
    - trip : int : Trip id of the assigned trip
    - loc : int : Zone number of vehicle   
    """
    def __init__(self, id: int, loc:int) -> None:
        self.id = id
        self.idle = True
        self.trip = None
        self.loc = loc
        self.idle_time = 0
        self.last_idle_updated = 0
    
    def take_trip(self, trip_id, grid,curr_time):
        # update_avg_stay_time(grid,curr_time- self.last_idle_updated,self.loc,curr_time)
        self.idle = False
        self.trip = trip_id
        self.last_idle_updated = None
        
    def end_trip(self, curr_time):
        self.last_idle_updated = curr_time
    
    def __str__(self) -> str:
        string = f"Car No:{self.id} Loc:{self.loc} "
        string+= f"Idling:{self.idle} Trip:{self.trip} "
        # if self.pickup_time:
        #     string+= f'Pickup Time : {self.pickup_time}'
        return string
    
    def update_zone_stay_time(self):
        pass    

class Trip:
    """
        Trips class encompasses all request related information
        
        Attributes:
        - id : int : unique identifier
        - source : int : pickup zone
        - destination : int : drop off zone
        - waiting_time : int : total time trip has been unassigned for
        - pickup_time : int : time for vehicle to pickup passenger
        - assigned : int :  0 == Unassigned
                            1 == vehicle picking up passenger
                            2 == passenger picked up
        - vehicle : str : id of vehicle that is assigned to a trip
        """

    def __init__(self, gen_time, source: int, destination: int,dist:float, 
                 time_taken:float, pickup_time: int=0, waiting_time:int = 0, px_mult=1
                 ) -> None:
        self.id = str(uuid.uuid4())[:8]
        self.source = source
        self.destination = destination
        self.waiting_time = waiting_time
        self.trip_gen_time = gen_time
        self.pickup_time = pickup_time
        self.assigned = 0 
        self.vehicle = None
        self.amount = 0
        self.px_mult = px_mult
        self.distance = dist
        self.time = time_taken
        
    def cal_amount(self):
        return self.px_mult * (h.mu1-h.mu2+self.distance*(h.alpha1-h.alpha2)+self.time*(h.beta1-h.beta2))
    
    def assign(self, vehicle_id):
        """assign this trip to a car"""
        self.assigned +=1
        self.vehicle = vehicle_id

    def __str__(self):
        return "\t>> id:{} assigned:{} source:{} destination:{} time_gen:{} pickup_time:{}".format(
            self.id,self.assigned, self.source,self.destination,self.trip_gen_time, self.pickup_time)

