from GameServer import GameServer
from players import Player
import numpy as np

server = GameServer()
server.start()
players = [Player(server) for i in range(30)]
server.addPlayers(players)

for i in range(2):
    server.Update()
    for player in players:
        player.step(np.ones(5))