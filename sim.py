#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import concurrent.futures
import copy
import math
import time
import pygame

from pygame.math import Vector2

from track_loader import Track_Loader

from functions import TwoDigitsOptimised as deepracer

# Constants
TRACK = "jyllandsringen_pro_cw"
TITLE = "DeepRacer Simulator"
DEBUG_LOG = False
FRAME_RATE = 15  # fps - DeepRacer runs the function at 15 fps
SCREEN_RATE = 80  # % of screen size
TAIL_LENGTH = 100
MIN_REWARD = 0.0001
STEERING_ANGLE = [-30, -15, -5, 0, 5, 15, 30]
SPEEDS = [2,3,4]
DEFAULT_SPEED = 3.0
BOTS_COUNT = 0
BOTS_SPEED = 0
FONT_FACE = "assets/FreeSansBold.ttf"
FONT_SIZE = 24
CAR_BOT = "assets/car-gray.png"
CAR_CONTROLLED = "assets/car-blue.png"
CAR_CRASHED = "assets/car-red.png"
CAR_OFFTRACK = "assets/car-purple.png"
CAR_ORIGIN = "assets/car-green.png"
CAR_WARNED = "assets/car-yello.png"
COLOR_CENTER = (242, 156, 56)
COLOR_CIRCLE = (250, 250, 250)
COLOR_FLOOR = (87, 191, 141)
COLOR_OBJECT = (250, 200, 100)
COLOR_ROAD = (37, 47, 61)
COLOR_SHORTCUT = (150, 150, 150)
COLOR_TRACK = (255, 255, 255)
COLOR_RAY = (100, 255, 255)
COLOR_RAY_TRACK = (255, 100, 100)
COLOR_RAY_SHORTCUT = (255, 255, 100)
COLOR_TEXT = (255, 255, 100)

# Global variables
g_scr_adjust = []
g_scr_rate = SCREEN_RATE
g_scr_width = 0
g_scr_height = 0
track = Track_Loader(TRACK)

def parse_args():
    params = argparse.ArgumentParser(description=TITLE)
    params.add_argument("-d", "--draw-lines", default=False, action="store_true", help="draw lines")
    params.add_argument("-f", "--full-screen", default=False, action="store_true", help="full screen")
    params.add_argument("-s", "--speed", type=float, default=DEFAULT_SPEED, help="speed")
    params.add_argument("--bots-count", type=int, default=BOTS_COUNT, help="bots count")
    params.add_argument("--bots-speed", type=float, default=BOTS_SPEED, help="bots speed")
    params.add_argument("--debug", default=DEBUG_LOG, action="store_true", help="debug")
    return params.parse_args()

def get_distance(coordinate1, coordinate2):
    '''Get distance between two points'''
    return math.sqrt(
        (coordinate1[0] - coordinate2[0]) *
        (coordinate1[0] - coordinate2[0]) +
        (coordinate1[1] - coordinate2[1]) *
        (coordinate1[1] - coordinate2[1]))

def get_target(pos, angle, dist):
    '''Get target point from position, angle and distance'''
    return [
        dist * math.cos(math.radians(angle)) + pos[0],
        dist * math.sin(math.radians(angle)) + pos[1],
    ]

def degrees(angle):
    '''Get angle in degrees'''
    if angle > 180:
        angle -= 360
    if angle < -180:
        angle += 360
    return angle

def get_radians(coordinate1, coordinate2):
    '''Get angle between two coordinates in radians'''
    return math.atan2((coordinate2[1] - coordinate1[1]), (coordinate2[0] - coordinate1[0]))

def get_degrees(coordinate1, coordinate2):
    '''Get angle between two coordinates in degrees'''
    return degrees(math.degrees(get_radians(coordinate1, coordinate2)))

def get_diff_radians(angle1, angle2):
    '''Get difference between two angles in radians'''
    diff = (angle1 - angle2) % (2.0 * math.pi)
    if diff >= math.pi:
        diff -= 2.0 * math.pi
    return diff

def get_diff_degrees(angle1, angle2):
    '''Get difference between two angles in degrees'''
    return degrees(math.degrees(get_diff_radians(angle1, angle2)))

