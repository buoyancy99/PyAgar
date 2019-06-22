from pyglet.window import key
import numpy as np
from Env import AgarEnv

render = True
num_agents = 1
num_bots = 29
gamemode = 0
env = AgarEnv(num_agents, num_bots, gamemode)
env.seed(0)

step = 1
window = None
action = np.zeros((num_agents, 4))

def on_mouse_motion(x, y, dx, dy):
    action[0][0] = (x / 1920 - 0.5) * 2
    action[0][1] = (y / 1080 - 0.5) * 2

def on_key_press(k, modifiers):
    if k == key.W:
        action[0][2:] = np.array([0, 1])
    elif k == key.SPACE:
        action[0][2:] = np.array([1, 0])

for episode in range(1):
    observation = env.reset()
    while True:
        if step % 200 == 0:
            print('step', step)
        if render:
            env.render(0)
            if not window:
                window = env.viewer.window
                window.on_key_press = on_key_press
                window.on_mouse_motion = on_mouse_motion
        observations, rewards, done = env.step(action)
        action[0][2:] = np.array([0, 0])
        step+=1
env.close()

