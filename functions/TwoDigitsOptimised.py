import math
import numpy as np
from scipy.spatial import KDTree

SHOULD_LOG = False

def logger(*args, **kwargs):
    if SHOULD_LOG:
        print(*args, **kwargs)


def dist(point1, point2):
    return ((point1[0] - point2[0]) ** 2 + (point1[1] - point2[1]) ** 2) ** 0.5


# thanks to https://stackoverflow.com/questions/20924085/python-conversion-between-coordinates
def rect(r, theta):
    """
    theta in degrees
    returns tuple; (float, float); (x,y)
    """

    x = r * math.cos(math.radians(theta))
    y = r * math.sin(math.radians(theta))
    return x, y


# thanks to https://stackoverflow.com/questions/20924085/python-conversion-between-coordinates
def polar(x, y):
    """
    returns r, theta(degrees)
    """

    r = (x ** 2 + y ** 2) ** 0.5
    theta = math.degrees(math.atan2(y, x))
    return r, theta


def angle_mod_360(angle):
    """
    Maps an angle to the interval -180, +180.
    Examples:
    angle_mod_360(362) == 2
    angle_mod_360(270) == -90
    :param angle: angle in degree
    :return: angle in degree. Between -180 and +180
    """

    n = math.floor(angle / 360.0)

    angle_between_0_and_360 = angle - n * 360.0

    if angle_between_0_and_360 <= 180.0:
        return angle_between_0_and_360
    else:
        return angle_between_0_and_360 - 360


def get_waypoints_ordered_in_driving_direction(params):
    # waypoints are always provided in counter clock wise order
    if params["is_reversed"]:  # driving clock wise.
        return list(reversed(params["waypoints"]))
    else:  # driving counter clock wise.
        return params["waypoints"]


def up_sample(waypoints, factor=10):
    """
    Adds extra waypoints in between provided waypoints
    :param waypoints:
    :param factor: integer. E.g. 3 means that the resulting list has 3 times as many points.
    :return:
    """
    p = waypoints
    n = len(p)

    return [
        [
            i / factor * p[int((j + 1) % n)][0] + (1 - i / factor) * p[j][0],
            i / factor * p[int((j + 1) % n)][1] + (1 - i / factor) * p[j][1],
        ]
        for j in range(n)
        for i in range(factor)
    ]

# Cache the upsampling for performance
waypoints = None
kdtree = None

def get_target_point(params):
    global waypoints
    global kdtree

    if waypoints is None:
        waypoints = up_sample(get_waypoints_ordered_in_driving_direction(params), 20)

    if kdtree is None:
        kdtree = KDTree(waypoints)

    car = [params["x"], params["y"]]

    _, i_closest = kdtree.query([car])
    n = len(waypoints)

    waypoints_starting_with_closest = [waypoints[(i + i_closest.item()) % n] for i in range(n)]

    r = params["track_width"] * 0.9

    is_inside = [dist(p, car) < r for p in waypoints_starting_with_closest]
    i_first_outside = is_inside.index(False)

    if i_first_outside < 0:
        # this can only happen if we choose r as big as the entire track
        return waypoints[i_closest.item()]

    rotated_waypoints = [waypoints_starting_with_closest[(i + i_first_outside) % n] for i in range(n)]
    return rotated_waypoints[0]


def get_target_steering_degree(params):
    tx, ty = get_target_point(params)
    car_x = params["x"]
    car_y = params["y"]
    dx = tx - car_x
    dy = ty - car_y
    heading = params["heading"]

    _, target_angle = polar(dx, dy)

    steering_angle = target_angle - heading

    return angle_mod_360(steering_angle)


def score_steer_to_point_ahead(params):
    best_steering_angle = get_target_steering_degree(params)
    steering_angle = params["steering_angle"]

    error = (
        steering_angle - best_steering_angle
    ) / 60.0  # 60 degree is already really bad

    score = 1.0 - abs(error)

    return max(
        score, 0.01
    )  # optimizer is rumored to struggle with negative numbers and numbers too close to zero


def reward_function(params):
    return float(score_steer_to_point_ahead(params))