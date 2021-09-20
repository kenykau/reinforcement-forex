from broker import Broker
from fxenv import FxEnv
from instrument import Symbol
from stable_baselines3.a2c import A2C
from stable_baselines3.dqn import DQN
from stable_baselines3.ppo import PPO
from stable_baselines3.common.vec_env.dummy_vec_env import DummyVecEnv
from stable_baselines3.common import env_checker as ec
broker: Broker = Broker()
eurusd: Symbol = Symbol(broker, "EURUSD")
fx: FxEnv = FxEnv(broker=broker, symbol=eurusd, window_size=4)

ec.check_env(fx)
env_creator = lambda: fx
env = DummyVecEnv(env_fns=[env_creator])
model = A2C("MlpPolicy", env)
model.learn(total_timesteps=10000)
model.save('eurusd_a2c')
