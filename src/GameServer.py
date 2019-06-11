import numpy as np
import math
from .Config import Config

class GameServer():
    def __init__(self):

        self.srcFiles = "../src"

        # Startup
        self.run = True
        self.version = '1.6.1'
        self.httpServer = None
        self.lastNodeId = 1
        self.lastPlayerId = 1
        self.clients = []
        self.socketCount = 0
        self.largestClient = None
        self.nodes = [] # Total nodes
        self.nodesVirus = [] # Virus nodes
        self.nodesFood = [] # Food nodes
        self.nodesEjected = [] # Ejected nodes
        self.nodesPlayer = [] # Player nodes

        self.movingNodes = [] # For move engine
        self.leaderboard = [] # For leaderboard
        self.leaderboardType = -1 # No type

        var BotLoader = require('./ai/BotLoader')
        self.bots = new BotLoader(self)

        # Main loop tick
        self.startTime = Date.now()
        self.stepDateTime = 0
        self.timeStamp = 0
        self.updateTime = 0
        self.updateTimeAvg = 0
        self.timerLoopBind = None
        self.mainLoopBind = None
        self.tickCounter = 0
        self.disableSpawn = False

        # Config
        self.config = Config()


        self.ipBanList = []
        self.minionTest = []
        self.userList = []
        self.badWords = []
        self.loadFiles()

        # Set border, quad-tree
        var QuadNode = require('./modules/QuadNode.js')
        self.setBorder(self.config.borderWidth, self.config.borderHeight)
        self.quadTree = QuadNode(self.border)


    def start(self):
        self.timerLoopBind = self.timerLoop.bind(self)
        self.mainLoopBind = self.mainLoop.bind(self)

        # Set up gamemode(s)
        Gamemode = require('./gamemodes')
        self.gameMode = Gamemode.get(self.config.serverGamemode)
        self.gameMode.onServerInit(self)

        # Client Binding
        bind = self.config.clientBind + ""
        self.clientBind = bind.split(' - ')

        # Start the server
        self.httpServer = http.createServer()
        wsOptions = {
            server: self.httpServer,
            perMessageDeflate: False,
            maxPayload: 4096
        }
        Logger.info("WebSocket: " + self.config.serverWsModule)
        self.WebSocket = require(self.config.serverWsModule)
        self.wsServer = self.WebSocket.Server(wsOptions)
        self.wsServer.on('error', self.onServerSocketError.bind(self))
        self.wsServer.on('connection', self.onClientSocketOpen.bind(self))
        self.httpServer.listen(self.config.serverPort, self.config.serverBind, self.onHttpServerOpen.bind(self))

        # Start stats port (if needed)
        if self.config.serverStatsPort > 0:
            self.startStatsServer(self.config.serverStatsPort)

    def onHttpServerOpen(self):
        # Start Main Loop
        setTimeout(self.timerLoopBind, 1)

        # Done
        Logger.info("Listening on port " + self.config.serverPort)
        Logger.info("Current game mode is " + self.gameMode.name)

        # Player bots (Experimental)
        if self.config.serverBots:
            for i in range(self.config.serverBots):
                self.bots.addBot()
            Logger.info("Added " + self.config.serverBots + " player bots")


    def addNode(self, node):
        # Add to quad-tree & node list
        x = node.position[0]
        y = node.position[1]
        s = node.size
        node.quadItem = {
            cell: node, # update viewbox for players
            bound: {
                minx: x - s,
                miny: y - s,
                maxx: x + s,
                maxy: y + s
            }
        }
        self.quadTree.insert(node.quadItem)
        self.nodes.push(node)

        # Special on-add actions
        node.onAdd(self)

    def onServerSocketError(self, error):
        Logger.error("WebSocket: " + error.code + " - " + error.message)
        switch (error.code) {
            case "EADDRINUSE":
                Logger.error("Server could not bind to port " + self.config.serverPort + "!")
                Logger.error("Please close out of Skype or change 'serverPort' in gameserver.ini to a different number.")
                break
            case "EACCES":
                Logger.error("Please make sure you are running MultiOgar-Edited with root privileges.")
                break
        }
        process.exit(1) # Exits the program


        def onClientSocketOpen(ws, req):
        var req = req || ws.upgradeReq
        var logip = ws._socket.remoteAddress + ":" + ws._socket.remotePort
        ws.on('error', function (err) {
            Logger.writeError("[" + logip + "] " + err.stack)
        })
        if (self.config.serverMaxConnections && self.socketCount >= self.config.serverMaxConnections) {
            ws.close(1000, "No slots")
            return
        }
        if (self.checkIpBan(ws._socket.remoteAddress)) {
            ws.close(1000, "IP banned")
            return
        }
        if (self.config.serverIpLimit) {
            var ipConnections = 0
            for (var i = 0 i < self.clients.length i++) {
                var socket = self.clients[i]
                if (!socket.isConnected || socket.remoteAddress != ws._socket.remoteAddress)
                    continue
                ipConnections++
            }
            if (ipConnections >= self.config.serverIpLimit) {
                ws.close(1000, "IP limit reached")
                return
            }
        }
        if (self.config.clientBind.length && req.headers.origin.indexOf(self.clientBind) < 0) {
            ws.close(1000, "Client not allowed")
            return
        }
        ws.isConnected = True
        ws.remoteAddress = ws._socket.remoteAddress
        ws.remotePort = ws._socket.remotePort
        ws.lastAliveTime = Date.now()
        Logger.write("CONNECTED " + ws.remoteAddress + ":" + ws.remotePort + ", origin: \"" + req.headers.origin + "\"")


        var PlayerTracker = require('./PlayerTracker')
        ws.playerTracker = new PlayerTracker(self, ws)
        var PacketHandler = require('./PacketHandler')
        ws.packetHandler = new PacketHandler(self, ws)
        var PlayerCommand = require('./modules/PlayerCommand')
        ws.playerCommand = new PlayerCommand(self, ws.playerTracker)

        var self = self
        ws.on('message', function (message) {
            if (self.config.serverWsModule === "uws")
                # uws gives ArrayBuffer - convert it to Buffer
                message = parseInt(process.version[1]) < 6 ? Buffer.from(message) : Buffer.from(message)

            if (!message.length) return
            if (message.length > 256) {
                ws.close(1009, "Spam")
                return
            }
            ws.packetHandler.handleMessage(message)
        })
        ws.on('error', function (error) {
            ws.packetHandler.sendPacket = function (data) {}
        })
        ws.on('close', function (reason) {
            if (ws._socket && ws._socket.destroy != null && typeof ws._socket.destroy == 'function') {
                ws._socket.destroy()
            }
            self.socketCount--
            ws.isConnected = False
            ws.packetHandler.sendPacket = function (data) {}
            ws.closeReason = {
                reason: ws._closeCode,
                message: ws._closeMessage
            }
            ws.closeTime = Date.now()
            Logger.write("DISCONNECTED " + ws.remoteAddress + ":" + ws.remotePort + ", code: " + ws._closeCode +
                ", reason: \"" + ws._closeMessage + "\", name: \"" + ws.playerTracker._name + "\"")
        })
        self.socketCount++
        self.clients.push(ws)

        # Check for external minions
        self.checkMinion(ws, req)
    }

