import torch

class AgarObservation():
    def __init__(self, obs):
        self.obs = obs
        self.tensor_obs = None

    def to(self, device):
        parsed_env_obs = []
        for player_obs in self.obs:
            playercells = [torch.from_numpy(player).to(device) for player in player_obs['player']] if player_obs['player'] else None
            foodcells = torch.from_numpy(player_obs['food']).to(device) if player_obs['food'] else None
            viruscells = torch.from_numpy(player_obs['virus']).to(device) if player_obs['virus'] else None
            ejectedcells = torch.from_numpy(player_obs['ejected']).to(device) if player_obs['ejected'] else None
            parsed_env_obs.append({'player': playercells, 'food': foodcells, 'virus': viruscells, 'ejected': ejectedcells})

        self.tensor_obs = parsed_env_obs

        return self