def get_distance_list(pos, waypoints):
    '''Get distance between position and each waypoint'''
    dist_list = []
    min_dist = float("inf")
    min_idx = -1

    for i, p in enumerate(waypoints):
        dist = get_distance(pos, p)
        if dist < min_dist:
            min_dist = dist
            min_idx = i
        dist_list.append(dist)

    return dist_list, min_dist, min_idx, len(waypoints)

def get_angle_list(pos, waypoints):
    '''Get angle between position and each waypoint'''
    angle_list = []
    dist_list = []

    for _, waypoint in enumerate(waypoints):
        angle = get_degrees(pos, waypoint)
        angle_list.append(angle)

        dist = get_distance(pos, waypoint)
        dist_list.append(dist)

    return angle_list, dist_list, len(waypoints)

def draw_line(surface, color, start_pos, end_pos, width):
    '''Draw line on surface'''
    try:
        pygame.draw.line(surface, color, get_adjust_point(start_pos), get_adjust_point(end_pos), width)
    except Exception as ex:
        print("Error:", ex, start_pos, end_pos, width)

def draw_lines(surface, color, closed, lines, width, dashed):
    '''Draw lines on surface'''
    try:
        if dashed:
            for i in range(0, len(lines) - 1):
                if i % 2 == 0:
                    draw_line(surface, color, lines[i - 1], lines[i], width)
        else:
            pygame.draw.lines(surface, color, closed, get_adjust_points(lines), width)
    except Exception as ex:
        print("Error:", ex, color)

def draw_polygon(surface, color, lines):
    '''Draw polygon on surface'''
    try:
        pygame.draw.polygon(surface, color, get_adjust_points(lines))
    except Exception as ex:
        print("Error:", ex, color)

def draw_circle(surface, color, center, radius, width):
    '''Draw circle on surface'''
    try:
        pygame.draw.circle(surface, color, get_adjust_point(center), get_adjust_length(radius), width)
    except Exception as ex:
        print("Error:", ex, center, radius, width)

def intersection(x1, y1, x2, y2, x3, y3, x4, y4):
    '''Calculate the intersection point between two line segments: Based on the algorithm from https://en.wikipedia.org/wiki/Line%E2%80%93line_intersection'''
    det = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)

    if det == 0:
        return None

    t = ((x1 - x3) * (y3 - y4) - (y1 - y3) * (x3 - x4)) / det
    u = -((x1 - x2) * (y1 - y3) - (y1 - y2) * (x1 - x3)) / det

    if 0 <= t <= 1 and 0 <= u <= 1:
        x = x1 + t * (x2 - x1)
        y = y1 + t * (y2 - y1)
        return (x, y)

    return None

def get_collision(pos, angles, walls, dist):
    left_angle = get_degrees(pos, walls[0])
    right_angle = get_degrees(pos, walls[-1])

    collisions = []
    for angle in angles:
        target = get_target(pos, angle, dist)

        diff_left = degrees(angle - left_angle)
        diff_right = degrees(angle - right_angle)
        if diff_left >= 0 or diff_right <= 0:
            print("Angle out of range", diff_left, left_angle, angle, right_angle, diff_right)
            continue

        intersections = []
        for i in range(0, len(walls) - 1):
            point = intersection(pos[0], pos[1], target[0], target[1], walls[i][0], walls[i][1], walls[i + 1][0], walls[i + 1][1])
            if point is not None:
                intersections.append(point)

        if len(intersections) > 0:
            collisions.append(min(intersections, key=lambda x: get_distance(pos, x)))

    return max(collisions, key=lambda x: get_distance(pos, x)) if len(collisions) > 0 else None

def find_destination(pos, heading, inside, outside, closest_idx, track_width):
    start_idx = (closest_idx + 1) % len(inside)
    length_cut = len(inside) // 5
    sight_dist = track_width * 20

    inside_cut = inside[start_idx : start_idx + length_cut]
    if len(inside_cut) < length_cut:
        inside_cut += inside[: length_cut - len(inside_cut)]
    outside_cut = outside[start_idx : start_idx + length_cut]
    if len(outside_cut) < length_cut:
        outside_cut += outside[: length_cut - len(outside_cut)]

    walls = inside_cut + outside_cut[::-1]

    angles = [degrees(heading + angle) for angle in range(-60, 60)]
    dest = get_collision(pos, angles, walls, sight_dist)

    if dest is not None:
        angle = get_degrees(pos, dest)
        angles = [degrees(angle / 10) for angle in range(int((angle - 2) * 10), int((angle + 2) * 10))]
        dest = get_collision(pos, angles, walls, sight_dist)

    return dest

