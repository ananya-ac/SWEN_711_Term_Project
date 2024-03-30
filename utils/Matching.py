import numpy as np
from scipy.optimize import linear_sum_assignment

def matching(u, v, vehicles, vehicle_engagement, travel_time):
    
    """implements vehicle-passenger matching. First the passengers and vehicles 
    in the same zone are matched, the remaining vehicles are dispatched by casting the 
    matching problem as a Linear Sum Assignment Problem (LAP)
    
    Params:
    - u : np.ndarray, shape = (num_zones,num_zones) : request_grid at a given timestamp
    - v : np.ndarray, shape = (num_zones,num_zones) : vehicle_grid at a given timestamp
    - vehicle_engagement : dict(car_id(int):bool) : something that keeps track of whether a vehicle is currently serving a trip
    - travel_time : np.ndarray, shape = (num_zones,num_zones) : matrix where i,j element denotes time of travel from zone i to zone j
    
        """
    
    
    #match the vehicles and passengers in the same zone first

    matched_pairs = []
    trips_per_zone = u.sum(axis = 1)
    free_cars_per_zone = v.diagonal()
    same_per_zone = np.minimum(trips_per_zone, free_cars_per_zone).tolist()
    for i in range(len(same_per_zone)):
        trips_left = same_per_zone[i]
        while trips_left > 0:
            for car in vehicles:
                if car.cur_zone == i:
                    car.on_trip = True
                    vehicle_engagement[car.id] = True
                    destination = np.random.choice([k for k in range(len(u)) if u[i][k] != 0])
                    matched_pairs.append((i, i))
                    v[i][i] -= 1
                    
                    u[i][destination] -= 1
                    trips_left -= 1
                    if trips_left == 0:
                        break
        same_per_zone[i] = trips_left
    
    #calc remaining trips and vehicles remaining after initial matching 

    trips_remaining = u.sum(axis = 1).astype(int)
    vehicles_left = (free_cars_per_zone - same_per_zone).astype(int)

    #create the cost-matrix based on travel time
    
    if trips_remaining.sum() > 0 and vehicles_left.sum() > 0:
        row_dict = {}
        sources = []
        for source in range(len(v.diagonal())):
            rem_vehicles = v.diagonal()[source]
            if rem_vehicles>0:    
                row_dict[source] = []
                sources.append(source)
            while rem_vehicles > 0:
                cost_row = travel_time[source]
                cost_row[u.sum(axis=1) == 0] = INF
                row_dict[source].append(cost_row)
                rem_vehicles -= 1
        rows = []
        for _,val in row_dict.items():
            rows.append(val[0])
        cost_matrix = np.zeros_like(v)
        cost_matrix[sources] = np.array(rows)
        cost_matrix[cost_matrix == 0] = INF
        rids, cids = linear_sum_assignment(cost_matrix)
        for t in list(zip(rids,cids)):
            
            if cost_matrix[t] != INF:
                i = min(len(row_dict[t[0]]), u.sum(axis = 1)[t[1]])
                
                while i > 0:
                    i -= 1    
                    matched_pairs.append(t)
                    v[t[0]][t[0]] -= 1
                    v[t[0]][t[1]] += 1
                    dest = np.random.choice(np.argwhere(u[t[1]]>0).flatten())
                    u[t[1]][dest] -= 1 
                    row_dict[t[0]].pop()
                    if len(row_dict[t[0]]) == 0:
                        row_dict.pop(t[0])

        #At this stage, same zone and least time cost traveller-passenger matching has 
        #been completed. If there are remaining cabs and trips, those are being matched
        #by the least time cost of the remaining potential trips.
            
        for source in row_dict:
            if u.sum() > 0:
                possible_dests = np.argwhere(u.sum(axis = 1) > 0).flatten()
                min_time = np.inf
                dest = 0
                for pd in possible_dests:
                    if travel_time[source][pd] < min_time:
                        min_time = travel_time[source][pd]
                        dest = pd
                #dest = np.random.choice(np.argwhere(u.sum(axis = 1) > 0).flatten())
                matched_pairs.append((source,dest))
                dest2 = np.random.choice(np.argwhere(u[dest]>0).flatten())
                u[dest][dest2] -= 1
                v[source][source] -= 1
                v[source][dest] += 1
                
            
    return matched_pairs, u, v