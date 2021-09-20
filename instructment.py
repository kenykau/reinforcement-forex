from os import close, name
from broker import Broker
from config import AssetType, Config, SpreadMode
from sessional_spread import SessionalSpread
from typing import List, Dict
from datetime import timedelta

import pandas as pd
import numpy as np
import talib as ta
class Symbol:
    def __init__(self,
        broker: Broker,
        symbol: str) -> None:
        '''
        broker: Broker -> Specifies a broker for the symbol
        symbol: str -> Symbol name
        '''
        assert symbol in broker.symbols, "Invalid symbol"
        assert len(list(filter(lambda x: x["name"] == symbol, Config.symbols))) == 1, "Symbol details not set in config file"
        
        self.broker = broker
        
        # getting the symbol specification from the Config class
        self.info = list(filter(lambda x: x["name"] == symbol, Config.symbols))[0]
        
        # getting the cash currency pair
        self.cash_pair: str = self.get_cash_pair()

        # initialize the sessional_spread to None
        self.sessional_spread: SessionalSpread = None
        
        '''
        The following are example to illustrate adding the features for the symbol
        '''
        # self.add_ema()
        # self.add_band()
        # self.add_roc()
        # self.add_atr()

    def get_cash_pair(self) -> str:
        '''
        Instructment.get_cash_pair(): This is to get the account currency and quote currency pair, so that which is needed to convert back and forth of the account currency       
        '''
        
        result: str = None
        if self.info["asset_type"] == AssetType.FOREX:
            if self.info["quote"] != Config.account["currency"]:
                tmp: List[str] = list(filter(lambda x: self.info["quote"] in x and Config.account["currency"] in x, self.broker.symbols))
                assert len(tmp) == 1, "None or more than 1 of fx pair is found"
                result = tmp[0]
            else:
                result = self.info["name"]
        else:
            result = Config.account["currency"]
        return result

    def get_rate(self) -> Dict:
        '''
        Instructment.get_rate(): Getting the price rates for the symbol, those rates can be used in trading simulation
        '''
        tmp = self.broker.get_data(
            symbol = self.info["name"],
            window_size = 1,
            features = ["tf", "open", "high", "low", "close", "vol", "bid", "ask", "spread"])
        result: Dict = dict(zip(tmp.index, tmp.tolist()))

        result["dt"] = tmp.name
        result["dt_close"] = result["dt"] + timedelta(minutes = result["tf"]) - timedelta(milliseconds=1)
        result.pop("tf")
        return result

    def get_pt_value(self, applied_price: str = "close") -> float:
        '''
        Instructment.get_pt_value(applied_price:str): 
        The point value of the symbol respectively to the account currency
        applied_price:str -> Either of 'open', 'high', 'low', 'close' symbol rate's respective account currency will need to be return 
        '''
        val: float = 1
        if self.info["asset_type"] == AssetType.FOREX:
            if self.info["quote"] != Config.account["currency"]:
                tmp = self.broker.get_data(self.cash_pair, 1, [applied_price])
                val = 1/tmp[applied_price]
        else:
            assert self.info["fixed_pt_value"] > 0, "Invalid fixed point value for the underlying asset."
            val = self.info["fixed_pt_value"]
        
        assert val > 0, "Invalid point value for the underlying asset."
        return val

    def set_spread(self, session_spread: SessionalSpread = None) -> None:
        '''
        Instructment.set_spread(session_spread: SessionalSpread) ->
        Setting the spread of the underlying instructment according the spread method
        '''
        
        if self.info["spread_mode"] == SpreadMode.RANDOM:
            s = np.random.uniform(
                low = self.info["min_spread"]/(10**self.info["digits"]),
                high = self.info["max_spread"]/(10**self.info["digits"]),
                size = len(self.broker.dt)
            )
            s = np.round(s, self.info["digits"])
            spread : pd.Series = pd.Series(s, name = "spread", index = self.broker.dt)
            self.broker.add_features(self.info["name"], spread)

        if self.info["spread_mode"] in [SpreadMode.FIXED, SpreadMode.IGNORE]:
            s = np.zeros(len(self.broker.dt))
            if self.info["spread_mode"] == SpreadMode.FIXED:
                s += self.info["fixed_spread"]
            spread : pd.Series = pd.Series(s, name = "spread", index = self.broker.dt)
            self.broker.add_features(self.info["name"], spread)
            
        if self.info["spread_mode"] == SpreadMode.SESSIONAL:
            assert session_spread != None, "Sessional Spread is not provided"
            self.sessional_spread = session_spread

        if self.info["spread_mode"] == SpreadMode.BIDASK:
            tmp: pd.DataFrame = self.broker.get_data(
                symbol = self.info["name"],
                window_size = 0,
                features = ["bid", "ask"]
            )
            sprad = tmp.ask - tmp.bid
            self.broker.add_features(self.info["name"], sprad, "spread")

    def get_spread(self) -> float:
        '''
        Instructment.get_spread(): getting the current spread
        '''
        if self.info["spread_mode"] == SpreadMode.SESSIONAL:
            assert self.sessional_spread != None, "Sessional spread is not set"
            return self.sessional_spread.get_spread(self.broker.dt[self.broker.shift])

        if self.info["spread_mode"] in [SpreadMode.FIXED, SpreadMode.BIDASK, SpreadMode.RANDOM]:
            if self.info["name"] in self.broker.symbols:
                tmp = self.broker.get_data(self.info["name"], 1, ["spread"])
                return tmp.spread

        if self.info["spread_mode"] == SpreadMode.IGNORE:
            return 0.0

    def add_sto(self) -> None:
        '''
        Instructment.add_sto(): This is the demo of adding stochastic oscillator to the symbol using the talib
        '''
        rates: pd.DataFrame = self.broker.get_data(symbol = self.info["name"], window_size = 0, features = ["open", "high", "low", "close"])
        slowk, slowd = ta.STOCH(high=rates.high,
                                low=rates.low,
                                fastk_period=5,
                                close=rates.close,
                                slowk_period=3,
                                slowk_matype=0,
                                slowd_period=3,
                                slowd_matype=0)
        self.broker.add_features(symbol = self.info["name"], features = slowk, feature_name = "sto_fast")
        self.broker.add_features(symbol = self.info["name"], features = slowd, feature_name = "sto_slow")

    def add_ema(self) -> None:
        '''
        Instructment.add_ema(): demo of adding ema to the symbol using the talib
        '''
        rates: pd.DataFrame = self.broker.get_data(symbol = self.info["name"], window_size = 0, features = ["open", "high", "low", "close"])
        ema = ta.EMA(rates.close, timeperiod=5)
        ema_code = rates.close - ema
        ema_code = ema_code.apply(lambda x: 1 if x>0 else 0)
        self.broker.add_features(symbol = self.info["name"], features = ema_code, feature_name = "ema")

    def add_roc(self) -> None:
        '''
        Instructment.add_roc(): adding the Rate Of Change of the symbol using the talib
        '''
        rates: pd.DataFrame = self.broker.get_data(symbol = self.info["name"], window_size = 0, features = ["open", "high", "low", "close"])
        roc = ta.ROC(rates.close, timeperiod=5)
        self.broker.add_features(symbol = self.info["name"], features = roc, feature_name = "roc")

    def add_band(self) -> None:
        '''
        Instructment.add_band(): adding the Bollinger Band to the symbol using the talib
        '''
        rates: pd.DataFrame = self.broker.get_data(symbol = self.info["name"], window_size = 0, features = ["open", "high", "low", "close"])
        upper, middle, lower = ta.BBANDS(rates.close, timeperiod=5, nbdevup=2, nbdevdn=2, matype=0)
        self.broker.add_features(symbol = self.info["name"], features = upper, feature_name = "bb_upper")
        self.broker.add_features(symbol = self.info["name"], features = middle, feature_name = "bb_middle")
        self.broker.add_features(symbol = self.info["name"], features = lower, feature_name = "bb_lower")
    
    def add_atr(self) -> None:
        '''
        Instructment.add_atr(): adding the Actual True Range indicator to the symbol using talib
        '''
        rates: pd.DataFrame = self.broker.get_data(symbol = self.info["name"], window_size = 0, features = ["open", "high", "low", "close"])
        atr = ta.ATR(high=rates.high,
                     low=rates.low,
                     close=rates.close,
                     timeperiod=5)
        self.broker.add_features(symbol = self.info["name"], features = atr, feature_name = "atr")
