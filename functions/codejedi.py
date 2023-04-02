import math

# From https://github.com/codejedi-ai/Deepracer/blob/main/Reward%20Function%20V4.ipynb

def reward_function(params):
    ###############################################################################
    '''
    Example of using waypoints and heading to make the car point in the right direction
    '''

    # Read input variables
    waypoints = params['waypoints']
    closest_waypoints = params['closest_waypoints']
    heading = params['heading']
    all_wheels_on_track = params['all_wheels_on_track']
    track_width = params['track_width']
    distance_from_center = params['distance_from_center']
    steering = params['steering_angle']
    is_left_of_center = params['is_left_of_center']
    speed = params["speed"]
    # Initialize the reward with typical value
    reward = 1.0

    # Calculate the direction of the center line based on the closest waypoints
    next_point = waypoints[closest_waypoints[1]]
    prev_point = waypoints[closest_waypoints[0]]

    # Calculate the direction in radius, arctan2(dy, dx), the result is (-pi, pi) in radians
    track_direction = math.atan2(next_point[1] - prev_point[1], next_point[0] - prev_point[0])
    # Convert to degree
    track_direction = math.degrees(track_direction)

    # Calculate the difference between the track direction and the heading direction of the car
    direction_diff = abs(track_direction - heading)
    if direction_diff > 180:
        direction_diff = 360 - direction_diff
        
    direction_diff -= 90
    
    # Calculate the distance from each border
    distance_from_border = 0.5 * track_width - distance_from_center
    #This is my Obscure turning stratagie where the car starts out on the opposite lane of the turning
    # e.g a left turn goes to the right lane and makes the left turn
    
    #Calculate the bonuses for being on the right track
    bonus = 1
    if (direction_diff > 0 and is_left_of_center) or (direction_diff < 0 and not is_left_of_center): 
        bonus = 2
        
    m_3 = 0.5 * track_width
    x = distance_from_center
    fun = -4 * x * (x - m_3) / (m_3 ** 2)
    
    track_position = bonus * fun
    
    SteeringCoef = 1.1
    perferedSteering = direction_diff * SteeringCoef
    turning = math.exp(-(abs(perferedSteering - steering) ** 2))
    
    
    # a linear function that determines the speed of the vehicle the larger the turn slower the car
    # However I am looking forward to make the vehicle constant speed line in indianapolis where slowing down costs

    perferedSpeed = 4/((direction_diff/15) ** 2 + 1)
    speedPoint = math.exp(-(abs(speed - perferedSpeed) ** 2))
    
    if not (all_wheels_on_track and distance_from_border >= 0.05):
        reward = 1e-3
    reward = turning + track_position + speedPoint + speed
    return float(reward)