GameServer.prototype.checkMinion = function (ws, req) {
    # Check headers (maybe have a config for self?)
    if (!req.headers['user-agent'] || !req.headers['cache-control'] ||
        req.headers['user-agent'].length < 50) {
        ws.playerTracker.isMinion = True
    }
    # External minion detection
    if (self.config.serverMinionThreshold) {
        if ((ws.lastAliveTime - self.startTime) / 1000 >= self.config.serverMinionIgnoreTime) {
            if (self.minionTest.length >= self.config.serverMinionThreshold) {
                ws.playerTracker.isMinion = True
                for (var i = 0 i < self.minionTest.length i++) {
                    var playerTracker = self.minionTest[i]
                    if (!playerTracker.socket.isConnected) continue
                    playerTracker.isMinion = True
                }
                if (self.minionTest.length) self.minionTest.splice(0, 1)
            }
            self.minionTest.push(ws.playerTracker)
        }
    }
    # Add server minions if needed
    if (self.config.serverMinions && !ws.playerTracker.isMinion) {
        for (var i = 0 i < self.config.serverMinions i++) {
            self.bots.addMinion(ws.playerTracker)
            ws.playerTracker.minionControl = True
        }
    }
}

GameServer.prototype.checkIpBan = function (ipAddress) {
    if (!self.ipBanList || !self.ipBanList.length || ipAddress == "127.0.0.1") {
        return False
    }
    if (self.ipBanList.indexOf(ipAddress) >= 0) {
        return True
    }
    var ipBin = ipAddress.split('.')
    if (ipBin.length != 4) {
        # unknown IP format
        return False
    }
    var subNet2 = ipBin[0] + "." + ipBin[1] + ".*.*"
    if (self.ipBanList.indexOf(subNet2) >= 0) {
        return True
    }
    var subNet1 = ipBin[0] + "." + ipBin[1] + "." + ipBin[2] + ".*"
    if (self.ipBanList.indexOf(subNet1) >= 0) {
        return True
    }
    return False
}

GameServer.prototype.setBorder = function (width, height) {
    var hw = width / 2
    var hh = height / 2
    self.border = {
        minx: -hw,
        miny: -hh,
        maxx: hw,
        maxy: hh,
        width: width,
        height: height
    }
}

