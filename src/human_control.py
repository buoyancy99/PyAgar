from GameServer import GameServer
from players import Player
import cv2
import numpy as np
from agar import AgarEnv
# server = GameServer()
# server.start(0)
# players = [Player(server) for i in range(60)]
# server.addPlayers(players)
#
# action = np.array([1,1,1,0,1])
# for i in range(1000):
#     for player in players:
#         player.step(action)
#     server.Update()
render = True
env = AgarEnv()
env.seed(0)
# action = np.random.random(size=(20, 5))
num_players = 60
action = np.ones((num_players, 5))/2

def update_mouse(event,x,y,flags,param):
    # if event == cv2.EVENT_LBUTTONDOWN:
    action[0][0] = x / 512 - 0.5
    action[0][1] = -(y / 512 - 0.5)

touchpad = np.zeros((512,512,3), np.uint8)
cv2.namedWindow('touchpad')
cv2.setMouseCallback('touchpad',update_mouse)

step = 0
for episode in range(1):
    env.reset(1)

    while True:
        if render:
            cv2.imshow('touchpad', touchpad)
            k = cv2.waitKey(40) & 0xFF
            if k == ord('w'):
                action[0][2:] = np.array([0,1,0])
            elif k == 32:
                action[0][2:] = np.array([1,0,0])
            else:
                action[0][2:] = np.array([0, 0, 1])
            env.render(0)
        env.step(action)
        print('step', step)
        step+=1
env.close()
cv2.destroyAllWindows()