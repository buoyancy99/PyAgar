import numpy as np

class Cell:
    def __init__(self, gameServer, owner, position, size):
        self.gameServer = gameServer
        self.owner = owner #playerTracker that owns this cell

        self.color = np.array([0,0,0])
        self.radius = 0
        self.size = 0
        self.mass = 0
        self.cellType = -1 #0 = Player Cell, 1 = Food, 2 = Virus, 3 = Ejected Mass
        self.isSpiked = False #If true, then this cell has spikes around it
        self.isAgitated = False #If true, then this cell has waves on it's outline
        self.killedBy = None
        self.isMoving = False
        self.boostDistance = 0
        self.boostDirection = np.array([1, 0])

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

        self.setSize(np.sqrt(self.radius + prey.radius))

    def setBoot(self, distance, angle):
        self.boostDistance = distance
        self.boostDirection = np.array(np.sin(angle), np.cos(angle))
        self.isMoving = True
        if not self.owner:
            idx = self.gameServer.movingNodes.index(self)
            if idx < 0:
                self.gameServer.movingNodes.append(self)

    def checkBorder(self, border):
        r = self.size / 2
        if self.position[0] < border.minx + r or self.position[0] > border.maxx - r:
            self.boostDirection[0] = -self.boostDirection[0]
            self.position[0] = np.maximum(self.position[0], border.minx + r)
            self.position[0] = np.minimum(self.position[0], border.minx - r)

        if self.position[1] < border.miny + r or self.position[1] > border.maxy - r:
            self.boostDirection[1] = -self.boostDirection[1]
            self.position[1] = np.maximum(self.position[1], border.miny + r)
            self.position[1] = np.minimum(self.position[1], border.miny - r)

    def onEaten(self):
        return

    def onAdd(self):
        return

    def onRemove(self):
        return


