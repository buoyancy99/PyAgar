from .Cell import Cell
import math
import numpy as np

class PlayerCell(Cell):
    def __init__(self, gameServer, owner, position, size):
        Cell.__init__(self, gameServer, owner, position, size)
        self.cellType = 0
        self.canRemerge = False

    def canEat(self, cell):
        return True

    def getSpeed(self, dist):
        speed = 2.2 * math.pow(self.size, -0.439)
        speed *= 40 * self.gameServer.config.playerSpeed
        return math.min(dist, speed) / dist

    def onAdd(self, gameServer):
        self.color = self.owner.color
        self.owner.cells.append(self)

        #TODO
        #self.owner.socket.packetHandler.sendPacket(new Packet.AddNode(self.owner, self))

        gameServer.gameMode.onCellAdd(self)

    def onRemove(self, gameServer):
        idx = self.owner.cells.index(self)
        if idx != -1:
            self.owner.cells.pop(idx)

        idx = self.gameServer.nodesPlayer.index(self)
        if idx != -1:
            self.gameServer.nodesPlayer.pop(idx)

        gameServer.gameMode.onCellRemove(self)