def init_bot(args):
    '''Initialize bot'''
    bots = []

    if args.bots_count < 1:
        return bots

    lanes = [
        get_waypoints("left"),
        get_waypoints("right"),
    ]

    for i in range(0, args.bots_count):
        index = i % len(lanes)
        waypoints = lanes[index]

        start_index = int(len(waypoints) / (args.bots_count + 2)) * (i + 2)
        target_index = (start_index + 3) % len(waypoints)

        car_angle = get_degrees(waypoints[start_index], waypoints[target_index])

        car = Car(args, waypoints[start_index], car_angle, args.bots_speed, True)
        bot = Bot(car, waypoints, i % 2 == 0)
        bots.append(bot)

    return bots

class Bot:
    '''Represents a bot'''
    def __init__(self, car, waypoints, is_left):
        self.car = car
        self.waypoints = waypoints
        self.is_left = is_left

    def get_pos(self):
        return self.car.get_pos()

    def get_angle(self):
        return self.car.get_angle()

    def left_of_center(self):
        if self.is_left:
            return 1
        else:
            return 0

    def move(self, surface, paused=False):
        pos = self.car.get_pos()

        _, _, min_idx, _ = get_distance_list(pos, self.waypoints)

        index = (min_idx + 3) % len(self.waypoints)

        angle = math.radians(self.car.get_angle())
        target_angle = get_radians(pos, self.waypoints[index])
        diff_angle = get_diff_degrees(angle, target_angle)

        if abs(diff_angle) > 15:
            if diff_angle > 0:
                angle = -15
            else:
                angle = 15
        else:
            angle = 0

        self.car.move(surface, angle, paused, False, False)


class Car:
    '''Represents a car'''
    def __init__(self, args, pos, angle, speed, is_bot):
        # global g_scr_rate

        self.args = args

        self.images = {
            "bot": pygame.image.load(CAR_BOT).convert_alpha(),
            "controlled": pygame.image.load(CAR_CONTROLLED).convert_alpha(),
            "crashed": pygame.image.load(CAR_CRASHED).convert_alpha(),
            "offtrack": pygame.image.load(CAR_OFFTRACK).convert_alpha(),
            "origin": pygame.image.load(CAR_ORIGIN).convert_alpha(),
            "warned": pygame.image.load(CAR_WARNED).convert_alpha(),
        }

        self.image = self.images["origin"]

        self.vel = Vector2((speed / FRAME_RATE), 0)

        self.pos = Vector2(pos)
        self.rect = self.image.get_rect(center=pos)

        self.angle = angle * -1
        self.vel.rotate_ip(angle)

        self.is_bot = is_bot

    def get_pos(self):
        return self.pos

    def get_angle(self):
        return self.angle * -1

    def move(self, surface, angle, paused=False, offtrack=False, crashed=False, warned=False):
        # global g_scr_width
        # global g_scr_height

        angle *= -1

        self.key_pressed = False

        if not paused:
            # pos
            if self.is_bot:
                self.pos += self.vel
            else:
                self.pos += self.vel

        self.rect.center = get_adjust_point(self.pos)

        if not paused:
            # angle
            if self.is_bot:
                if abs(angle) > 0:
                    self.angle += angle
                    self.vel.rotate_ip(-angle)
            else:
                if abs(angle) > 0:
                    self.angle += angle
                    self.vel.rotate_ip(-angle)

        if self.angle > 180:
            self.angle = self.angle - 360
        elif self.angle < -180:
            self.angle = self.angle + 360

        # car
        if self.is_bot:
            image = self.images["bot"]
        elif offtrack:
            image = self.images["offtrack"]
        elif crashed:
            image = self.images["crashed"]
        elif warned:
            image = self.images["warned"]
        elif self.key_pressed:
            image = self.images["controlled"]
        else:
            image = self.images["origin"]

        self.image = pygame.transform.rotate(image, -self.angle)

        scale_width = int(self.image.get_width() * (g_scr_rate / 100))
        scale_height = int(self.image.get_height() * (g_scr_rate / 100))
        self.image = pygame.transform.scale(self.image, (scale_width, scale_height))

        self.rect = self.image.get_rect(center=self.rect.center)
        pygame.mask.from_surface(self.image)

        # draw car
        surface.blit(self.image, self.rect)

        return self.pos, (self.angle * -1)

