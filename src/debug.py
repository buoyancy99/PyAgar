from GameServer import GameServer
from players import Player
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

env = AgarEnv()
env.seed(0)

for episode in range(1):
    env.reset()
    for s in range(100):
        env.render(0)
        action = np.array([1, 1, 0, 0, 1])
        env.step(action)