from .GameAbstractions import *

def disjoint(a, b):
    return b.minx >= a.maxx or b.maxx <= a.minx or b.miny >= a.maxy or b.maxy <= a.miny

class QuadNode:
    def __init__(self, bound):
        self.halfWidth = (bound.maxx - bound.minx) // 2
        self.halfHeight = (bound.maxy - bound.miny) // 2

        self.bound = bound
        self.bound.cx = bound.minx + self.halfWidth
        self.bound.cy = bound.miny + self.halfHeight
        self.childNodes = []
        self.items = []


    def insert(self, item):
        if len(self.childNodes) != 0:
            quad = self.getQuad(item.bound)
            if quad is not -1:
                return self.childNodes[quad].insert(item)

        self.items.append(item)
        item.quadNode = self;  # used for quick search quad node by item

        # split and rebalance current node
        if not self.childNodes and len(self.items) > 64:
            # split into 4 subnodes (top, left, bottom, right)
            w = self.halfWidth
            h = self.halfHeight
            my = self.bound.miny
            mx = self.bound.minx
            mh = my + h
            mw = mx + w
            b0 = Bound(mw, my, mw + w, my + h)
            b1 = Bound(mx, my, mx + w, my + h)
            b2 = Bound(mx, mh, mx + w, mh + h)
            b3 = Bound(mw, mh, mw + w, mh + h)
            self.childNodes.append(QuadNode(b0))
            self.childNodes.append(QuadNode(b1))
            self.childNodes.append(QuadNode(b2))
            self.childNodes.append(QuadNode(b3))



    def remove(self, item):
        if item.quadNode is not self:
            return item.quadNode.remove(item)
        self.items.remove(item)
        item.quadNode = None

    def find(self, bound, callback):
        if len(self.childNodes) != 0:
            quad = self.getQuad(bound)
            if quad != -1:
                self.childNodes[quad].find(bound, callback)
            else:
                for node in self.childNodes:
                    if not disjoint(node.bound, bound):
                        node.find(bound, callback)

        for item in self.items:
            if not disjoint(item.bound, bound):
                return callback(item.cell)

    # Returns quadrant for the bound.
    # Returns -1 if bound cannot completely fit within a child node
    def getQuad(self, bound):
        isTop = (bound.miny and bound.maxy) < self.bound.cy
        if (bound.minx and bound.maxx) < self.bound.cx:
            if isTop:
                return 1
            elif bound.miny > self.bound.cy:
                return 2 # isBottom
        elif bound.minx > self.bound.cx: # isRight
            if isTop:
                return 0
            elif bound.miny > self.bound.cy:
                return 3 # isBottom
        return -1 # cannot fit (too large size)


