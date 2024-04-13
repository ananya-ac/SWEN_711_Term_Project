import uuid
import numpy as np

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
    
    def take_trip(self, trip_id):
        self.idle = False
        self.trip = trip_id
    
    def __str__(self) -> str:
        string = f"Car No:{self.id} Loc:{self.loc} "
        string+= f"Idling:{self.idle} Trip:{self.trip} "
        # if self.pickup_time:
        #     string+= f'Pickup Time : {self.pickup_time}'
        return string

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

    def __init__(self, gen_time, source: int, destination: int,
                 pickup_time: int=0, waiting_time:int = 0) -> None:
        self.id = str(uuid.uuid4())[:8]
        self.source = source
        self.destination = destination
        self.waiting_time = waiting_time
        self.trip_gen_time = gen_time
        self.pickup_time = pickup_time
        self.assigned = 0 
        self.vehicle = None
    
    
    def assign(self, vehicle_id):
        """assign this trip to a car"""
        self.assigned +=1
        self.vehicle = vehicle_id
        

    def __str__(self):
        return "\t>> id:{} status:{} source:{} destination:{} time_gen:{}".format(
            self.id,self.assigned, self.source,self.destination,self.trip_gen_time)

