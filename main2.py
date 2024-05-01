from utils.GymEnv import RideGrid
import numpy as np
from stable_baselines3 import TD3
from stable_baselines3.common.noise import NormalActionNoise

# The noise objects for TD3

if __name__ == '__main__':
    rewards = []
    for i in range(100):
        env = RideGrid('data/saved_trips.pkl')
        # env.reset()
        n_actions = env.action_space.shape[-1]
        action_noise = NormalActionNoise(mean=np.zeros(n_actions), sigma=0.1 * np.ones(n_actions))

        model = TD3("MultiInputPolicy", env, action_noise=action_noise, verbose=1)     

        model.learn(total_timesteps=1000, log_interval=10)
        
        # while not env.done:
        #     env.step(np.array([1,1,1,1]))
