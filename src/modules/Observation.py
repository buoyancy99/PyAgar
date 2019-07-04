import torch

class AgarObservation():
    def __init__(self, obs):
        self.obs = obs
        self.tensorobs = None

    def tensor_obs(self, device):
        parsed_env_obs = []
        for player_obs in self.obs:
            playercells = [torch.from_numpy(player).to(device) for player in playercells]
            foodcells = torch.from_numpy(player_obs['food']).to(device)
            viruscells = torch.from_numpy(player_obs['virus']).to(device)
            ejectedcells = torch.from_numpy(player_obs['ejected']).to(device)
            parsed_env_obs.append({'player': playercells, 'food': foodcells, 'virus': viruscells, 'ejected': ejectedcells})

        self.tensorobs = parsed_env_obs

        return self