def calculate_reward(params, speed, steering_angle):
    '''Calculate reward for a given speed and steering angle'''
    params_copy = copy.deepcopy(params) # Deep copy the params dict
    params_copy["steering_angle"] = steering_angle
    params_copy["speed"] = speed
    reward = deepracer.reward_function(params_copy)
    return {"reward": reward, "angle": steering_angle, "speed": speed}

def find_max_reward(futures):
    '''Find the max reward from a list of futures'''
    max_reward = {"reward": float("-inf")}
    for future in concurrent.futures.as_completed(futures):
        reward = future.result()
        if reward["reward"] > max_reward["reward"]:
            max_reward = reward
    return max_reward

def run():
    '''Main run function for pygame'''
    global g_scr_adjust
    global g_scr_rate
    global g_scr_width
    global g_scr_height

    args = parse_args()

    prev_time = float("inf")
    record = float("inf")
    total_reward = float(0)

    steps = 0
    prev_progress = 100

    start_time = time.time()

    tails = []

    # pygame
    pygame.init()

    clock = pygame.time.Clock()

    # title
    pygame.display.set_caption(TITLE)

    # screen
    if args.full_screen:
        surface = pygame.display.set_mode((0, 0), pygame.FULLSCREEN, 32)

        width, height = pygame.display.Info().current_w, pygame.display.Info().current_h

        print("screen", width, height)

        g_scr_width = width
        g_scr_height = height
    else:
        _, _, width, height = get_adjust()

        print("screen", width, height)

        g_scr_width = width
        g_scr_height = height

        surface = pygame.display.set_mode((g_scr_width, g_scr_height))

    # track
    waypoints = get_waypoints("center")

    inside = get_waypoints("inside")
    outside = get_waypoints("outside")

    shortcut = get_waypoints("shortcut")

    track_width = get_distance(inside[0], outside[0])

    print("track", len(waypoints), track_width)

    # laptime
    font = pygame.font.Font(FONT_FACE, FONT_SIZE)

    lap_time = font.render("", True, COLOR_TEXT, COLOR_FLOOR)
    lap_time_rect = lap_time.get_rect(center=(20, 30))

    latest = font.render("", True, COLOR_TEXT, COLOR_FLOOR)
    latest_rect = lap_time.get_rect(center=(20, 60))

    # speed
    speed_display = font.render("", True, COLOR_TEXT, COLOR_FLOOR)
    speed_display_rect = speed_display.get_rect(center=(200, 30))

    # reward
    reward_display = font.render("", True, COLOR_TEXT, COLOR_FLOOR)
    reward_display_rect = reward_display.get_rect(center=(200, 60))

    # total_reward
    total_reward_display = font.render("", True, COLOR_TEXT, COLOR_FLOOR)
    total_reward_display_rect = total_reward_display.get_rect(center=(200, 90))

    # car angle
    car_angle = get_degrees(waypoints[0], waypoints[1])

    # init car
    car = Car(args, waypoints[0], car_angle, args.speed, False)

    # init bots
    bots = init_bot(args)

    run_game = True
    paused = False
    while run_game:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run_game = False
                break

        keys = pygame.key.get_pressed()
        if keys[pygame.K_ESCAPE] or keys[pygame.K_q]:
            run_game = False
        if keys[pygame.K_SPACE] or keys[pygame.K_p]:
            paused = paused == False

        if run_game == False:
            break

        # fill bg
        surface.fill(COLOR_FLOOR)

        # draw track
        draw_polygon(surface, COLOR_ROAD, outside)
        draw_polygon(surface, COLOR_FLOOR, inside)

        # draw lines
        draw_lines(surface, COLOR_TRACK, False, inside, 5, False)
        draw_lines(surface, COLOR_TRACK, False, outside, 5, False)

        draw_lines(surface, COLOR_CENTER, False, waypoints, 5, True)

        if len(shortcut) > 0:
            draw_lines(surface, COLOR_SHORTCUT, False, shortcut, 2, True)

        # car
        pos = car.get_pos()
        heading = car.get_angle()

        # closest
        _, closest_dist, closest_idx, waypoints_length = get_distance_list(pos, waypoints)

        closest_waypoints = [closest_idx, (closest_idx + 1) % waypoints_length]

        # progress
        progress = (closest_idx / waypoints_length) * 100
        if steps > 0 and prev_progress > progress:
            steps = 0
            start_time = time.time()
        steps += 1
        prev_progress = progress

        if args.debug:
            print("")
            print("run", steps, progress)

        # Off track
        if closest_dist > (track_width * 0.55):
            offtrack = True
            paused = True
        else:
            offtrack = False

        dist_inside = get_distance(pos, inside[closest_idx])
        dist_outside = get_distance(pos, outside[closest_idx])

        # is_left
        if dist_inside < dist_outside:
            is_left_of_center = True
        else:
            is_left_of_center = False

        # objects
        closest_objects = []
        objects_location = []
        objects_distance = []
        objects_left_of_center = []

        crashed = False
        warned = False

        # draw_bots
        if len(bots) > 0:
            for _, bot in enumerate(bots):
                bot.move(surface, paused)

                obj_pos = bot.get_pos()

                objects_location.append([obj_pos[0], obj_pos[1]])
                objects_distance.append(get_distance(pos, obj_pos))
                objects_left_of_center.append(bot.left_of_center())

            bot_dist = min(objects_distance)
            bot_idx = objects_distance.index(bot_dist)
            closest_objects = objects_location[bot_idx]

            if bot_dist < (track_width * 1.5):
                warned = True

        # tails
        tails.append([pos[0], pos[1]])
        if len(tails) > TAIL_LENGTH:
            del tails[0]
        if len(tails) > 1:
            draw_lines(surface, COLOR_SHORTCUT, False, tails, 2, False)

        # dummy
        params = {
            "all_wheels_on_track": not offtrack, # TODO: This isn't true
            "closest_objects": closest_objects,
            "closest_waypoints": closest_waypoints,
            "is_crashed": crashed,
            "distance_from_center": closest_dist,
            "heading": heading,
            "is_left_of_center": is_left_of_center,
            "is_reversed": False,
            "objects_distance": objects_distance,
            "objects_left_of_center": objects_left_of_center,
            "objects_location": objects_location,
            "is_offtrack": offtrack,
            "progress": progress,
            "speed": args.speed,
            "steering_angle": 0,
            "steps": steps,
            "track_width": track_width,
            "waypoints": waypoints,
            "x": pos[0],
            "y": pos[1],
        }

        # pick target
        rewards = []
        target = []
        angle = 0

        if not paused:
            with concurrent.futures.ThreadPoolExecutor() as executor:
                rewards = []

                # Submit tasks to the thread pool
                tasks = []
                for speed in SPEEDS:
                    for steering_angle in STEERING_ANGLE:
                        task = executor.submit(calculate_reward, params, speed, steering_angle)
                        tasks.append(task)

                max_reward = find_max_reward(tasks)

        angle = max_reward["angle"]
        speed = max_reward["speed"]

        print("Chosen Speed:", speed, " Chosen Angle:", angle, " Reward:", max_reward["reward"])

        if not paused and args.debug:
            print("pick {} {}".format(max_reward, rewards))

        # moving
        pos, heading = car.move(surface, angle, paused, offtrack, crashed, warned)

        if not paused:
            # time
            race_time = time.time() - start_time

            # laptime
            s = "{:3.3f}".format(race_time)
            lap_time = font.render(s, True, COLOR_TEXT, COLOR_FLOOR)

            # speed
            speed_display = font.render("Speed: " + str(speed), True, COLOR_TEXT, COLOR_FLOOR)

            # reward
            total_reward += max_reward["reward"]
            reward_display = font.render("Reward: " + "{:3f}".format(max_reward["reward"]), True, COLOR_TEXT, COLOR_FLOOR)
            total_reward_display = font.render("Total Reward: " + "{:3f}".format(total_reward), True, COLOR_TEXT, COLOR_FLOOR)

        if progress == 0 and prev_time > 5:
            record = prev_time
        prev_time = race_time

        # latest
        if record < 120 and record > 5:
            s = "{:3.3f}".format(record)
            latest = font.render(s, True, COLOR_TEXT, COLOR_FLOOR)

        surface.blit(lap_time, lap_time_rect)
        surface.blit(speed_display, speed_display_rect)
        surface.blit(reward_display, reward_display_rect)
        surface.blit(total_reward_display, total_reward_display_rect)
        surface.blit(latest, latest_rect)

        # draw lines
        if args.draw_lines:
            draw_circle(surface, COLOR_CIRCLE, pos, track_width, 1)

            if warned:
                draw_line(surface, COLOR_OBJECT, pos, closest_objects, 2)

            target = get_target(pos, heading, track_width * 2)
            if target:
                draw_line(surface, COLOR_RAY, pos, target, 2)

            destination = find_destination(pos, heading, inside, outside, closest_idx, track_width)
            if destination:
                draw_line(surface, COLOR_RAY, pos, destination, 1)

        # pygame.display.flip()
        pygame.display.update()
        clock.tick(FRAME_RATE)

    pygame.quit()

