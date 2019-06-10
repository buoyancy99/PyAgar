from .Food import Food
from .Cell import Cell
import numpy as np
import math
import random

class MotherCell(Cell):
    def __init__(self, gameServer, owner, position, size):
        Cell.__init__(self, gameServer, owner, position, size)
        self.cellType = 2
        self.isSpiked = True
        self.isMotherCell = True
        self.color = np.array([206, 99, 99])
        self.motherCellMinSize = 149
        self.motherCellSpawnAmount = 2
        if not self.size:
            self.setSize(self.motherCellMinSize)

    def canEat(self, cell):
        maxMass = self.gameServer.config.motherCellMaxMass
        if maxMass and self.mass >= maxMass:
            return False
        return cell.cellType in [0, 2, 3]

    def onUpdate(self):
        maxFood = self.gameServer.config.foodMaxAmount
        if len(self.gameServer.nodeFood) >= maxFood:
            return
        size1 = self.size
        size2 = self.gameServer.config.foodMinSize
        for i in range(self.motherCellSpawnAmount):
            size1 = math.sqrt(size1**2 - size2 **2)
            size1 = math.max(size1, self.motherCellMinSize)
            self.setSize(size1)

            angle = random.random() * 2 * math.pi
            pos = self.position + size1 * np.array(math.sin(angle), math.cos(angle))

            food = Food(self.gameServer, None, pos, size2)
            food.color = self.gameServer.getRandomColor()
            self.gameServer.addNode(food)

            food.setBoost(32 + 42*random.random(), angle)
            if len(self.gameServer.nodeFood) >= maxFood or size1 <= self.motherCellMinSize:
                break
        self.gameServer.updateNodeQuad(self)

    def onAdd(self):
        return

    def onRemove(self):
        return


