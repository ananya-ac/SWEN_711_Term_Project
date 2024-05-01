# imports

# utility functions
def sort_by_elapsed_time(obj_list:list, key, current_time):
    # implements bucket sort, key = elapsed time
    elapsed_time = {}
    for ele in obj_list:
        elapsed_time[current_time-ele.trip_gen_time] = elapsed_time.get(
            current_time-ele.trip_gen_time, []).append(ele)
    print(elapsed_time)
    sorted_keys = sorted(list(elapsed_time.keys()),reverse=True)
    output = []
    for key in sorted_keys:
        output.extend(elapsed_time[key])
    return output


def match(a,b):
    # return u_i_j, v_ij, [(vehicle.loc,pickup), ...]
    return [],[], [(0,1), (1,2), (3,2), (0,2)]
