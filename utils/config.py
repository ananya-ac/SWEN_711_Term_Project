class Grid():
    DIM = 4
    LAMBDA_TRIP_GEN = 2

class Simulation():
    VEHICLES_PER_ZONE = 1
    
class Trip():
    MAX_REQUEST_WAITING_TIME = 5

INF = 99999

class HyperParams():
    alpha1 = 10 # Per dist revenue of platform
    alpha2 = 2 # Per dist revenue of drivers
    beta1 = 1 # Per time revenue of platform
    beta2 = .1 # Per time revenue of drivers
    mu1 = 10 # Base Income revenue of platform
    mu2 = 1 # Base Income revenue of drivers