from .Player import Player
import numpy as np
from modules import *
import random

class Bot(Player):
    def __init__(self, gameServer, name='bot'):
        super().__init__(gameServer, name)
        self.tickstamp = None
        self.actionstamp = np.zeros(4)


    def step(self):
        if len(self.cells) == 0:
            self.isRemoved = True
        if self.isRemoved:
            return
        visible_food = []
        action = np.zeros(4)
        has_enemy = False
        for cell in self.viewNodes:
            if cell.cellType == 1 or cell.cellType == 3:
                visible_food.append(cell)
            elif cell.cellType == 0:
                if cell.owner is not self and not self.gameServer.gameMode.haveTeams:
                    has_enemy = True
                elif self.gameServer.gameMode.haveTeams and cell.owner.team != self.team:
                    has_enemy = True
        if not has_enemy:
            action[2] = 1

        if visible_food and self.cells:
            if not self.tickstamp or self.gameServer.tickCounter - self.tickstamp >= 20:
                self.mincell = min(self.cells, key = lambda c : c.radius)
                target = sorted(visible_food, key=lambda c: (abs(c.position.x - self.mincell.position.x) + abs(c.position.y - self.mincell.position.y)) / c.mass)[0]

                # target = sorted(visible_food, key=lambda c: (abs(c.position.x - self.centerPos.x) + abs(c.position.y - self.centerPos.y)) / c.mass)[0]
                relative_position = target.position.clone().sub(self.centerPos)

                action[0] = relative_position.x / max(abs(relative_position.x), abs(relative_position.y))
                action[1] = relative_position.y / max(abs(relative_position.x), abs(relative_position.y))

                self.tickstamp = self.gameServer.tickCounter
                self.actionstamp[:2] = action[:2]
            else:
                action[:2] = self.actionstamp[:2]

        elif self.cells:
            if not self.tickstamp or self.gameServer.tickCounter - self.tickstamp >= 500:
                self.tickstamp = self.gameServer.tickCounter
                action[:2] = np.random.randint(2, size=(2)) * 2 - 1
                self.actionstamp[:2] = action[:2]

            else:
                action[:2] = self.actionstamp[:2]

        self.mouse = self.centerPos.add(Vec2(action[0] * self.gameServer.config.serverViewBaseX, action[1] * self.gameServer.config.serverViewBaseY), 1)
        if action[2] == 1:
            self.pressSpace()
        elif action[3] == 1:
            self.pressW()
