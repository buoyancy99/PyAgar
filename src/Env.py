import gym
from gym import spaces
from gamemodes import *
from GameServer import GameServer
from players import Player, Bot
import time
import rendering


class AgarEnv(gym.Env):
    def __init__(self, num_agents, num_bots, gamemode = 0):
        super(AgarEnv, self).__init__()
        self.viewer = None
        self.num_players = num_agents + num_bots
        self.num_agents = num_agents
        self.num_bots = num_bots
        self.gamemode = gamemode

    def step(self, actions):
        for action, agent in zip(actions, self.agents):
            agent.step(action)
        for bot in self.bots:
            bot.step()

        self.server.Update()
        observations = [agent.viewNodes for agent in self.agents]
        rewards = []
        done = False
        return observations, rewards, done

    def reset(self):
        self.server = GameServer()
        self.server.start(self.gamemode)
        self.agents = [Player(self.server) for _ in range(self.num_agents)]
        self.bots = [Bot(self.server) for _ in range(self.num_bots)]
        self.players = self.agents + self.bots
        self.server.addPlayers(self.players)
        self.viewer = None
        self.server.Update()
        observations = [agent.viewNodes for agent in self.agents]
        return observations

    def render(self, playeridx, mode = 'human'):
        # time.sleep(0.3)
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
