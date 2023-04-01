import os
import numpy as np

class Track_Loader:
  def __init__(self, route):
    self.route = route

    loaded_route = np.load("./routes/" + route + ".npy")

    loaded_route = np.flip(loaded_route, 0)

    self.center_waypoints = [[r[0], r[1]] for r in loaded_route]
    self.inside_waypoints = [[r[2], r[3]] for r in loaded_route]
    self.outside_waypoints = [[r[4], r[5]] for r in loaded_route]

    racing_line_path = "./racinglines/" + route + ".npy"
    self.racing_line = []

    if (os.path.isfile(racing_line_path)):
        self.racing_line = np.load(racing_line_path)

  def get_center_waypoints(self):
      return self.center_waypoints

  def get_inside_waypoints(self):
      return self.inside_waypoints

  def get_outside_waypoints(self):
      return self.outside_waypoints

  def get_shortcut_waypoints(self):
      return self.racing_line