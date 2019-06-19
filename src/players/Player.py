from modules import *
from entity import *
from gamemodes import *
import math
import numpy as np

class Player:
    def __init__(self, gameServer):
        self.gameServer = gameServer
        self.name = None
        self.mouse = None
        self.cells = []
        self.frozen = False
        self.mergeOverride = False
        self.spectate = False
        self.score = 0
        self.isRemoved = False

    def step(self, action):
        if self.isRemoved:
            return
        # action in format [0] mouse x, [1] mouse y, [2] key space bool, [3] key w bool, [4] no key bool
        self.update_view()
        self.mouse = Vec2(action[0], action[1])
        assert np.sum(action[2:]) == 1
        if action[2] == 1:
            self.pressSpace()
        elif action[3] == 1:
            self.pressW()

    def update_view(self):
        # TODO
        self.setCenterPos()

    #
    def pressSpace(self):
        if self.gameServer.run:
            if len(self.cells) <= 2:
                self.mergeOverride = False
            if self.mergeOverride or self.frozen:
                return
        self.gameServer.splitCells(self)

    def pressW(self):
        if self.spectate or not self.gameServer.run:
            return
        self.gameServer.ejectMass(self)

    def setCenterPos(self, p):
        p.x = max(p.x, self.gameServer.border.minx)
        p.y = max(p.y, self.gameServer.border.miny)
        p.x = min(p.x, self.gameServer.border.maxx)
        p.y = min(p.y, self.gameServer.border.maxy)
        self.centerPos = p

    def getScale(self):
        scale = 0
        for cell in self.cells:
            scale += cell.size
            self.score += cell.mass
        if scale == 0:
            self.scale = 0.4
        else:
            self.scale = math.pow(min(64 / scale, 1), 0.4)
        return self.scale



