import math

# From https://github.com/wlfd/aws-deepracer/blob/main/src/optimize/reward_function%20HSBC.py

class Reward:
    def __init__(self):
        self.first_racingpoint_index = 0

    def reward_function(self, params):
        def dist_2_points(x1, x2, y1, y2):
            return abs(abs(x1-x2)**2 + abs(y1-y2)**2)**0.5

        def closest_2_racing_points_index(racing_coords, car_coords):

            # Calculate all distances to racing points
            distances = []
            for i in range(len(racing_coords)):
                distance = dist_2_points(x1=racing_coords[i][0], x2=car_coords[0],
                                         y1=racing_coords[i][1], y2=car_coords[1])
                distances.append(distance)

            # Get index of the closest racing point
            closest_index = distances.index(min(distances))

            # Get index of the second closest racing point
            distances_no_closest = distances.copy()
            distances_no_closest[closest_index] = 999
            second_closest_index = distances_no_closest.index(
                min(distances_no_closest))

            return [closest_index, second_closest_index]

        def dist_to_racing_line(closest_coords, second_closest_coords, car_coords):

            # Calculate the distances between 2 closest racing points
            a = abs(dist_2_points(x1=closest_coords[0],
                                  x2=second_closest_coords[0],
                                  y1=closest_coords[1],
                                  y2=second_closest_coords[1]))

            # Distances between car and closest and second closest racing point
            b = abs(dist_2_points(x1=car_coords[0],
                                  x2=closest_coords[0],
                                  y1=car_coords[1],
                                  y2=closest_coords[1]))
            c = abs(dist_2_points(x1=car_coords[0],
                                  x2=second_closest_coords[0],
                                  y1=car_coords[1],
                                  y2=second_closest_coords[1]))

            # Calculate distance between car and racing line (goes through 2 closest racing points)
            # try-except in case a=0 (rare bug in DeepRacer)
            try:
                distance = abs(-(a**4) + 2*(a**2)*(b**2) + 2*(a**2)*(c**2) -
                               (b**4) + 2*(b**2)*(c**2) - (c**4))**0.5 / (2*a)
            except:
                distance = b

            return distance

        def next_prev_racing_point(closest_coords, second_closest_coords, car_coords, heading):

            # Virtually set the car more into the heading direction
            heading_vector = [math.cos(math.radians(
                heading)), math.sin(math.radians(heading))]
            new_car_coords = [car_coords[0]+heading_vector[0],
                              car_coords[1]+heading_vector[1]]

            # Calculate distance from new car coords to 2 closest racing points
            distance_closest_coords_new = dist_2_points(x1=new_car_coords[0],
                                                        x2=closest_coords[0],
                                                        y1=new_car_coords[1],
                                                        y2=closest_coords[1])
            distance_second_closest_coords_new = dist_2_points(x1=new_car_coords[0],
                                                               x2=second_closest_coords[0],
                                                               y1=new_car_coords[1],
                                                               y2=second_closest_coords[1])

            if distance_closest_coords_new <= distance_second_closest_coords_new:
                next_point_coords = closest_coords
                prev_point_coords = second_closest_coords
            else:
                next_point_coords = second_closest_coords
                prev_point_coords = closest_coords

            return [next_point_coords, prev_point_coords]

        def racing_direction_diff(closest_coords, second_closest_coords, car_coords, heading):

            # Calculate the direction of the center line based on the closest waypoints
            next_point, prev_point = next_prev_racing_point(closest_coords,
                                                            second_closest_coords,
                                                            car_coords,
                                                            heading)

            # Calculate the direction in radius, arctan2(dy, dx), the result is (-pi, pi) in radians
            track_direction = math.atan2(
                next_point[1] - prev_point[1], next_point[0] - prev_point[0])

            # Convert to degree
            track_direction = math.degrees(track_direction)

            # Calculate the difference between the track direction and the heading direction of the car
            direction_diff = abs(track_direction - heading)
            if direction_diff > 180:
                direction_diff = 360 - direction_diff

            return direction_diff

        def indexes_cyclical(start, end, array_len):

            if end < start:
                end += array_len

            return [index % array_len for index in range(start, end)]

        def projected_time(first_index, closest_index, step_count, times_list):

            # Calculate how much time has passed since start
            current_actual_time = (step_count-1) / 15

            # Calculate which indexes were already passed
            indexes_traveled = indexes_cyclical(
                first_index, closest_index, len(times_list))

            # Calculate how much time should have passed if car would have followed optimals
            current_expected_time = sum(
                [times_list[i] for i in indexes_traveled])

            # Calculate how long one entire lap takes if car follows optimals
            total_expected_time = sum(times_list)

            # Calculate how long car would take for entire lap, if it continued like it did until now
            try:
                projected_time = (current_actual_time /
                                  current_expected_time) * total_expected_time
            except:
                projected_time = 9999

            return projected_time

        racing_track = [[3.07458, 0.71464, 4.0, 0.03591],
                        [3.21928, 0.70426, 4.0, 0.03627],
                        [3.36538, 0.6966, 4.0, 0.03657],
                        [3.51258, 0.69117, 4.0, 0.03682],
                        [3.66065, 0.68755, 4.0, 0.03703],
                        [3.80939, 0.68536, 4.0, 0.03719],
                        [3.95861, 0.68423, 4.0, 0.03731],
                        [4.10814, 0.68377, 4.0, 0.03738],
                        [4.25783, 0.68367, 4.0, 0.03742],
                        [4.40759, 0.68373, 4.0, 0.03744],
                        [4.55735, 0.68378, 3.8897, 0.0385],
                        [4.70705, 0.684, 3.53108, 0.04239],
                        [4.85639, 0.68522, 3.24011, 0.04609],
                        [5.00502, 0.68823, 2.99504, 0.04963],
                        [5.15253, 0.69382, 2.78546, 0.053],
                        [5.29844, 0.70281, 2.62144, 0.05576],
                        [5.44222, 0.71591, 2.46196, 0.05864],
                        [5.5833, 0.73375, 2.34749, 0.06058],
                        [5.72106, 0.75693, 2.24181, 0.06231],
                        [5.8548, 0.78594, 2.13139, 0.06421],
                        [5.98382, 0.82119, 2.03144, 0.06584],
                        [6.10745, 0.86288, 1.8985, 0.06872],
                        [6.22498, 0.91118, 1.77193, 0.07171],
                        [6.33586, 0.96601, 1.65518, 0.07473],
                        [6.43956, 1.02721, 1.54139, 0.07812],
                        [6.53548, 1.09465, 1.41602, 0.08281],
                        [6.62301, 1.16811, 1.3, 0.0879],
                        [6.70115, 1.24753, 1.3, 0.08571],
                        [6.76873, 1.33276, 1.3, 0.08367],
                        [6.82444, 1.42345, 1.3, 0.08187],
                        [6.86664, 1.51908, 1.3, 0.0804],
                        [6.89292, 1.6188, 1.3, 0.07932],
                        [6.90033, 1.72078, 1.3486, 0.07582],
                        [6.89028, 1.82236, 1.44808, 0.07049],
                        [6.86515, 1.92186, 1.53292, 0.06695],
                        [6.82676, 2.01829, 1.53292, 0.06771],
                        [6.77472, 2.11031, 1.62469, 0.06507],
                        [6.71032, 2.19715, 1.75122, 0.06174],
                        [6.63504, 2.27849, 1.87293, 0.05918],
                        [6.54996, 2.3541, 2.00357, 0.05681],
                        [6.45603, 2.42388, 2.14948, 0.05443],
                        [6.35417, 2.48785, 2.32677, 0.05169],
                        [6.24532, 2.54621, 2.52974, 0.04882],
                        [6.13039, 2.59931, 2.80244, 0.04518],
                        [6.01036, 2.64768, 3.16604, 0.04087],
                        [5.88626, 2.69206, 3.83414, 0.03437],
                        [5.75934, 2.73355, 3.87852, 0.03443],
                        [5.63097, 2.7735, 3.69056, 0.03643],
                        [5.49668, 2.81546, 3.61538, 0.03891],
                        [5.36296, 2.85868, 3.61538, 0.03887],
                        [5.23025, 2.90414, 3.61538, 0.0388],
                        [5.09891, 2.95265, 3.61538, 0.03872],
                        [4.96923, 3.00477, 3.61538, 0.03866],
                        [4.84137, 3.06085, 3.61538, 0.03862],
                        [4.71542, 3.12104, 3.63105, 0.03845],
                        [4.59138, 3.18532, 3.73573, 0.0374],
                        [4.46916, 3.25346, 3.94424, 0.03548],
                        [4.34859, 3.32508, 4.0, 0.03506],
                        [4.22944, 3.39965, 4.0, 0.03514],
                        [4.1114, 3.47654, 4.0, 0.03522],
                        [3.99414, 3.55506, 3.63253, 0.03885],
                        [3.87735, 3.63453, 3.29657, 0.04285],
                        [3.76274, 3.71288, 3.0559, 0.04543],
                        [3.64758, 3.78995, 2.87912, 0.04813],
                        [3.5315, 3.86477, 2.74525, 0.05031],
                        [3.41412, 3.93638, 2.63989, 0.05208],
                        [3.29518, 4.00388, 2.55276, 0.05357],
                        [3.17446, 4.06642, 2.47613, 0.05491],
                        [3.05186, 4.12321, 2.40437, 0.0562],
                        [2.92741, 4.17355, 2.33463, 0.0575],
                        [2.80124, 4.21681, 2.27041, 0.05874],
                        [2.67365, 4.25242, 2.23346, 0.05931],
                        [2.54507, 4.2799, 2.21694, 0.05931],
                        [2.41606, 4.29881, 2.17493, 0.05995],
                        [2.28731, 4.30877, 2.09757, 0.06157],
                        [2.1596, 4.30946, 2.00311, 0.06376],
                        [2.03378, 4.3007, 1.92453, 0.06553],
                        [1.91065, 4.2826, 1.77748, 0.07002],
                        [1.79084, 4.25548, 1.65869, 0.07406],
                        [1.67502, 4.2195, 1.5602, 0.07773],
                        [1.56398, 4.17456, 1.5602, 0.07678],
                        [1.45867, 4.1204, 1.5602, 0.0759],
                        [1.36003, 4.05691, 1.5602, 0.07519],
                        [1.26976, 3.98322, 1.5602, 0.07469],
                        [1.18983, 3.89866, 1.5602, 0.07458],
                        [1.12261, 3.80271, 1.80331, 0.06496],
                        [1.06571, 3.69874, 1.91524, 0.06188],
                        [1.01862, 3.58785, 2.03515, 0.0592],
                        [0.9809, 3.47094, 2.14724, 0.05721],
                        [0.95228, 3.34873, 2.26594, 0.0554],
                        [0.93248, 3.22188, 2.40544, 0.05337],
                        [0.92115, 3.09111, 2.53729, 0.05173],
                        [0.91796, 2.95716, 2.68173, 0.04996],
                        [0.92253, 2.82083, 2.81269, 0.0485],
                        [0.93446, 2.68299, 2.80817, 0.04927],
                        [0.95342, 2.54453, 2.72046, 0.05137],
                        [0.97924, 2.40644, 2.6322, 0.05337],
                        [1.01179, 2.26978, 2.54965, 0.0551],
                        [1.0509, 2.1356, 2.47123, 0.05656],
                        [1.09639, 2.00481, 2.38875, 0.05797],
                        [1.14811, 1.87819, 2.29362, 0.05963],
                        [1.206, 1.75639, 2.19469, 0.06145],
                        [1.27, 1.63992, 1.97898, 0.06715],
                        [1.34008, 1.52921, 1.97898, 0.06621],
                        [1.41621, 1.42462, 1.97898, 0.06537],
                        [1.49846, 1.32655, 1.97898, 0.06467],
                        [1.587, 1.23554, 1.97898, 0.06417],
                        [1.68215, 1.15225, 1.97898, 0.0639],
                        [1.78514, 1.07863, 2.12168, 0.05966],
                        [1.89477, 1.01369, 2.28841, 0.05568],
                        [2.01011, 0.95652, 2.44758, 0.05259],
                        [2.13044, 0.90643, 2.60622, 0.05001],
                        [2.25524, 0.8629, 2.76417, 0.04782],
                        [2.38407, 0.8255, 2.95175, 0.04545],
                        [2.51649, 0.79375, 3.13649, 0.04342],
                        [2.65214, 0.76727, 3.35603, 0.04118],
                        [2.79063, 0.7456, 3.62474, 0.03867],
                        [2.93157, 0.72824, 3.96018, 0.03586]]

        all_wheels_on_track = params['all_wheels_on_track']
        x = params['x']
        y = params['y']
        heading = params['heading']
        progress = params['progress']
        steps = params['steps']
        speed = params['speed']
        track_width = params['track_width']

        closest_index, second_closest_index = closest_2_racing_points_index(
            racing_track, [x, y])

        # Get optimal [x, y, speed, time] for closest and second closest index
        optimals = racing_track[closest_index]
        optimals_second = racing_track[second_closest_index]

        if steps == 1:
            self.first_racingpoint_index = closest_index

        ### REWARD AND PUNISHMENT ###
        reward = 1

        DISTANCE_MULTIPLE = 1
        dist = dist_to_racing_line(optimals[0:2], optimals_second[0:2], [x, y])
        distance_reward = max(1e-3, 1 - (dist/(track_width*0.5)))
        reward += distance_reward * DISTANCE_MULTIPLE

        ## Reward if speed is close to optimal speed ##
        SPEED_DIFF_NO_REWARD = 1
        SPEED_MULTIPLE = 2
        speed_diff = abs(optimals[2]-speed)
        if speed_diff <= SPEED_DIFF_NO_REWARD:
            # we use quadratic punishment (not linear) bc we're not as confident with the optimal speed
            # so, we do not punish small deviations from optimal speed
            speed_reward = (1 - (speed_diff/(SPEED_DIFF_NO_REWARD))**2)**2
        else:
            speed_reward = 0
        reward += speed_reward * SPEED_MULTIPLE

        # Reward if less steps
        REWARD_PER_STEP_FOR_FASTEST_TIME = 1
        STANDARD_TIME = 37
        FASTEST_TIME = 27
        times_list = [row[3] for row in racing_track]
        proj_time = projected_time(
            self.first_racingpoint_index, closest_index, steps, times_list)

        try:
            steps_prediction = proj_time*15+1
            reward_prediction = max(1e-3, (-REWARD_PER_STEP_FOR_FASTEST_TIME*(FASTEST_TIME) / (
                STANDARD_TIME-FASTEST_TIME))*(steps_prediction-(STANDARD_TIME*15+1)))
            steps_reward = min(REWARD_PER_STEP_FOR_FASTEST_TIME,
                               reward_prediction / steps_prediction)
        except:
            steps_reward = 0

        reward += steps_reward

        direction_diff = racing_direction_diff(
            optimals[0:2], optimals_second[0:2], [x, y], heading)
        if direction_diff > 30:
            reward = 1e-3

        speed_diff_zero = optimals[2]-speed
        if speed_diff_zero > 0.5:
            reward = 1e-3

        ## Incentive for finishing the lap in less steps ##
        # should be adapted to track length and other rewards
        REWARD_FOR_FASTEST_TIME = 1500
        STANDARD_TIME = 37  # seconds (time that is easily done by model)
        FASTEST_TIME = 27  # seconds (best time of 1st place on the track)
        if progress == 100:
            finish_reward = max(1e-3, (-REWARD_FOR_FASTEST_TIME /
                                       (15*(STANDARD_TIME-FASTEST_TIME)))*(steps-STANDARD_TIME*15))
        else:
            finish_reward = 0
        reward += finish_reward

        ## Zero reward if off track ##
        if all_wheels_on_track == False:
            reward = 1e-3

        return float(reward)


reward_object = Reward()  # add parameter verbose=True to get noisy output for testing


def reward_function(params):
    return reward_object.reward_function(params)