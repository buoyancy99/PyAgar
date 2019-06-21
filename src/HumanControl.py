from GameServer import GameServer
from players import Player
import pyglet
from pyglet.window import mouse, key, event
import numpy as np
from Env import AgarEnv

render = True
num_players = 60
gamemode = 0
env = AgarEnv(num_players, gamemode)
env.seed(0)

action = np.zeros((num_players, 5))

step = 0

def on_mouse_motion(x, y, dx, dy):
    action[0][0] = (x / 1920 - 0.5) * 2
    action[0][1] = (y / 1080 - 0.5) * 2

def on_key_press(k, modifiers):
    if k == key.W:
        action[0][2:] = np.array([0, 1, 0])
    elif k == key.SPACE:
        action[0][2:] = np.array([1, 0, 0])

for episode in range(1):
    env.reset()
    while True:
        action[0][2:] = np.array([0, 0, 1])
        if render:
            env.render(0)
            window = env.viewer.window
            window.on_key_press = on_key_press
            window.on_mouse_motion = on_mouse_motion
        env.step(action)
        # print('step', step)
        step+=1
env.close()

