
class Car:
    """A car maybe assigned a trip, otherwise it idles or 
        repositions to a new zone"""
    
    def __init__(self, id: int) -> None:
        
        self.id = id
        self.on_trip = False
        self.trip = None
        

    def take_trip(self, trip):

        self.on_trip = True
        self.trip = trip

    




class Trip:
    
    """A trip has a source, a destination and waiting time"""

    def __init__(self, source: int, destination: int, pickup_time: int) -> None:
        
        self.source = source
        self.destination = destination
        self.pickup_time = pickup_time
        self.assigned = False
    
    
    
    def assign(self):
        """assign this trip to a car"""
        
        self.assigned = True
        

    def __str__(self):
        return "source:{}   destination:{}".format(self.source,self.destination)