def get_adjust():
    global g_scr_adjust
    global g_scr_rate
    global g_scr_width
    global g_scr_height

    if len(g_scr_adjust) > 0:
        return g_scr_adjust, g_scr_rate, g_scr_width, g_scr_height

    min_x = float("inf")
    min_y = float("inf")
    max_x = float("-inf")
    max_y = float("-inf")

    lines = track.get_outside_waypoints()

    for point in lines:
        min_x = min(min_x, point[0])
        min_y = min(min_y, point[1])

        max_x = max(max_x, point[0])
        max_y = max(max_y, point[1])

    print("min", min_x, min_y)
    print("max", max_x, max_y)

    if g_scr_width == 0 or g_scr_height == 0:
        g_scr_width = int(((max_x - min_x) + ((max_x - min_x) * 0.05)) * g_scr_rate)
        g_scr_height = int(((max_y - min_y) + ((max_y - min_y) * 0.05)) * g_scr_rate)

    x = ((g_scr_width / g_scr_rate) * 0.5) - ((max_x + min_x) * 0.5)
    y = ((g_scr_height / g_scr_rate) * 0.5) - ((max_y + min_y) * 0.5)

    g_scr_adjust = [x, y]

    print("adjust", g_scr_adjust)

    return g_scr_adjust, g_scr_rate, g_scr_width, g_scr_height