GameServer.prototype.getRandomColor = function () {
    # get random
    var colorRGB = [0xFF, 0x07, (Math.random() * 256) >> 0]
    colorRGB.sort(function () {
        return 0.5 - Math.random()
    })
    # return random
    return {
        r: colorRGB[0],
        g: colorRGB[1],
        b: colorRGB[2]
    }
}

GameServer.prototype.removeNode = function (node) {
    # Remove from quad-tree
    node.isRemoved = True
    self.quadTree.remove(node.quadItem)
    node.quadItem = null

    # Remove from node lists
    var i = self.nodes.indexOf(node)
    if (i > -1) self.nodes.splice(i, 1)
    i = self.movingNodes.indexOf(node)
    if (i > -1) self.movingNodes.splice(i, 1)

    # Special on-remove actions
    node.onRemove(self)
}

GameServer.prototype.updateClients = function () {
    # check dead clients
    var len = self.clients.length
    for (var i = 0 i < len) {
        if (!self.clients[i]) {
            i++
            continue
        }
        self.clients[i].playerTracker.checkConnection()
        if (self.clients[i].playerTracker.isRemoved)
            # remove dead client
            self.clients.splice(i, 1)
        else
            i++
    }
    # update
    for (var i = 0 i < len i++) {
        if (!self.clients[i]) continue
        self.clients[i].playerTracker.updateTick()
    }
    for (var i = 0 i < len i++) {
        if (!self.clients[i]) continue
        self.clients[i].playerTracker.sendUpdate()
    }

    # check minions
    for (var i = 0, test = self.minionTest.length i < test) {
        if (!self.minionTest[i]) {
            i++
            continue
        }
        var date = new Date() - self.minionTest[i].connectedTime
        if (date > self.config.serverMinionInterval)
            self.minionTest.splice(i, 1)
        else
            i++
    }
}

GameServer.prototype.updateLeaderboard = function () {
    # Update leaderboard with the gamemode's method
    self.leaderboard = []
    self.leaderboardType = -1
    self.gameMode.updateLB(self, self.leaderboard)

    if (!self.gameMode.specByLeaderboard) {
        # Get client with largest score if gamemode doesn't have a leaderboard
        var clients = self.clients.valueOf()

        # Use sort function
        clients.sort(function (a, b) {
            return b.playerTracker._score - a.playerTracker._score
        })
        self.largestClient = null
        if (clients[0]) self.largestClient = clients[0].playerTracker
    } else {
        self.largestClient = self.gameMode.rankOne
    }
}

GameServer.prototype.onChatMessage = function (from, to, message) {
    if (!message) return
    message = message.trim()
    if (message === "") {
        return
    }
    if (from && message.length && message[0] == '/') {
        # player command
        message = message.slice(1, message.length)
        from.socket.playerCommand.executeCommandLine(message)
        return
    }
    if (!self.config.serverChat || (from && from.isMuted)) {
        # chat is disabled or player is muted
        return
    }
    if (message.length > 64) {
        message = message.slice(0, 64)
    }
    if (self.config.serverChatAscii) {
        for (var i = 0 i < message.length i++) {
            if ((message.charCodeAt(i) < 0x20 || message.charCodeAt(i) > 0x7F) && from) {
                self.sendChatMessage(null, from, "Message failed - You can use ASCII text only!")
                return
            }
        }
    }
    if (self.checkBadWord(message) && from && self.config.badWordFilter === 1) {
        self.sendChatMessage(null, from, "Message failed - Stop insulting others! Keep calm and be friendly please.")
        return
    }
    self.sendChatMessage(from, to, message)
}

GameServer.prototype.checkBadWord = function (value) {
    if (!value) return False
    value = " " + value.toLowerCase().trim() + " "
    for (var i = 0 i < self.badWords.length i++) {
        if (value.indexOf(self.badWords[i]) >= 0) {
            return True
        }
    }
    return False
}

GameServer.prototype.sendChatMessage = function (from, to, message) {
    for (var i = 0, len = self.clients.length i < len i++) {
        if (!self.clients[i]) continue
        if (!to || to == self.clients[i].playerTracker) {
            var Packet = require('./packet')
            if (self.config.separateChatForTeams && self.gameMode.haveTeams) {
                #  from equals null if message from server
                if (from == null || from.team === self.clients[i].playerTracker.team) {
                    self.clients[i].packetHandler.sendPacket(new Packet.ChatMessage(from, message))
                }
            } else {
                self.clients[i].packetHandler.sendPacket(new Packet.ChatMessage(from, message))
            }
        }

    }
}

