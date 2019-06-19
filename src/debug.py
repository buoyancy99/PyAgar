from GameServer import GameServer
from players import Player
import numpy as np

server = GameServer()
server.start(0)
players = [Player(server) for i in range(60)]
server.addPlayers(players)

action = np.array([1,1,1,0,1])
for i in range(10):
    server.Update()
    for player in players:
        player.step(action)