def get_waypoints(key):
    '''Get list of waypoints for the given key'''
    if key == "center":
        return track.get_center_waypoints()
    elif key == "inside":
        return track.get_inside_waypoints()
    elif key == "outside":
        return track.get_outside_waypoints()
    elif key == "shortcut":
        return track.get_shortcut_waypoints()
    elif key == "left":
        return get_merge_waypoints(
            track.get_center_waypoints(),
            track.get_inside_waypoints(),
        )
    elif key == "left2":
        return get_border_waypoints(track.get_center_waypoints(), track.get_inside_waypoints(), 0.9)
    elif key == "right":
        return get_merge_waypoints(
            track.get_center_waypoints(),
            track.get_outside_waypoints(),
        )
    elif key == "right2":
        return get_border_waypoints(track.get_center_waypoints(), track.get_outside_waypoints(), 0.9)
    return None

def get_adjust_length(val):
    _, rate, _, _ = get_adjust()
    return int(val * rate)

def get_adjust_point(point):
    adjust, rate, _, height = get_adjust()

    if rate == 1:
        return point

    x = (point[0] + adjust[0]) * rate
    y = height - ((point[1] + adjust[1]) * rate)
    return [int(x), int(y)]

def get_adjust_points(points):
    results = []
    for point in points:
        results.append(get_adjust_point(point))
    return results

def get_merge_waypoints(points1, points2, rate=0.5):
    length = min(len(points1), len(points2))
    results = []
    for i in range(0, length):
        results.append(
            [
                (points1[i][0] + points2[i][0]) * rate,
                (points1[i][1] + points2[i][1]) * rate,
            ]
        )
    return results

def get_border_waypoints(points1, points2, rate=1.2):
    length = min(len(points1), len(points2))
    results = []
    for i in range(0, length):
        dist = get_distance(points1[i], points2[i]) * rate
        angle = get_radians(points1[i], points2[i])
        results.append(
            [
                dist * math.cos(angle) + points1[i][0],
                dist * math.sin(angle) + points1[i][1],
            ]
        )
    return results

if __name__ == "__main__":
    run()