GameServer.prototype.timerLoop = function () {
    var timeStep = 40 # vanilla: 40
    var ts = Date.now()
    var dt = ts - self.timeStamp
    if (dt < timeStep - 5) {
        setTimeout(self.timerLoopBind, timeStep - 5)
        return
    }
    if (dt > 120) self.timeStamp = ts - timeStep
    # update average, calculate next
    self.updateTimeAvg += 0.5 * (self.updateTime - self.updateTimeAvg)
    self.timeStamp += timeStep
    setTimeout(self.mainLoopBind, 0)
    setTimeout(self.timerLoopBind, 0)
}

GameServer.prototype.mainLoop = function () {
    self.stepDateTime = Date.now()
    var tStart = process.hrtime()
    var self = self

    # Restart
    if (self.tickCounter > self.config.serverRestart) {
        var QuadNode = require('./modules/QuadNode.js')
        self.httpServer = null
        self.wsServer = null
        self.run = True
        self.lastNodeId = 1
        self.lastPlayerId = 1
        for (var i = 0 i < self.clients.length i++) {
            var client = self.clients[i]
            client.close()
        }
        self.nodes = []
        self.nodesVirus = []
        self.nodesFood = []
        self.nodesEjected = []
        self.nodesPlayer = []
        self.movingNodes = []
        if (self.config.serverBots) {
            for (var i = 0 i < self.config.serverBots i++)
                self.bots.addBot()
            Logger.info("Added " + self.config.serverBots + " player bots")
        }
        self.commands
        self.tickCounter = 0
        self.startTime = Date.now()
        self.setBorder(self.config.borderWidth, self.config.borderHeight)
        self.quadTree = new QuadNode(self.border, 64, 32)
    }

    # Loop main functions
    if (self.run) {
        # Move moving nodes first
        self.movingNodes.forEach((cell) => {
            if (cell.isRemoved) return
            # Scan and check for ejected mass / virus collisions
            self.boostCell(cell)
            self.quadTree.find(cell.quadItem.bound, function (check) {
                var m = self.checkCellCollision(cell, check)
                if (cell.cellType == 3 && check.cellType == 3 && !self.config.mobilePhysics)
                    self.resolveRigidCollision(m)
                else
                    self.resolveCollision(m)
            })
            if (!cell.isMoving)
                self.movingNodes = null
        })
        # Update players and scan for collisions
        var eatCollisions = []
        self.nodesPlayer.forEach((cell) => {
            if (cell.isRemoved) return
            # Scan for eat/rigid collisions and resolve them
            self.quadTree.find(cell.quadItem.bound, function (check) {
                var m = self.checkCellCollision(cell, check)
                if (self.checkRigidCollision(m))
                    self.resolveRigidCollision(m)
                else if (check != cell)
                    eatCollisions.unshift(m)
            })
            self.movePlayer(cell, cell.owner)
            self.boostCell(cell)
            self.autoSplit(cell, cell.owner)
            # Decay player cells once per second
            if (((self.tickCounter + 3) % 25) === 0)
                self.updateSizeDecay(cell)
            # Remove external minions if necessary
            if (cell.owner.isMinion) {
                cell.owner.socket.close(1000, "Minion")
                self.removeNode(cell)
            }
        })
        eatCollisions.forEach((m) => {
            self.resolveCollision(m)
        })
        if ((self.tickCounter % self.config.spawnInterval) === 0) {
            # Spawn food & viruses
            self.spawnCells()
        }
        self.gameMode.onTick(self)
        self.tickCounter++
    }
    if (!self.run && self.gameMode.IsTournament)
        self.tickCounter++
    self.updateClients()

    # update leaderboard
    if (((self.tickCounter + 7) % 25) === 0)
        self.updateLeaderboard() # once per second

    # ping server tracker
    if (self.config.serverTracker && (self.tickCounter % 750) === 0)
        self.pingServerTracker() # once per 30 seconds

    # update-update time
    var tEnd = process.hrtime(tStart)
    self.updateTime = tEnd[0] * 1e3 + tEnd[1] / 1e6
}

# update remerge first
GameServer.prototype.movePlayer = function (cell, client) {
    if (client.socket.isConnected == False || client.frozen || !client.mouse)
        return # Do not move

    # get movement from vector
    var d = client.mouse.clone().sub(cell.position)
    var move = cell.getSpeed(d.sqDist()) # movement speed
    if (!move) return # avoid jittering
    cell.position.add(d, move)

    # update remerge
    var time = self.config.playerRecombineTime,
        base = Math.max(time, cell._size * 0.2) * 25
    # instant merging conditions
    if (!time || client.rec || client.mergeOverride) {
        cell._canRemerge = cell.boostDistance < 100
        return # instant merge
    }
    # regular remerge time
    cell._canRemerge = cell.getAge() >= base
}

