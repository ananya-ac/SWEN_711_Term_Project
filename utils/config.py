INF = 99999
average_speed = 30

DIST_MATRIX =           ((0, 30, 60, 60),
                        (30, 0, 90, 60),
                        (60, 90, 0, 30),
                        (60, 60, 30 ,0))




TRAVEL_TIME_MATRIX =   ((1, 1, 2, 2),
                        (1, 1, 3, 2),
                        (2, 3, 1, 1),
                        (2, 2, 1 ,1))

class Grid():
    DIM = 4
    LAMBDA_TRIP_GEN = 0.5

class Simulation():
    VEHICLES_PER_ZONE = 1
    
class Trip():
    MAX_REQUEST_WAITING_TIME = 5

class HyperParams():
    alpha1 = 1 # Per dist revenue of platform
    alpha2 = .3 # Per dist revenue of drivers
    beta1 = 1 # Per time revenue of platform
    beta2 = .3 # Per time revenue of drivers
    mu1 = 1 # Base Income revenue of platform
    mu2 = .3 # Base Income revenue of drivers
    alpha3 = .1 # Penalty per unit distance when idling 
    beta3 = .1 # Penalty per unit time when idling 

    
class MainParmas():
    generate_new_trips = True
    max_runtime = 500
    num_trip_gen_rounds = 20