from .Cell import Cell
class Food(Cell):
    def __init__(self, gameServer, owner, position, size):
        Cell.__init__(self, gameServer, owner, position, size)
        self.cellType = 1

    def onAdd(self, gameServer):
        gameServer.nodesEjected.append(self)


    def onRemove(self, gameServer):
        idx = gameServer.nodesEjected.index(self)
        if idx != -1:
            gameServer.nodesEjected.pop(idx)