# decay player cells
GameServer.prototype.updateSizeDecay = function (cell) {
    var rate = self.config.playerDecayRate,
        cap = self.config.playerDecayCap

    if (!rate || cell._size <= self.config.playerMinSize)
        return

    # remove size from cell at decay rate
    if (cap && cell._mass > cap) rate *= 10
    var decay = 1 - rate * self.gameMode.decayMod
    cell.setSize(Math.sqrt(cell.radius * decay))
}

GameServer.prototype.boostCell = function (cell) {
    if (cell.isMoving && !cell.boostDistance || cell.isRemoved) {
        cell.boostDistance = 0
        cell.isMoving = False
        return
    }
    # decay boost-speed from distance
    var speed = cell.boostDistance / 9 # val: 87
    cell.boostDistance -= speed # decays from speed
    cell.position.add(cell.boostDirection, speed)

    # update boundries
    cell.checkBorder(self.border)
    self.updateNodeQuad(cell)
}

GameServer.prototype.autoSplit = function (cell, client) {
    # get size limit based off of rec mode
    if (client.rec) var maxSize = 1e9 # increase limit for rec (1 bil)
    else maxSize = self.config.playerMaxSize

    # check size limit
    if (client.mergeOverride || cell._size < maxSize) return
    if (client.cells.length >= self.config.playerMaxCells || self.config.mobilePhysics) {
        # cannot split => just limit
        cell.setSize(maxSize)
    } else {
        # split in random direction
        var angle = Math.random() * 2 * Math.PI
        self.splitPlayerCell(client, cell, angle, cell._mass * .5)
    }
}

GameServer.prototype.updateNodeQuad = function (node) {
    # update quad tree
    var item = node.quadItem.bound
    item.minx = node.position.x - node._size
    item.miny = node.position.y - node._size
    item.maxx = node.position.x + node._size
    item.maxy = node.position.y + node._size
    self.quadTree.remove(node.quadItem)
    self.quadTree.insert(node.quadItem)
}

# Checks cells for collision
GameServer.prototype.checkCellCollision = function (cell, check) {
    var p = check.position.clone().sub(cell.position)

    # create collision manifold
    return {
        cell: cell,
        check: check,
        d: p.sqDist(), # distance from cell to check
        p: p # check - cell position
    }
}

# Checks if collision is rigid body collision
GameServer.prototype.checkRigidCollision = function (m) {
    if (!m.cell.owner || !m.check.owner)
        return False

    if (m.cell.owner != m.check.owner) {
        # Minions don't collide with their team when the config value is 0
        if (self.gameMode.haveTeams && m.check.owner.isMi || m.cell.owner.isMi && self.config.minionCollideTeam === 0) {
            return False
        } else {
            # Different owners => same team
            return self.gameMode.haveTeams &&
                m.cell.owner.team == m.check.owner.team
        }
    }
    var r = self.config.mobilePhysics ? 1 : 13
    if (m.cell.getAge() < r || m.check.getAge() < r) {
        return False # just splited => ignore
    }
    return !m.cell._canRemerge || !m.check._canRemerge
}

# Resolves rigid body collisions
GameServer.prototype.resolveRigidCollision = function (m) {
    var push = (m.cell._size + m.check._size - m.d) / m.d
    if (push <= 0 || m.d == 0) return # do not extrude

    # body impulse
    var rt = m.cell.radius + m.check.radius
    var r1 = push * m.cell.radius / rt
    var r2 = push * m.check.radius / rt

    # apply extrusion force
    m.cell.position.sub2(m.p, r2)
    m.check.position.add(m.p, r1)
}

# Resolves non-rigid body collision
GameServer.prototype.resolveCollision = function (m) {
    var cell = m.cell
    var check = m.check
    if (cell._size > check._size) {
        cell = m.check
        check = m.cell
    }
    # Do not resolve removed
    if (cell.isRemoved || check.isRemoved)
        return

    # check eating distance
    check.div = self.config.mobilePhysics ? 20 : 3
    if (m.d >= check._size - cell._size / check.div) {
        return # too far => can't eat
    }

    # collision owned => ignore, resolve, or remerge
    if (cell.owner && cell.owner == check.owner) {
        if (cell.getAge() < 13 || check.getAge() < 13)
            return # just splited => ignore
    } else if (check._size < cell._size * 1.15 || !check.canEat(cell))
        return # Cannot eat or cell refuses to be eaten

    # Consume effect
    check.onEat(cell)
    cell.onEaten(check)
    cell.killedBy = check

    # Remove cell
    self.removeNode(cell)
}

