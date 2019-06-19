from .Cell import Cell
import math
import random
from ..abstraction import *
from ..modules import *

class Virus(Cell):
    def __init__(self, gameServer, owner, position, size):
        Cell.__init__(self, gameServer, owner, position, size)
        self.cellType = 2
        self.isSpiked = True
        self.isMotherCell = False
        self.color = Color(51, 255, 51)

    def canEat(self, cell):
        if len(self.gameServer.nodeVirus) < self.gameServer.config.virusMaxAmount:
            return self.cellType == 3

    def onEat(self, prey):
        self.setSize(math.sqrt(self.radius + prey.radius))
        if self.size >= self.gameServer.config.virusMaxSize:
            self.setSize(self.gameServer.config.virusMaxSize)
            self.gameServer.shootVirus(self, prey.boostDirection.angle())

    def onEaten(self, cell):
        if not cell.owner:
            return
        config = self.gameServer.config
        cellsLeft = (config.virusMaxCells or config.playerMaxCells) - cell.owner.cells.length

        if cellsLeft <= 0:
            return
        splitMin = config.virusMaxPoppedSize**2 / 100
        cellMass = cell.mass
        splits = []

        if config.virusEqualPopSize:
            splitCount = math.min(math.floor(cellMass / splitMin), cellsLeft)
            splitMass = cellMass / (1 + splitCount)
            splits = splits + [splitMass for _ in range(splitCount)]
            return self.explodeCell(cell, splits)

        if (cellMass / cellsLeft < splitMin):
            splitCount = 2
            splitMass = cellMass / splitCount
            while splitMass > splitMin and splitCount * 2 < cellsLeft:
                splitCount *= 2
                splitMass = cellMass / splitCount

            splitMass = cellMass / (splitCount + 1)
            splits = splits + [splitMass for _ in range(splitCount)]
            splitCount = 0
            return self.explodeCell(cell, splits)

        splitMass = cellMass / 2
        massLeft  = cellMass / 2
        while cellsLeft > 0:
            cellsLeft -= 1
            if (massLeft / cellsLeft < splitMin):
                splitMass = massLeft / cellsLeft
                splits = splits + [splitMass for _ in range(cellsLeft)]
                cellsLeft = 0

            while splitMass >= massLeft and cellsLeft > 0:
                splitMass /= 2

            splits.append(splitMass)
            massLeft -= splitMass
        self.explodeCell(cell, splits)

    def explodeCell(self, cell, splits):
        for s in splits:
            self.gameServer.splitPlayerCell(cell.owner, cell, 2*math.pi * random.random(), s)

    def onAdd(self, gameServer):
        gameServer.nodesVirus.append(self)


    def onRemove(self, gameServer):
        idx = gameServer.nodesVirus.index(self)
        if idx != -1:
            gameServer.nodesVirus.pop(idx)