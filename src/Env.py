# Author: Boyuan Chen
# Berkeley Artifical Intelligence Research

# The project is largely based on m-byte918's javascript implementation of the game with a lot of bug fixes and optimization for python
# Original Ogar-Edited project https://github.com/m-byte918/MultiOgar-Edited


import gym
from src.GameServer import GameServer
from src.modules import AgarObservation
from src.players import Player, Bot
import numpy as np
import src.rendering as rendering


class AgarEnv(gym.Env):
    def __init__(self, num_agents = 1, num_bots = 9, gamemode = 0):
        super(AgarEnv, self).__init__()
        self.viewer = None
        self.num_players = num_agents + num_bots
        self.num_agents = num_agents
        self.num_bots = num_bots
        self.gamemode = gamemode

        # factors for reward
        self.mass_reward_eps = 0.01  # make the max mass reward < 100
        self.kill_reward_eps = 10
        self.killed_reward_eps = 10

    def step(self, actions):
        for action, agent in zip(actions, self.agents):
            agent.step(action)
        for bot in self.bots:
            bot.step()

        self.server.Update()
        observations = AgarObservation([self.parse_obs(agent) for agent in self.agents])
        rewards = np.array([self.parse_reward(agent) for agent in self.agents])
        done = np.array([False for agent in self.agents])
        info = {}
        return observations, rewards, done, info

    def reset(self):
        self.server = GameServer()
        self.server.start(self.gamemode)
        self.agents = [Player(self.server) for _ in range(self.num_agents)]
        self.bots = [Bot(self.server) for _ in range(self.num_bots)]
        self.players = self.agents + self.bots
        self.server.addPlayers(self.players)
        self.viewer = None
        self.server.Update()
        observations = AgarObservation([self.parse_obs(agent) for agent in self.agents])
        return observations

    def parse_obs(self, player):
        obs = [{}, [], [], []]
        for cell in player.viewNodes:
            t, feature = self.cell_obs(cell, player)
            if t != 0:  # if type is not player, directly append
                obs[t].append(feature)
            else:
                owner = cell.owner
                if owner in obs[0]:
                    obs[0][owner].append(feature)
                else:
                    obs[0][owner] = [feature]

        playercells = [np.concatenate(v, 0) for k, v in obs[0].items()] # a list of np array. each array represents the state of all cells owned by a player
        foodcells = np.concatenate(obs[1], 0) if obs[1] else None # np array, each row represents a cell
        viruscells = np.concatenate(obs[2], 0) if obs[2] else None
        ejectedcells = np.concatenate(obs[3], 0) if obs[3] else None

        return {'player': playercells, 'food': foodcells, 'virus': viruscells, 'ejected': ejectedcells}

    def cell_obs(self, cell, player):
        if cell.cellType == 0:
            # player features
            boost_x = (cell.boostDistance * cell.boostDirection.x) / self.server.config.splitVelocity  # [-1, 1]
            boost_y = cell.boostDistance * cell.boostDirection.y / self.server.config.splitVelocity  # [-1, 1]
            radius = cell.radius / 400  # need to think about mean though [0, infinite...]  # fixme
            log_radius = np.log(cell.radius / 100)  # need to think about mean though   # fixme
            position_x = (cell.position.x - self.server.config.borderWidth / 2) / self.server.config.borderWidth * 2  # [-1, 1]
            position_y = (cell.position.y - self.server.config.borderHeight / 2) / self.server.config.borderHeight * 2  # [-1, 1]
            relative_position_x = (cell.position.x - player.centerPos.x - self.server.config.serverViewBaseX / 2) / self.server.config.serverViewBaseX * 2  # [-1, 1]
            relative_position_y = (cell.position.y - player.centerPos.y - self.server.config.serverViewBaseY / 2) / self.server.config.serverViewBaseY * 2  # [-1, 1]
            canRemerge = onehot(cell.canRemerge, ndim=2)  # len 2 onehot 0 or 1
            ismycell = onehot(cell.owner == player, ndim=2)  # len 2 onehot 0 or 1
            features_player = np.array([[boost_x, boost_y, radius, log_radius, position_x, position_y, relative_position_x, relative_position_y]])
            features_player = np.concatenate([features_player, canRemerge, ismycell], axis=1)
            return cell.cellType, features_player

        elif cell.cellType == 1:
            # food features
            radius = (cell.radius - (self.server.config.foodMaxRadius + self.server.config.foodMinRadius) / 2) / (self.server.config.foodMaxRadius - self.server.config.foodMinRadius) * 2  # fixme
            log_radius = np.log(cell.radius / ((self.server.config.foodMaxRadius + self.server.config.foodMinRadius) / 2))  # fixme
            position_x = (cell.position.x - self.server.config.borderWidth / 2) / self.server.config.borderWidth * 2  # [-1, 1]
            position_y = (cell.position.y - self.server.config.borderHeight / 2) / self.server.config.borderHeight * 2  # [-1, 1]
            relative_position_x = (cell.position.x - player.centerPos.x - self.server.config.serverViewBaseX / 2) / self.server.config.serverViewBaseX * 2  # [-1, 1]
            relative_position_y = (cell.position.y - player.centerPos.y - self.server.config.serverViewBaseY / 2) / self.server.config.serverViewBaseY * 2  # [-1, 1]
            features_food = np.array([[radius, log_radius, position_x, position_y, relative_position_x, relative_position_y]])
            return cell.cellType, features_food

        elif cell.cellType == 2:
            # virus features
            boost_x = (cell.boostDistance * cell.boostDirection.x) / self.server.config.splitVelocity  # [-1, 1]
            boost_y = cell.boostDistance * cell.boostDirection.y / self.server.config.splitVelocity  # [-1, 1]
            radius = (cell.radius - (self.server.config.virusMaxRadius + self.server.config.virusMinRadius) / 2) / (self.server.config.virusMaxRadius - self.server.config.virusMinRadius) * 2  # fixme
            log_radius = np.log(cell.radius / ((self.server.config.virusMaxRadius + self.server.config.virusMinRadius) / 2))  # fixme
            position_x = (cell.position.x - self.server.config.borderWidth / 2) / self.server.config.borderWidth * 2  # [-1, 1]
            position_y = (cell.position.y - self.server.config.borderHeight / 2) / self.server.config.borderHeight * 2  # [-1, 1]
            relative_position_x = (cell.position.x - player.centerPos.x - self.server.config.serverViewBaseX / 2) / self.server.config.serverViewBaseX * 2  # [-1, 1]
            relative_position_y = (cell.position.y - player.centerPos.y - self.server.config.serverViewBaseY / 2) / self.server.config.serverViewBaseY * 2  # [-1, 1]
            features_virus = np.array([[boost_x, boost_y, radius, log_radius, position_x, position_y, relative_position_x, relative_position_y]])
            return cell.cellType, features_virus

        elif cell.cellType == 3:
            # ejected mass features
            boost_x = (cell.boostDistance * cell.boostDirection.x) / self.server.config.splitVelocity  # [-1, 1]
            boost_y = cell.boostDistance * cell.boostDirection.y / self.server.config.splitVelocity  # [-1, 1]
            position_x = (cell.position.x - self.server.config.borderWidth / 2) / self.server.config.borderWidth * 2  # [-1, 1]
            position_y = (cell.position.y - self.server.config.borderHeight / 2) / self.server.config.borderHeight * 2  # [-1, 1]
            relative_position_x = (cell.position.x - player.centerPos.x - self.server.config.serverViewBaseX / 2) / self.server.config.serverViewBaseX * 2  # [-1, 1]
            relative_position_y = (cell.position.y - player.centerPos.y - self.server.config.serverViewBaseY / 2) / self.server.config.serverViewBaseY * 2  # [-1, 1]
            features_food = np.array([[boost_x, boost_y, position_x, position_y, relative_position_x, relative_position_y]])
            return cell.cellType, features_food

    def parse_reward(self, player):
        mass_reward, kill_reward, killed_reward = self.calc_reward(player)
        # reward for being --- big, not dead, eating part of others, killing all of others, not be eaten by someone
        reward = mass_reward * self.mass_reward_eps + \
                 kill_reward * self.kill_reward_eps + \
                 killed_reward * self.killed_reward_eps
        return reward

    def calc_reward(self, player):
        mass_reward = sum([c.mass for c in player.cells])
        kill_reward = player.killreward
        killedreward = player.killedreward
        return mass_reward, kill_reward, killedreward

    def render(self, playeridx, mode = 'human'):
        # time.sleep(0.001)
        if self.viewer is None:
            self.viewer = rendering.Viewer(self.server.config.serverViewBaseX, self.server.config.serverViewBaseY)
            self.render_border()
            self.render_grid()

        bound = self.players[playeridx].get_view_box()
        self.viewer.set_bounds(*bound)
        # self.viewer.set_bounds(-7000, 7000, -7000, 7000)

        self.geoms_to_render = []
        # self.viewNodes = sorted(self.viewNodes, key=lambda x: x.size)
        for node in self.players[playeridx].viewNodes:
            self.add_cell_geom(node)

        self.geoms_to_render = sorted(self.geoms_to_render, key=lambda x: x.order)
        for geom in self.geoms_to_render:
            self.viewer.add_onetime(geom)

        return self.viewer.render(return_rgb_array=mode == 'rgb_array')

    def render_border(self):
        map_left = - self.server.config.borderWidth / 2
        map_right = self.server.config.borderWidth / 2
        map_top = - self.server.config.borderHeight / 2
        map_bottom = self.server.config.borderHeight / 2
        line_top = rendering.Line((map_left, map_top), (map_right, map_top))
        line_top.set_color(0, 0, 0)
        self.viewer.add_geom(line_top)
        line_bottom = rendering.Line((map_left, map_bottom), (map_right, map_bottom))
        line_bottom.set_color(0, 0, 0)
        self.viewer.add_geom(line_bottom)
        line_left = rendering.Line((map_left, map_top), (map_left, map_bottom))
        line_left.set_color(0, 0, 0)
        self.viewer.add_geom(line_left)
        map_right = rendering.Line((map_right, map_top), (map_right, map_bottom))
        map_right.set_color(0, 0, 0)
        self.viewer.add_geom(map_right)

    def render_grid(self):
        map_left = - self.server.config.borderWidth / 2
        map_right = self.server.config.borderWidth / 2
        map_top = - self.server.config.borderHeight / 2
        map_bottom = self.server.config.borderHeight / 2
        for i in range(0, int(map_right), 100):
            line = rendering.Line((i, map_top), (i, map_bottom))
            line.set_color(0.8, 0.8, 0.8)
            self.viewer.add_geom(line)
            line = rendering.Line((-i, map_top), (-i, map_bottom))
            line.set_color(0.8, 0.8, 0.8)
            self.viewer.add_geom(line)

        for i in range(0, int(map_bottom), 100):
            line = rendering.Line((map_left, i), (map_right, i))
            line.set_color(0.8, 0.8, 0.8)
            self.viewer.add_geom(line)
            line = rendering.Line((map_left, -i), (map_right, -i))
            line.set_color(0.8, 0.8, 0.8)
            self.viewer.add_geom(line)

    def add_cell_geom(self, cell):
        if cell.cellType == 0:
            cellwall = rendering.make_circle(radius=cell.radius)
            cellwall.set_color(cell.color.r * 0.75 / 255.0, cell.color.g * 0.75 / 255.0 , cell.color.b * 0.75 / 255.0)
            xform = rendering.Transform()
            cellwall.add_attr(xform)
            xform.set_translation(cell.position.x, cell.position.y)
            cellwall.order = cell.radius
            self.geoms_to_render.append(cellwall)

            geom = rendering.make_circle(radius=cell.radius - max(10, cell.radius * 0.1))
            geom.set_color(cell.color.r / 255.0, cell.color.g / 255.0, cell.color.b / 255.0)
            xform = rendering.Transform()
            geom.add_attr(xform)
            xform.set_translation(cell.position.x, cell.position.y)
            if cell.owner.maxradius < self.server.config.virusMinRadius:
                geom.order = cell.owner.maxradius + 0.0001
            elif cell.radius < self.server.config.virusMinRadius:
                geom.order = self.server.config.virusMinRadius - 0.0001
            else: #cell.owner.maxradius < self.server.config.virusMaxRadius:
                geom.order = cell.owner.maxradius + 0.0001

            self.geoms_to_render.append(geom)

            # self.viewer.add_onetime(geom)
        elif cell.cellType == 2:
            geom = rendering.make_circle(radius=cell.radius)
            geom.set_color(cell.color.r / 255.0, cell.color.g / 255.0, cell.color.b / 255.0, 0.6)
            xform = rendering.Transform()
            geom.add_attr(xform)
            xform.set_translation(cell.position.x, cell.position.y)
            geom.order = cell.radius
            self.geoms_to_render.append(geom)

        else:
            geom = rendering.make_circle(radius=cell.radius)
            geom.set_color(cell.color.r / 255.0, cell.color.g / 255.0, cell.color.b / 255.0)
            xform = rendering.Transform()
            geom.add_attr(xform)
            xform.set_translation(cell.position.x, cell.position.y)
            geom.order = cell.radius
            self.geoms_to_render.append(geom)


    def close(self):
        if self.viewer is not None:
            self.viewer.close()
            self.viewer = None


def onehot(d, ndim):
    v = np.zeros((1, ndim))
    v[0, d] = 1
    return v