GameServer.prototype.splitPlayerCell = function (client, parent, angle, mass) {
    var size = Math.sqrt(mass * 100)
    var size1 = Math.sqrt(parent.radius - size * size)

    # Too small to split
    if (!size1 || size1 < self.config.playerMinSize)
        return

    # Remove size from parent cell
    parent.setSize(size1)

    # Create cell and add it to node list
    var newCell = new Entity.PlayerCell(self, client, parent.position, size)
    newCell.setBoost(self.config.splitVelocity * Math.pow(size, 0.0122), angle)
    self.addNode(newCell)
}

GameServer.prototype.randomPos = function () {
    return new Vec2(
        self.border.minx + self.border.width * Math.random(),
        self.border.miny + self.border.height * Math.random()
    )
}

GameServer.prototype.spawnCells = function () {
    # spawn food at random size
    var maxCount = self.config.foodMinAmount - self.nodesFood.length
    var spawnCount = Math.min(maxCount, self.config.foodSpawnAmount)
    for (var i = 0 i < spawnCount i++) {
        var cell = new Entity.Food(self, null, self.randomPos(), self.config.foodMinSize)
        if (self.config.foodMassGrow) {
            var maxGrow = self.config.foodMaxSize - cell._size
            cell.setSize(cell._size += maxGrow * Math.random())
        }
        cell.color = self.getRandomColor()
        self.addNode(cell)
    }

    # spawn viruses (safely)
    if (self.nodesVirus.length < self.config.virusMinAmount) {
        var virus = new Entity.Virus(self, null, self.randomPos(), self.config.virusMinSize)
        if (!self.willCollide(virus)) self.addNode(virus)
    }
}

GameServer.prototype.spawnPlayer = function (player, pos) {
    if (self.disableSpawn) return # Not allowed to spawn!

    # Check for special starting size
    var size = self.config.playerStartSize
    if (player.spawnmass) size = player.spawnmass

    # Check if can spawn from ejected mass
    var index = ~~(self.nodesEjected.length * Math.random())
    var eject = self.nodesEjected[index] # Randomly selected
    if (Math.random() <= self.config.ejectSpawnPercent &&
        eject && eject.boostDistance < 1) {
        # Spawn from ejected mass
        pos = eject.position.clone()
        player.color = eject.color
        size = Math.max(size, eject._size * 1.15)
    }
    # Spawn player safely (do not check minions)
    var cell = new Entity.PlayerCell(self, player, pos, size)
    if (self.willCollide(cell) && !player.isMi)
        pos = self.randomPos() # Not safe => retry
    self.addNode(cell)

    # Set initial mouse coords
    player.mouse = new Vec2(pos.x, pos.y)
}

GameServer.prototype.willCollide = function (cell) {
    var notSafe = False # Safe by default
    var sqSize = cell.radius
    var pos = self.randomPos()
    var d = cell.position.clone().sub(pos)
    if (d.dist() + sqSize <= sqSize * 2) {
        notSafe = True
    }
    self.quadTree.find({
        minx: cell.position.x - cell._size,
        miny: cell.position.y - cell._size,
        maxx: cell.position.x + cell._size,
        maxy: cell.position.y + cell._size
    }, function (n) {
        if (n.cellType == 0) notSafe = True
    })
    return notSafe
}

GameServer.prototype.splitCells = function (client) {
    # Split cell order decided by cell age
    var cellToSplit = []
    for (var i = 0 i < client.cells.length i++)
        cellToSplit.push(client.cells[i])

    # Split split-able cells
    cellToSplit.forEach((cell) => {
        var d = client.mouse.clone().sub(cell.position)
        if (d.dist() < 1) {
            d.x = 1, d.y = 0
        }

        if (cell._size < self.config.playerMinSplitSize)
            return # cannot split

        # Get maximum cells for rec mode
        if (client.rec) var max = 200 # rec limit
        else max = self.config.playerMaxCells
        if (client.cells.length >= max) return

        # Now split player cells
        self.splitPlayerCell(client, cell, d.angle(), cell._mass * .5)
    })
}

GameServer.prototype.canEjectMass = function (client) {
    if (client.lastEject === null) {
        # first eject
        client.lastEject = self.tickCounter
        return True
    }
    var dt = self.tickCounter - client.lastEject
    if (dt < self.config.ejectCooldown) {
        # reject (cooldown)
        return False
    }
    client.lastEject = self.tickCounter
    return True
}

