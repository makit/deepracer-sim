import numpy as np
import math

# From https://github.com/hansonjc888/deepracer_rewardfunction/blob/main/New%20racer%20v2.0%20with%20stability%20factor.ipynb

def reward_function(params):
    
    
    ### Toolkit 1 - Subfunction to calculate the angle of vector vs x-axis given 2 waypoints
    def angle(waypoint1, waypoint2):
        anglept = math.degrees(math.atan2(waypoint2[1]-waypoint1[1],waypoint2[0]-waypoint1[0]))
        
        return anglept
    
    ### Toolkit 2 - Normalized score - 2 parameters 
    ### a: factor = +/- 0.8 equivalent to 26.7% peak shift
    ### b: -0.5 on exponential
    def dist_score(on_turn, normal_dist):
        if on_turn == 'right':
            factor = -0.8
        elif on_turn == 'left':
            factor = 0.8
        else:
            factor = 0
        
        score = 10/math.sqrt(2*math.pi)*math.exp(-0.5*(3*normal_dist+factor)**2)
        
        return score
    
    #### Section 1 -wheels on track point <as a multiplier of total score>
    on_track = params['all_wheels_on_track']
    
    if on_track == True:
        reward_multiplier = 1
    else:
        reward_multiplier = 0.3
        
    #### Section 2 -Central line award
    
    
    # Section 2.0 - Inputs
    abs_dist = params['distance_from_center']
    half_track = params['track_width']/2
    
    # Section 2.1 - Calculate the distance from centre, -ve being the left side distance and +ve being the right side distance
    # return absolute distance as 'dist'
    if params['is_left_of_center'] == True:
        dist = -abs_dist
    else:
        dist = abs_dist
    normalized_dist = dist / half_track
        
    
    ### Section 2.2 - Calculate upcoming 5 waypoints turning angle, +ve being to the left, -ve being to the right
    ### summing 5 way points angle delta, in degree
    ### and deciding upcoming's turn direction turn = 'right','left' or 'center'
    
    ## Section 2.2.1 - Inputs for closest waypoints and total waypoint list of tuples
    waypoints = params['waypoints']
    closest_waypoints = params['closest_waypoints']
    
        #1st waypoint number
    first_waypoint_number = params['closest_waypoints'][1]
    
        #2nd waypoint number
    if (first_waypoint_number +1) >(len(waypoints)-1):
        second_waypoint_number = first_waypoint_number + 1 - (len(waypoints)-1)
    else:
        second_waypoint_number = first_waypoint_number + 1
    
        #5th waypoint number
    if (first_waypoint_number +5) >(len(waypoints)-1):
        fifth_waypoint_number = first_waypoint_number + 5 - (len(waypoints)-1)
    else:
        fifth_waypoint_number = first_waypoint_number + 5

        #6th waypoint number
    if (first_waypoint_number +6) >(len(waypoints)-1):
        sixth_waypoint_number = first_waypoint_number + 6 - (len(waypoints)-1)
    else:
        sixth_waypoint_number = first_waypoint_number + 6
    
        ## calculate the angluar difference between 1st waypoint and 5th waypoint
    
    heading_angle = angle(waypoints[fifth_waypoint_number],waypoints[sixth_waypoint_number]) - angle(waypoints[first_waypoint_number],waypoints[second_waypoint_number])
    
    if heading_angle > 180:
        heading_angle = 360 - heading_angle
    elif heading_angle < -180:
        heading_angle = 360 + heading_angle
    
    ## heading left, right or centre
    if heading_angle > 30:
        turn = 'left'
    elif heading_angle < -30:
        turn = 'right'
    else:
        turn = 'center'
    
    ### Section 2.3 - Define the steering score - Maximum being 3.989 pts
    
    reward_distance = dist_score(turn,normalized_dist)
    
    
    ## Section 3 - return the speed reward - Maximum being 2 pts if 4ms-1 and 1 pts for 2ms-1 for center lane, 
    if turn == 'center':
        reward_speed = params['speed']/2
    else:
        reward_speed = min(params['speed'],2)/2
        
        
    ## Section 4 - stable angle when straightline
    heading = params['heading']
    next_heading = angle(waypoints[first_waypoint_number],waypoints[second_waypoint_number])
    direction_diff = abs(heading - next_heading)
    if direction_diff > 180:
        direction_diff = 360 - direction_diff
        
    if turn == 'center':
        if direction_diff > 15:
            reward_heading = 0.6
        else:
            reward_heading = 1
    else:
        if direction_diff > 20:
            reward_heading = 0.8
        else:
            reward_heading = 1
    
    
    ### Section 5 - total reward
    total_reward = reward_multiplier *reward_heading*(reward_distance + reward_speed)
    
    ##reward = {"distance":dist,
    #          "normalized distance": normalized_dist,
    #          "turn": turn,
    #          "heading angle": heading,
    #          "reward for right position":reward_distance,
    #          "reward for right speed":reward_speed,
    #          "heading discount":reward_heading,
    #          "on_the_line_discount":reward_multiplier,
    #          "total reward":total_reward,
    #          "first_waypoint_number": first_waypoint_number,
    #          "second_waypoint_number": second_waypoint_number,
    #          "fifth_waypoint_number": fifth_waypoint_number,
    #          "sixth_waypoint_number":sixth_waypoint_number,
    #          "direction difference":direction_diff}
    
    reward = total_reward
    
    ##return reward
    return float(reward)