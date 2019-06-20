import gym
from gym import spaces
from gamemodes import *
from GameServer import GameServer
from players import Player

class AgarEnv(gym.Env):
    def __init__(self):
        super(AgarEnv, self).__init__()
        self.viewer = None

    def step(self, actions):
        for action, player in zip(actions, self.players):
            player.step(action)

        self.server.Update()

    def reset(self, num_players = 60, gamemode = 0):
        self.server = GameServer()
        self.gamemode = gamemode
        self.num_players = num_players
        self.server.start(self.gamemode)
        self.players = [Player(self.server) for _ in range(num_players)]
        self.server.addPlayers(self.players)
        self.viewer = None

    def render(self, playeridx, mode = 'human'):
        if self.viewer is None:
            from gym.envs.classic_control import rendering
        self.viwer = rendering.Viewer(1000, 1000)
        self.viwer.set_bounds(*self.players[playeridx].get_view_box())
        for node in self.players[playeridx].viewNodes:
            geom = rendering.make_circle(radius= node.size)
            xform = rendering.Transform()
            geom.set_color(node.color.r, node.color.g, node.color.b)
            geom.add_attr(xform)
            self.viwer.add_geom(geom)
            xform.set_translation(node.position.x, node.position.y)


        return self.viewer.render(return_rgb_array = mode=='rgb_array')
