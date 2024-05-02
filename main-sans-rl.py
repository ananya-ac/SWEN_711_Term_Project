from utils.GymEnv import RideGrid
import numpy as np
from stable_baselines3 import TD3
from stable_baselines3.common.noise import NormalActionNoise
import pandas as pd

# The noise objects for TD3

if __name__ == '__main__':
    rewards = []
    for i in range(100):
        env = RideGrid('data/saved_trips.pkl')
        env.reset()
        # n_actions = env.action_space.shape[-1]
        # action_noise = NormalActionNoise(mean=np.zeros(n_actions), sigma=0.1 * np.ones(n_actions))

        # model = TD3("MultiInputPolicy", env, action_noise=action_noise, verbose=1)     

        # model.learn(total_timesteps=1000, log_interval=10)
        act = np.array([1,1,1,1])
        i = 0
        while not env.done:
            # if i > 0 and i%5 == 0:
            #     act = np.random.uniform(low=0.0, high=1.0, size=(4,))
            env.step(act)

        rewards.append(env.epi_reward)
    
    df = pd.DataFrame({'NoAgentReward':rewards})
    df.to_csv('NoAgentTrajectoryLogs.csv')