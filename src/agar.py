import gym
from gym import spaces

class AgarEnv(gym.Env):
  metadata = {'render.modes': ['human']}

  def __init__(self, arg):
    super(AgarEnv, self).__init__()
    # Define action and observation space
    # They must be gym.spaces objects
    # Example when using discrete actions:
    # self.action_space = spaces.Discrete(N_DISCRETE_ACTIONS)
    # # Example for using image as input:
    # self.observation_space = spaces.Box(low=0, high=255, shape=
    #                 (HEIGHT, WIDTH, N_CHANNELS), dtype=np.uint8)

  def step(self, action):
    pass

  def reset(self):
    pass

  def render(self, mode='human', close=False):
    pass