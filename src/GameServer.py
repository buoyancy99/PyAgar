import numpy as np
import math
from Config import Config
import random
from datetime import datetime

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

        BotLoader = require('./ai/BotLoader')
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
        QuadNode = require('./modules/QuadNode.js')
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
        self.nodes.append(node)

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
        req = req or ws.upgradeReq
        logip = ws._socket.remoteAddress + ":" + ws._socket.remotePort
        ws.on('error', function (err) {
            Logger.writeError("[" + logip + "] " + err.stack)
        })
        if (self.config.serverMaxConnections and self.socketCount >= self.config.serverMaxConnections) {
            ws.close(1000, "No slots")
            return
        }
        if (self.checkIpBan(ws._socket.remoteAddress)) {
            ws.close(1000, "IP banned")
            return
        }
        if (self.config.serverIpLimit) {
            ipConnections = 0
            for (i = 0 i < self.clients.length i++) {
                socket = self.clients[i]
                if (!socket.isConnected or socket.remoteAddress != ws._socket.remoteAddress)
                    continue
                ipConnections++
            }
            if (ipConnections >= self.config.serverIpLimit) {
                ws.close(1000, "IP limit reached")
                return
            }
        }
        if (self.config.clientBind.length and req.headers.origin.indexOf(self.clientBind) < 0) {
            ws.close(1000, "Client not allowed")
            return
        }
        ws.isConnected = True
        ws.remoteAddress = ws._socket.remoteAddress
        ws.remotePort = ws._socket.remotePort
        ws.lastAliveTime = Date.now()
        Logger.write("CONNECTED " + ws.remoteAddress + ":" + ws.remotePort + ", origin: \"" + req.headers.origin + "\"")


        PlayerTracker = require('./PlayerTracker')
        ws.playerTracker = new PlayerTracker(self, ws)
        PacketHandler = require('./PacketHandler')
        ws.packetHandler = new PacketHandler(self, ws)
        PlayerCommand = require('./modules/PlayerCommand')
        ws.playerCommand = new PlayerCommand(self, ws.playerTracker)

        self = self
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
            ws.packetHandler.sendPacket(selfdata) {}
        })
        ws.on('close', function (reason) {
            if (ws._socket and ws._socket.destroy != null and typeof ws._socket.destroy == 'function') {
                ws._socket.destroy()
            }
            self.socketCount--
            ws.isConnected = False
            ws.packetHandler.sendPacket(selfdata) {}
            ws.closeReason = {
                reason: ws._closeCode,
                message: ws._closeMessage
            }
            ws.closeTime = Date.now()
            Logger.write("DISCONNECTED " + ws.remoteAddress + ":" + ws.remotePort + ", code: " + ws._closeCode +
                ", reason: \"" + ws._closeMessage + "\", name: \"" + ws.playerTracker._name + "\"")
        })
        self.socketCount++
        self.clients.append(ws)

        # Check for external minions
        self.checkMinion(ws, req)
    }

    def checkMinion(selfws, req) {
    # Check headers (maybe have a config for self?)
    if (!req.headers['user-agent'] or !req.headers['cache-control'] or
        req.headers['user-agent'].length < 50) {
        ws.playerTracker.isMinion = True
    }
    # External minion detection
    if (self.config.serverMinionThreshold) {
        if ((ws.lastAliveTime - self.startTime) / 1000 >= self.config.serverMinionIgnoreTime) {
            if (self.minionTest.length >= self.config.serverMinionThreshold) {
                ws.playerTracker.isMinion = True
                for (i = 0 i < self.minionTest.length i++) {
                    playerTracker = self.minionTest[i]
                    if (!playerTracker.socket.isConnected) continue
                    playerTracker.isMinion = True
                }
                if (self.minionTest.length) self.minionTest.splice(0, 1)
            }
            self.minionTest.append(ws.playerTracker)
        }
    }
    # Add server minions if needed
    if (self.config.serverMinions and !ws.playerTracker.isMinion) {
        for (i = 0 i < self.config.serverMinions i++) {
            self.bots.addMinion(ws.playerTracker)
            ws.playerTracker.minionControl = True
        }
    }
}

    def setBorder(width, height):
        hw = width / 2
        hh = height / 2
        self.border = {
        "minx": -hw,
        "miny": -hh,
        "maxx": hw,
        "maxy": hh,
        "width": width,
        "height": height
        }


    def getRandomColor():
        colorRGB = [0xff, 0x07, random.randint(256) // 2]
        random.shuffle(colorRGB)
        # return random
        return {'r': colorRGB[0], 'g': colorRGB[1], 'b': colorRGB[2]}


    def removeNode(node):
        # Remove from quad-tree
        node.isRemoved = True
        self.quadTree.remove(node.quadItem)
        node.quadItem = None

        # Remove from node lists
        i = self.nodes.index(node)
        if i > -1:
            self.nodes.pop(i)
            i = self.movingNodes.index(node)
        if i > -1:
            self.movingNodes.pop(i)

        # Special on-remove actions
        node.onRemove(self)

    def updateClients():
        # check dead clients
        len = self.clients.length
        for (i = 0 i < len) {
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
        for (i = 0 i < len i++) {
            if (!self.clients[i]) continue
            self.clients[i].playerTracker.updateTick()
        }
        for (i = 0 i < len i++) {
            if (!self.clients[i]) continue
            self.clients[i].playerTracker.sendUpdate()
        }

        # check minions
        for (i = 0, test = self.minionTest.length i < test) {
            if (!self.minionTest[i]) {
                i++
                continue
            }
            date = new Date() - self.minionTest[i].connectedTime
            if (date > self.config.serverMinionInterval)
                self.minionTest.splice(i, 1)
            else
                i++
        }

    def timerLoop(self):
        timeStep = 40 # vanilla: 40
        ts = datetime.now()
        dt = ts - self.timeStamp
        if dt < timeStep - 5:
            setTimeout(self.timerLoopBind, timeStep - 5)
            return

        if dt > 120:
            self.timeStamp = ts - timeStep
        # update average, calculate next
        self.updateTimeAvg += 0.5 * (self.updateTime - self.updateTimeAvg)
        self.timeStamp += timeStep
        setTimeout(self.mainLoopBind, 0)
        setTimeout(self.timerLoopBind, 0)


    def mainLoop(self):
        self.stepDateTime = datetime.now()
        tStart = process.hrtime()
        self = self

        # Restart
        if self.tickCounter > self.config.serverRestart:
            QuadNode = require('./modules/QuadNode.js')
            self.httpServer = None
            self.wsServer = None
            self.run = True
            self.lastNodeId = 1
            self.lastPlayerId = 1
            for i in range(self.clients.length):
                self.clients[i].close()

            self.nodes = []
            self.nodesVirus = []
            self.nodesFood = []
            self.nodesEjected = []
            self.nodesPlayer = []
            self.movingNodes = []
            if self.config.serverBots:
                for i in range(self.config.serverBots):
                    self.bots.addBot()
                Logger.info("Added " + self.config.serverBots + " player bots")

            self.tickCounter = 0
            self.startTime = datetime.now()
            self.setBorder(self.config.borderWidth, self.config.borderHeight)
            self.quadTree = new QuadNode(self.border, 64, 32)


        # Loop main functions
        if self.run:
            # Move moving nodes first
            for cell in self.movingNodes:
                if cell.isRemoved:
                    return
                # Scan and check for ejected mass / virus collisions
                self.boostCell(cell)
                self.quadTree.find(cell.quadItem.bound, function (check) {
                    m = self.checkCellCollision(cell, check)
                    if (cell.cellType == 3 and check.cellType == 3 and not self.config.mobilePhysics:
                        self.resolveRigidCollision(m)
                    else:
                        self.resolveCollision(m)
                })
                if not cell.isMoving:
                    self.movingNodes = None

            # Update players and scan for collisions
            eatCollisions = []
            self.nodesPlayer.forEach((cell) => {
                if (cell.isRemoved) return
                # Scan for eat/rigid collisions and resolve them
                self.quadTree.find(cell.quadItem.bound, function (check) {
                    m = self.checkCellCollision(cell, check)
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
        if (not self.run and self.gameMode.IsTournament):
            self.tickCounter+=1
        self.updateClients()

        # update leaderboard
        if (((self.tickCounter + 7) % 25) == 0):
            self.updateLeaderboard() # once per second

        # ping server tracker
        if (self.config.serverTracker and (self.tickCounter % 750) === 0)
            self.pingServerTracker() # once per 30 seconds

        # update-update time
        tEnd = process.hrtime(tStart)
        self.updateTime = tEnd[0] * 1e3 + tEnd[1] / 1e6
}

# update remerge first
    def movePlayer(self, cell, client):
        if (client.socket.isConnected == False or client.frozen or not client.mouse):
            return # Do not move

        # get movement from vector
        d = client.mouse.clone().sub(cell.position)
        move = cell.getSpeed(d.sqDist()) # movement speed
        if not move:
            return # avoid jittering
        cell.position.add(d, move)

        # update remerge
        time = self.config.playerRecombineTime,
        base = math.max(time, cell._size * 0.2) * 25
        # instant merging conditions
        if (not time or client.rec or client.mergeOverride):
            cell._canRemerge = cell.boostDistance < 100
            return # instant merge

        # regular remerge time
        cell._canRemerge = cell.getAge() >= base


# decay player cells
    def updateSizeDecay(self, cell):
        rate = self.config.playerDecayRate
        cap = self.config.playerDecayCap

        if (not rate or cell._size <= self.config.playerMinSize):
            return

        # remove size from cell at decay rate
        if (cap and cell._mass > cap):
            rate *= 10
        decay = 1 - rate * self.gameMode.decayMod
        cell.setSize(math.sqrt(cell.radius * decay))


    def boostCell(self, cell):
        if (cell.isMoving and not cell.boostDistance or cell.isRemoved):
            cell.boostDistance = 0
            cell.isMoving = False
            return
        # decay boost-speed from distance
        speed = cell.boostDistance / 9 # val: 87
        cell.boostDistance -= speed # decays from speed
        cell.position.add(cell.boostDirection, speed)

        # update boundries
        cell.checkBorder(self.border)
        self.updateNodeQuad(cell)

    def autoSplit(self, cell, client):
        # get size limit based off of rec mode
        if client.rec:
            maxSize = 1e9 # increase limit for rec (1 bil)
        else:
            maxSize = self.config.playerMaxSize

        # check size limit
        if client.mergeOverride or cell._size < maxSize:
            return
        if client.cells.length >= self.config.playerMaxCells or self.config.mobilePhysics:
            # cannot split => just limit
            cell.setSize(maxSize)
        else:
            # split in random direction
            angle = math.random() * 2 * math.PI
            self.splitPlayerCell(client, cell, angle, cell._mass * .5)



    def updateNodeQuad(self, node):
        # update quad tree
        item = node.quadItem.bound
        item.minx = node.position.x - node.size
        item.miny = node.position.y - node.size
        item.maxx = node.position.x + node.size
        item.maxy = node.position.y + node.size
        self.quadTree.remove(node.quadItem)
        self.quadTree.insert(node.quadItem)


# Checks cells for collision
    def checkCellCollision(self, cell, check):
        p = check.position.clone().sub(cell.position)

    # create collision manifold
        return {'cell': cell, 'check': check, 'd': p.sqDist(), 'p': p}


# Checks if collision is rigid body collision
    def checkRigidCollision(self, m):
        if not m.cell.owner or not m.check.owner:
            return False

        if m.cell.owner != m.check.owner:
            # Minions don't collide with their team when the config value is 0
            if (self.gameMode.haveTeams and m.check.owner.isMi or m.cell.owner.isMi and self.config.minionCollideTeam == 0):
                return False
            else:
                # Different owners => same team
                return self.gameMode.haveTeams and m.cell.owner.team == m.check.owner.team

        r = 1 if self.config.mobilePhysics else 13
        if (m.cell.getAge() < r or m.check.getAge() < r):
            return False # just splited => ignore

        return not m.cell._canRemerge or not m.check._canRemerge


# Resolves rigid body collisions
    def resolveRigidCollision(self, m):
        push = (m.cell._size + m.check._size - m.d) / m.d
        if (push <= 0 or m.d == 0):
            return # do not extrude

        # body impulse
        rt = m.cell.radius + m.check.radius
        r1 = push * m.cell.radius / rt
        r2 = push * m.check.radius / rt

        # apply extrusion force
        m.cell.position.sub2(m.p, r2)
        m.check.position.add(m.p, r1)


# Resolves non-rigid body collision
    def resolveCollision(m):
        cell = m.cell
        check = m.check
        if cell._size > check._size:
            cell = m.check
            check = m.cell

        # Do not resolve removed
        if cell.isRemoved or check.isRemoved:
            return

        # check eating distance
        check.div = 20 if self.config.mobilePhysics else 3
        if m.d >= check._size - cell._size / check.div:
            return # too far => can't eat


        # collision owned => ignore, resolve, or remerge
        if cell.owner and cell.owner == check.owner:
            if (cell.getAge() < 13 or check.getAge() < 13):
                return # just splited => ignore
        elif check._size < cell._size * 1.15 or not check.canEat(cell):
            return # Cannot eat or cell refuses to be eaten

        # Consume effect
        check.onEat(cell)
        cell.onEaten(check)
        cell.killedBy = check

        # Remove cell
        self.removeNode(cell)


    def plitPlayerCell(self, client, parent, angle, mass):
        size = math.sqrt(mass * 100)
        size1 = math.sqrt(parent.radius - size * size)

        # Too small to split
        if not size1 or size1 < self.config.playerMinSize:
            return

        # Remove size from parent cell
        parent.setSize(size1)

        # Create cell and add it to node list
        newCell = Entity.PlayerCell(self, client, parent.position, size)
        newCell.setBoost(self.config.splitVelocity * math.pow(size, 0.0122), angle)
        self.addNode(newCell)


    def randomPos(self):
        return np.array([
            self.border.minx + self.border.width * math.random(),
            self.border.miny + self.border.height * math.random()]
        )


    def spawnCells(self):
        # spawn food at random size
        maxCount = self.config.foodMinAmount - self.nodesFood.length
        spawnCount = math.min(maxCount, self.config.foodSpawnAmount)
        for i in range(spawnCount):
            cell = Entity.Food(self, None, self.randomPos(), self.config.foodMinSize)
            if self.config.foodMassGrow:
                maxGrow = self.config.foodMaxSize - cell._size
                cell.setSize(cell._size += maxGrow * math.random())

            cell.color = self.getRandomColor()
            self.addNode(cell)

        # spawn viruses (safely)
        if (self.nodesVirus.length < self.config.virusMinAmount):
            virus = Entity.Virus(self, None, self.randomPos(), self.config.virusMinSize)
            if not self.willCollide(virus):
                self.addNode(virus)


    def spawnPlayer(self, player, pos):
        if self.disableSpawn:
            return

        # Check for special starting size
        size = self.config.playerStartSize
        if player.spawnmass:
            size = player.spawnmass

        # Check if can spawn from ejected mass
        index = math.floor(self.nodesEjected.length * math.random())
        eject = self.nodesEjected[index] # Randomly selected
        if (math.random() <= self.config.ejectSpawnPercent and eject and eject.boostDistance < 1):
            # Spawn from ejected mass
            pos = eject.position.clone()
            player.color = eject.color
            size = math.max(size, eject._size * 1.15)

        # Spawn player safely (do not check minions)
        cell = Entity.PlayerCell(self, player, pos, size)
        if self.willCollide(cell) and not player.isMi:
            pos = self.randomPos() # Not safe => retry
        self.addNode(cell)

        # Set initial mouse coords
        player.mouse = pos


    def willCollide(self, cell):
        notSafe = False # Safe by default
        sqSize = cell.radius
        pos = self.randomPos()
        d = cell.position.clone().sub(pos)
        if d.dist() + sqSize <= sqSize * 2:
            notSafe = True

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

    def splitCells(self, client):
        # Split cell order decided by cell age
        cellToSplit = []
        for i in range(client.cells.length):
            cellToSplit.append(client.cells[i])

        for cell in cellToSplit:
            d = client.mouse.clone().sub(cell.position)
            if d.dist() < 1:
                d.x = 1
                d.y = 0

            if cell._size < self.config.playerMinSplitSize:
                return  # cannot split

            # Get maximum cells for rec mode
            if client.rec:
                max = 200  # rec limit
            else:
                max = self.config.playerMaxCells
            if client.cells.length >= max:
                return

            # Now split player cells
            self.splitPlayerCell(client, cell, d.angle(), cell._mass * .5)


    def canEjectMass(self, client):
        if client.lastEject == None:
            # first eject
            client.lastEject = self.tickCounter
            return True

        dt = self.tickCounter - client.lastEject
        if dt < self.config.ejectCooldown:
            # reject (cooldown)
            return False

        client.lastEject = self.tickCounter
        return True

    def ejectMass(self, client):
        if not self.canEjectMass(client) or client.frozen:
            return
        for i in range(client.cells.length):
            cell = client.cells[i]

            if (cell._size < self.config.playerMinEjectSize)
                continue # Too small to eject

            d = client.mouse.clone().sub(cell.position)
            sq = d.sqDist()
            d.x = d.x / sq if sq > 1 else 1
            d.y = d.y / sq if sq > 1 else 0

            # Remove mass from parent cell first
            loss = self.config.ejectSizeLoss
            loss = cell.radius - loss * loss
            cell.setSize(math.sqrt(loss))

            # Get starting position
            pos = np.array([
                cell.position.x + d.x * cell._size,
                cell.position.y + d.y * cell._size
            ])
            angle = d.angle() + (math.random() * .6) - .3

            # Create cell and add it to node list
            if not self.config.ejectVirus:
                ejected = Entity.EjectedMass(self, None, pos, self.config.ejectSize)
            else:
                ejected = Entity.Virus(self, None, pos, self.config.ejectSize)

            ejected.color = cell.color
            ejected.setBoost(self.config.ejectVelocity, angle)
            self.addNode(ejected)



    def shootVirus(self, parent, angle):
        # Create virus and add it to node list
        pos = parent.position.clone()
        newVirus = Entity.Virus(self, None, pos, self.config.virusMinSize)
        newVirus.setBoost(self.config.virusVelocity, angle)
        self.addNode(newVirus)


    def loadFiles(self) {
    # Load config
    fs = require("fs")
    fileNameConfig = self.srcFiles + '/gameserver.ini'
    ini = require(self.srcFiles + '/modules/ini.js')
    try {
        if (!fs.existsSync(fileNameConfig)) {
            # No config
            Logger.warn("Config not found... Generating new config")
            # Create a new config
            fs.writeFileSync(fileNameConfig, ini.stringify(self.config), 'utf-8')
        } else {
            # Load the contents of the config file
            load = ini.parse(fs.readFileSync(fileNameConfig, 'utf-8'))
            # Replace all the default config's values with the loaded config's values
            for (key in load) {
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
    fileNameBadWords = self.srcFiles + '/badwords.txt'
    try {
        if (!fs.existsSync(fileNameBadWords)) {
            Logger.warn(fileNameBadWords + " not found")
        } else {
            words = fs.readFileSync(fileNameBadWords, 'utf-8')
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
    UserRoleEnum = require(self.srcFiles + '/enum/UserRoleEnum')
    fileNameUsers = self.srcFiles + '/enum/userRoles.json'
    try {
        self.userList = []
        if (!fs.existsSync(fileNameUsers)) {
            Logger.warn(fileNameUsers + " is missing.")
            return
        }
        usersJson = fs.readFileSync(fileNameUsers, 'utf-8')
        list = JSON.parse(usersJson.trim())
        for (i = 0 i < list.length) {
            item = list[i]
            if (!item.hasOwnProperty("ip") or
                !item.hasOwnProperty("password") or
                !item.hasOwnProperty("role") or
                !item.hasOwnProperty("name")) {
                list.splice(i, 1)
                continue
            }
            if (!item.password or !item.password.trim()) {
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
            item.name = (item.name or "").trim()
            i++
        }
        self.userList = list
        Logger.info(self.userList.length + " user records loaded.")
    } catch (err) {
        Logger.error(err.stack)
        Logger.error("Failed to load " + fileNameUsers + ": " + err.message)
    }

    # Load ip ban list
    fileNameIpBan = self.srcFiles + '/ipbanlist.txt'
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