GameServer.prototype.ejectMass = function (client) {
    if (!self.canEjectMass(client) || client.frozen)
        return
    for (var i = 0 i < client.cells.length i++) {
        var cell = client.cells[i]

        if (cell._size < self.config.playerMinEjectSize)
            continue # Too small to eject

        var d = client.mouse.clone().sub(cell.position)
        var sq = d.sqDist()
        d.x = sq > 1 ? d.x / sq : 1
        d.y = sq > 1 ? d.y / sq : 0

        # Remove mass from parent cell first
        var loss = self.config.ejectSizeLoss
        loss = cell.radius - loss * loss
        cell.setSize(Math.sqrt(loss))

        # Get starting position
        var pos = new Vec2(
            cell.position.x + d.x * cell._size,
            cell.position.y + d.y * cell._size
        )
        var angle = d.angle() + (Math.random() * .6) - .3

        # Create cell and add it to node list
        if (!self.config.ejectVirus) {
            var ejected = new Entity.EjectedMass(self, null, pos, self.config.ejectSize)
        } else {
            ejected = new Entity.Virus(self, null, pos, self.config.ejectSize)
        }
        ejected.color = cell.color
        ejected.setBoost(self.config.ejectVelocity, angle)
        self.addNode(ejected)
    }
}

GameServer.prototype.shootVirus = function (parent, angle) {
    # Create virus and add it to node list
    var pos = parent.position.clone()
    var newVirus = new Entity.Virus(self, null, pos, self.config.virusMinSize)
    newVirus.setBoost(self.config.virusVelocity, angle)
    self.addNode(newVirus)
}

GameServer.prototype.loadFiles = function () {
    # Load config
    var fs = require("fs")
    var fileNameConfig = self.srcFiles + '/gameserver.ini'
    var ini = require(self.srcFiles + '/modules/ini.js')
    try {
        if (!fs.existsSync(fileNameConfig)) {
            # No config
            Logger.warn("Config not found... Generating new config")
            # Create a new config
            fs.writeFileSync(fileNameConfig, ini.stringify(self.config), 'utf-8')
        } else {
            # Load the contents of the config file
            var load = ini.parse(fs.readFileSync(fileNameConfig, 'utf-8'))
            # Replace all the default config's values with the loaded config's values
            for (var key in load) {
                if (self.config.hasOwnProperty(key)) self.config[key] = load[key]
                else Logger.error("Unknown gameserver.ini value: " + key)
            }
        }
    } catch (err) {
        Logger.error(err.stack)
        Logger.error("Failed to load " + fileNameConfig + ": " + err.message)
    }
    Logger.setVerbosity(self.config.logVerbosity)
    Logger.setFileVerbosity(self.config.logFileVerbosity)

    # Load bad words
    var fileNameBadWords = self.srcFiles + '/badwords.txt'
    try {
        if (!fs.existsSync(fileNameBadWords)) {
            Logger.warn(fileNameBadWords + " not found")
        } else {
            var words = fs.readFileSync(fileNameBadWords, 'utf-8')
            words = words.split(/[\r\n]+/)
            words = words.map(function (arg) {
                return " " + arg.trim().toLowerCase() + " " # Formatting
            })
            words = words.filter(function (arg) {
                return arg.length > 2
            })
            self.badWords = words
            Logger.info(self.badWords.length + " bad words loaded")
        }
    } catch (err) {
        Logger.error(err.stack)
        Logger.error("Failed to load " + fileNameBadWords + ": " + err.message)
    }

    # Load user list
    var UserRoleEnum = require(self.srcFiles + '/enum/UserRoleEnum')
    var fileNameUsers = self.srcFiles + '/enum/userRoles.json'
    try {
        self.userList = []
        if (!fs.existsSync(fileNameUsers)) {
            Logger.warn(fileNameUsers + " is missing.")
            return
        }
        var usersJson = fs.readFileSync(fileNameUsers, 'utf-8')
        var list = JSON.parse(usersJson.trim())
        for (var i = 0 i < list.length) {
            var item = list[i]
            if (!item.hasOwnProperty("ip") ||
                !item.hasOwnProperty("password") ||
                !item.hasOwnProperty("role") ||
                !item.hasOwnProperty("name")) {
                list.splice(i, 1)
                continue
            }
            if (!item.password || !item.password.trim()) {
                Logger.warn("User account \"" + item.name + "\" disabled")
                list.splice(i, 1)
                continue
            }
            if (item.ip) item.ip = item.ip.trim()
            item.password = item.password.trim()
            if (!UserRoleEnum.hasOwnProperty(item.role)) {
                Logger.warn("Unknown user role: " + item.role)
                item.role = UserRoleEnum.USER
            } else {
                item.role = UserRoleEnum[item.role]
            }
            item.name = (item.name || "").trim()
            i++
        }
        self.userList = list
        Logger.info(self.userList.length + " user records loaded.")
    } catch (err) {
        Logger.error(err.stack)
        Logger.error("Failed to load " + fileNameUsers + ": " + err.message)
    }

    # Load ip ban list
    var fileNameIpBan = self.srcFiles + '/ipbanlist.txt'
    try {
        if (fs.existsSync(fileNameIpBan)) {
            # Load and input the contents of the ipbanlist file
            self.ipBanList = fs.readFileSync(fileNameIpBan, "utf8").split(/[\r\n]+/).filter(function (x) {
                return x != '' # filter empty lines
            })
            Logger.info(self.ipBanList.length + " IP ban records loaded.")
        } else {
            Logger.warn(fileNameIpBan + " is missing.")
        }
    } catch (err) {
        Logger.error(err.stack)
        Logger.error("Failed to load " + fileNameIpBan + ": " + err.message)
    }

    # Convert config settings
    self.config.serverRestart = self.config.serverRestart === 0 ? 1e999 : self.config.serverRestart * 1500
}

