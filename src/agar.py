import gym
from gym import spaces
from gamemodes import *
from GameServer import GameServer
from players import Player
import time
from gym.envs.classic_control import rendering


class AgarEnv(gym.Env):
    def __init__(self):
        super(AgarEnv, self).__init__()
        self.viewer = None

    def step(self, actions):
        for action, player in zip(actions, self.players):
            player.step(action)

        self.server.Update()

    def reset(self, num_players = 20, gamemode = 0):
        self.server = GameServer()
        self.gamemode = gamemode
        self.num_players = num_players
        self.server.start(self.gamemode)
        self.players = [Player(self.server) for _ in range(num_players)]
        self.server.addPlayers(self.players)
        self.viewer = None

    def render(self, playeridx, mode = 'human'):
        print('==================================================', self.players[playeridx].pID)

        # time.sleep(0.3)
        if self.viewer is None:
            self.viewer = rendering.Viewer(self.server.config.serverViewBaseX, self.server.config.serverViewBaseY)
        else:
            self.viewer.geoms = []
        self.render_border()
        bound = self.players[playeridx].get_view_box()
        self.viewer.set_bounds(*bound)

        for node in self.players[playeridx].viewNodes:
            geom = rendering.make_circle(radius= node.radius)
            geom.set_color(node.color.r / 255.0, node.color.g / 255.0, node.color.b / 255.0)
            xform = rendering.Transform()

            geom.add_attr(xform)
            xform.set_translation(node.position.x, node.position.y)
            self.viewer.add_geom(geom)

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


    def close(self):
        if self.viewer is not None:
            self.viewer.close()
            self.viewer = None
