import math
from ..abstraction import *
from ..modules import *

class Cell:
    def __init__(self, gameServer, owner, position, size):
        self.gameServer = gameServer
        self.owner = owner #playerTracker that owns this cell

        self.color = Color(0,0,0)
        self.radius = 0
        self.size = 0
        self.mass = 0
        self.cellType = -1 #0 = Player Cell, 1 = Food, 2 = Virus, 3 = Ejected Mass
        self.isSpiked = False #If true, then this cell has spikes around it
        self.isAgitated = False #If true, then this cell has waves on it's outline
        self.killedBy = None
        self.isMoving = False
        self.boostDistance = 0
        self.boostDirection = Vec2(1, 0)

        if self.gameServer:
            self.tickOfBirth = self.gameServer.tickCounter
            self.nodeId = self.gameServer.lastNodeId
            self.gameServer.lastNodeId += 1
            self.setSize(size)
            self.position = position

    def setSize(self, size):
        self.size = size
        self.radius = size * size
        self.mass = self.radius / 100

    def canEat(self, cell):
        return False

    def getAge(self, cell):
        return self.gameServer.tickCounter - self.tickOfBirth

    def onEat(self, prey):
        if not self.gameServer.config.playerBotGrow:
            if self.size >= 250 and prey.size<=41 and prey.cellType == 0:
                prey.radius = 0

        self.setSize(math.sqrt(self.radius + prey.radius))

    def setBoost(self, distance, angle):
        self.boostDistance = distance
        self.boostDirection = Vec2(math.sin(angle), math.cos(angle))
        self.isMoving = True
        if not self.owner:
            idx = self.gameServer.movingNodes.index(self)
            if idx < 0:
                self.gameServer.movingNodes.append(self)

    def checkBorder(self, border):
        r = self.size / 2
        if self.position.x < border.minx + r or self.position.x > border.maxx - r:
            self.boostDirection.scale(-1, 1);
            self.position.x = math.max(self.position.x, border.minx + r);
            self.position.x = math.min(self.position.x, border.maxx - r);

        if self.position.y < border.miny + r or self.position.y > border.maxy - r:
            self.boostDirection.scale(1, -1);
            self.position.y = math.max(self.position.y, border.miny + r);
            self.position.y = math.min(self.position.y, border.maxy - r);


    def onEaten(self):
        return

    def onAdd(self):
        return

    def onRemove(self):
        return