GameServer.prototype.startStatsServer = function (port) {
    # Create stats
    self.stats = "Test"
    self.getStats()

    # Show stats
    self.httpServer = http.createServer(function (req, res) {
        res.setHeader('Access-Control-Allow-Origin', '*')
        res.writeHead(200)
        res.end(self.stats)
    }.bind(self))
    self.httpServer.on('error', function (err) {
        Logger.error("Stats Server: " + err.message)
    })

    var getStatsBind = self.getStats.bind(self)
    self.httpServer.listen(port, function () {
        # Stats server
        Logger.info("Started stats server on port " + port)
        setInterval(getStatsBind, self.config.serverStatsUpdate * 1000)
    }.bind(self))
}

GameServer.prototype.getStats = function () {
    # Get server statistics
    var totalPlayers = 0
    var alivePlayers = 0
    var spectatePlayers = 0
    for (var i = 0, len = self.clients.length i < len i++) {
        var socket = self.clients[i]
        if (!socket || !socket.isConnected || socket.playerTracker.isMi)
            continue
        totalPlayers++
        if (socket.playerTracker.cells.length) alivePlayers++
        else spectatePlayers++
    }
    var s = {
        'server_name': self.config.serverName,
        'server_chat': self.config.serverChat ? "True" : "False",
        'border_width': self.border.width,
        'border_height': self.border.height,
        'gamemode': self.gameMode.name,
        'max_players': self.config.serverMaxConnections,
        'current_players': totalPlayers,
        'alive': alivePlayers,
        'spectators': spectatePlayers,
        'update_time': self.updateTimeAvg.toFixed(3),
        'uptime': Math.round((self.stepDateTime - self.startTime) / 1000 / 60),
        'start_time': self.startTime
    }
    self.stats = JSON.stringify(s)
}

# Pings the server tracker, should be called every 30 seconds
# To list us on the server tracker located at http:#ogar.mivabe.nl/master
GameServer.prototype.pingServerTracker = function () {
    # Get server statistics
    var os = require('os')
    var totalPlayers = 0
    var alivePlayers = 0
    var spectatePlayers = 0
    var robotPlayers = 0
    for (var i = 0, len = self.clients.length i < len i++) {
        var socket = self.clients[i]
        if (!socket || socket.isConnected == False)
            continue
        if (socket.isConnected == null) {
            robotPlayers++
        } else {
            totalPlayers++
            if (socket.playerTracker.cells.length) alivePlayers++
            else spectatePlayers++
        }
    }

    # ogar.mivabe.nl/master
    var data = 'current_players=' + totalPlayers +
        '&alive=' + alivePlayers +
        '&spectators=' + spectatePlayers +
        '&max_players=' + self.config.serverMaxConnections +
        '&sport=' + self.config.serverPort +
        '&gamemode=[**] ' + self.gameMode.name + # we add [**] to indicate that self is MultiOgar-Edited server
        '&agario=True' + # protocol version
        '&name=Unnamed Server' + # we cannot use it, because other value will be used as dns name
        '&opp=' + os.platform() + ' ' + os.arch() + # "win32 x64"
        '&uptime=' + process.uptime() + # Number of seconds server has been running
        '&version=MultiOgar-Edited ' + self.version +
        '&start_time=' + self.startTime
    trackerRequest({
        host: 'ogar.mivabe.nl',
        port: 80,
        path: '/master',
        method: 'POST'
    }, 'application/x-www-form-urlencoded', data)
}

function trackerRequest(options, type, body) {
    if (options.headers == null) options.headers = {}
    options.headers['user-agent'] = 'MultiOgar-Edited' + self.version
    options.headers['content-type'] = type
    options.headers['content-length'] = body == null ? 0 : Buffer.byteLength(body, 'utf8')
    var req = http.request(options, function (res) {
        if (res.statusCode != 200) {
            Logger.writeError("[Tracker][" + options.host + "]: statusCode = " + res.statusCode)
            return
        }
        res.setEncoding('utf8')
    })
    req.on('error', function (err) {
        Logger.writeError("[Tracker][" + options.host + "]: " + err)
    })
    req.shouldKeepAlive = False
    req.on('close', function () {
        req.destroy()
    })
    req.write(body)
    req.end()
}