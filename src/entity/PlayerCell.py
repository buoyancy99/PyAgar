from .Cell import Cell
import math

class PlayerCell(Cell):
    def __init__(self, gameServer, owner, position, radius):
        Cell.__init__(self, gameServer, owner, position, radius)
        self.cellType = 0
        self.canRemerge = False

    def canEat(self, cell):
        return True

    def getSpeed(self, dist):
        if dist == 0:
            return 0
        speed = 2.2 * math.pow(self.radius, -0.439)
        speed *= 40 * self.gameServer.config.playerSpeed
        return min(dist, speed) / dist

    def onAdd(self, gameServer):
        self.color = self.owner.color
        self.owner.cells.append(self)

        #TODO
        #self.owner.socket.packetHandler.sendPacket(new Packet.AddNode(self.owner, self))
        self.gameServer.nodesPlayer.insert(0, self);
        gameServer.gameMode.onCellAdd(self)

    def onRemove(self, gameServer):
        if self in self.owner.cells:
            self.owner.cells.remove(self)

        if self in self.gameServer.nodesPlayer:
            self.gameServer.nodesPlayer.remove(self)

        gameServer.gameMode.onCellRemove(self)