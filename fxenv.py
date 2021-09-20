from account import Account
from broker import Broker
from config import Config, Op
from gym.spaces.discrete import Discrete
from instrument import Symbol
from typing import Dict, List, Tuple
from gym import spaces
import gym
import numpy as np
import pandas as pd
import talib as ta

from order import Order

class FxEnv(gym.Env):
    metadata = {'reder.mode': ['human']}

    def __init__(self, broker: Broker, symbol: Symbol, window_size: int = 12) -> None:
        self.cycle: int = 0
        self.broker: Broker = broker
        self.symbol: Symbol = symbol
        
        self.window_size: int = window_size
        self.symbol.set_spread()
        self.broker.post_process()
        self.broker.move(window_size*3+1)
        
        self.account: Account = Account(broker = broker, symbol = symbol)

        tmp: int = int((symbol.info["max_lot"]-symbol.info["min_lot"])/symbol.info["lot_step"])
        self.action_space: spaces.Discrete = spaces.Discrete(3)
        self.observation_space: spaces.Box = spaces.Box(
            low=-np.inf,
            high=np.inf,
            shape=self.get_observation().shape)

        self.done: bool = False
        self.total_rewards: float = 0
        self.reset()
        

    def is_done(self) -> bool:
        result: bool = False
        
        if self.broker.shift >= len(self.broker.dt) -1:
            result = True
        
        curr: pd.Series = self.account.df.iloc[self.broker.shift]
        if curr.equity < curr.balance * Config.account["stop_out"]:
            result = True
        
        if curr.equity < Config.account["balance"] * 0.5:
            result = True

        self.done = result
        return result

    def get_observation(self) -> np.ndarray:
        price_features = self.broker.get_data(
            symbol = self.symbol.info["name"], 
            window_size = self.window_size, 
            #features = Config.env["obs_price_features"], 
            excludes = Config.env["obs_price_exclude"])
            
        account_features = self.account.get_features(Config.env["obs_account_features"])
        result = price_features.to_numpy().flatten()
        #result = np.append(result, account_features.to_numpy())
        #print(self.broker.shift)
        #print(result.shape)
        
        return result
        
    def step(self, action):
        
        if not self.is_done():
            self.broker.next()
            #op: Op = Op(action[0])
            op = Op(action)
            lots: float = 0.1
            self.account.action(op, lots)
        else:
            self.account.action(Op.CLOSEALL)
        obs = self.get_observation()
        reward = (self.account.df.iloc[self.broker.shift]["equity"] - self.account.df.iloc[self.broker.shift-1]["equity"])/self.account.df.iloc[self.broker.shift]['equity']
        #reward: float = self.compute_rewards()
        self.total_rewards += reward

        
        if self.broker.shift%500 == 0:
            self.render()
        #self.render()
        return obs, reward, self.done, {}

    def reset(self):
        print(f"Cycle: {self.cycle}. Total Rewards: {self.total_rewards}")
        
        
        self.total_rewards = 0
        self.done = False
        self.broker.move(self.window_size*3+1)
        self.account.save(self.symbol.info["name"], self.cycle)
        self.account = Account(broker = self.broker, symbol = self.symbol)
        Order.id = 0
        self.cycle += 1
        
        return self.get_observation()
        
    def render(self) -> None:
        acc = self.account.info()
        print(acc)
        #self.compute_rewards()

    def close(self) -> None:
        return super().close()

    def compute_rewards(self) -> float:
        tmp: List[Order] = self.account.history+self.account.orders
        pctChange: List[float] = [(b.pnl-a.pnl)/a.pnl for a, b in list(zip(tmp[::1], tmp[1::1]))]
        r = np.array([x+1 for x in pctChange[-self.window_size:]]).cumprod() - 1
        return 0 if len(r) < 1 else r[-1]
