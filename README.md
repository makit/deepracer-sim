# AWS DeepRacer Reward Function Simulator

Simulates the AWS DeepRacer vehicle driving a track by using a provided Reward Function.

On each step the Reward Function is ran for a series of Steering Angles and Speeds, and the one with the highest reward is chosen.

This does not simulate how the actual DeepRacer learns, which picks Steering Angles and Speeds at random and then when the vehicle eventually crashes it looks at the whole "episode" to learn.

This means that the simulator is a good way to check that the Reward Function is returning rewards that are expected, but when actually training the results will be different.

## Installation
### Mac/Linux
```bash
brew install pyenv
pyenv install 3.8.6

pyenv shell 3.8.6

pip3 install numpy
pip3 install pygame
```

### Windows
```bash
py -m pip install -U pygame --user
```

## Running

```bash
python sim.py

### Drawing Lines and Specific Speed
python sim.py -d -s 1

### With Bots
python sim.py -d -s 1 --bots-count 6 --bots-speed 1.0
```

## Demo
[DeepRacer Simulator Demo Video](https://youtu.be/9jSZm7FcqmE?t=0s)

## Trouble Shooting

```
python3 sim.py -h

pygame 2.0.0.dev10 (SDL 2.0.12, python 3.7.6)
Hello from the pygame community. https://www.pygame.org/contribute.html
usage: sim.py [-h] [-a] [-d] [-f] [-s SPEED] [--bots-count BOTS_COUNT]
              [--bots-speed BOTS_SPEED]

DeepRacer Simulator

optional arguments:
  -h, --help            show this help message and exit
  -a, --autonomous      autonomous
  -d, --draw-lines      draw lines
  -f, --full-screen     full screen
  -s SPEED, --speed SPEED
                        speed
  --bots-count BOTS_COUNT
                        bots count
  --bots-speed BOTS_SPEED
                        bots speed
```
