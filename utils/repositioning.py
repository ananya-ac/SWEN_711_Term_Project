
def update_avg_stay_time(grid,wait_time,zone,curr_time, numcars):
    curr_stay_time = grid.avg_stay_time[zone]
    grid.avg_stay_time[zone] = curr_stay_time + (1/(curr_time)) * (wait_time)
    
