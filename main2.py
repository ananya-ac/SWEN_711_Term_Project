from utils.GymEnv import RideGrid
import numpy as np
from stable_baselines3 import TD3,PPO, DDPG
from stable_baselines3.common.noise import NormalActionNoise
from stable_baselines3.common.logger import configure, CSVOutputFormat



if __name__ == '__main__':
    
    env = RideGrid('data/saved_trips.pkl')
    n_actions = env.action_space.shape[-1]
    action_noise = NormalActionNoise(mean=np.zeros(n_actions), sigma=0.1 * np.ones(n_actions))
    #model = DDPG(policy = "MultiInputPolicy",action_noise=action_noise, env = env,learning_rate=5e-4, verbose=1)     
    model = TD3(policy = "MultiInputPolicy",learning_starts=20000, env = env, action_noise=action_noise, learning_rate=5e-4, verbose=1)     
    model.learn(total_timesteps=100000)
        
    