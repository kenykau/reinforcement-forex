from config import Config
from os import path
from typing import List, Dict
import pandas as pd
import numpy as np
import talib as ta

class Broker:
    def __init__(self) -> None:
        
        # A global pointer indicating the current position of prices
        self.shift: int = 0
        
        # This is the symbol list containing all symbols in the CSV file
        self.symbols: List[str] = []
            
        # The price data for each symbol
        self.data: List[Dict] = []
        
        # Reading all price data from the csv
        self.pre_process()
        
        # Finding missing prices data for each symbol
        self.post_process()

    def pre_process(self) -> None:
        '''
        Broker.pre_process(): reading all price data from the datafile specificed in the Config class
        '''
        
        assert path.exists(Config.datafile), "data file not exists"
        df = pd.read_csv(
            Config.datafile,
            infer_datetime_format=True,
            parse_dates=[Config.fields["dt"]],
            header=0,
            index_col=Config.fields["dt"])
        
        # Mapping all fields to the standardized name 'open', 'high', 'low', 'close', 'bid', 'ask', 'volume'
        mapped_fields = {v: k for k, v in Config.fields.items()}
        df.rename(columns=mapped_fields, inplace=True)
        
        # Extracting the unique datetime index
        self.dt = df.index.unique().copy()
        
        # Extracting all symbols contained in the csv file
        self.symbols = df.symbol.unique().tolist()
        
        # Separating the prices data for each symbol and making each symbol is in sync. manner
        for symbol in self.symbols:
            self.data.append({
                "symbol": symbol,
                "df": df[df.symbol == symbol].copy(deep=True)})

            self.dt = self.dt.drop(self.dt.difference(self.data[-1]["df"].index).to_list())
        
        for d in self.data:
            d["df"] = d["df"].reindex(self.dt)
            d["df"] = d["df"].set_index(self.dt)
    
    
    
    def post_process(self) -> None:
        '''
        Broker.post_process(): find and move to the first valid price data after adding any features to the dataset
        '''
        assert len(self.data) > 0, "Data is empty"
        tmp : List[int] = []
        for data in self.data:
            idx = data['df'].apply(pd.DataFrame.first_valid_index).max()
            tmp.append(idx)
        self.shift = self.dt.get_loc(max(tmp))

    def move(self, shift: int = -1) -> None:
        '''
        Broker.move(shift: int = -1): move the global pointer to the desire position
        '''
        assert shift >=0 and shift<len(self.dt), "Invalid position"
        self.shift = shift
    
    def next(self) -> None:
        '''
        Broker.next(): move the global pointer to the next avaliable position
        '''
        assert self.shift<len(self.dt), "No more data"
        self.shift += 1
    
    def get_data(self, 
        symbol: str, 
        window_size: int = 0, 
        features: List[str] = [], 
        excludes: List[str] = []) -> pd.DataFrame:
        '''
        Broker.get_data(symbol: str, window_size: int, features: List[str], exclude: List[str]) -> pd.DataFrame: 
        Get the prices or avaliable features from the dataset. 
        symbol: str -> specify the desired symbol containing in the dataset
        window_size: int -> default value 0 means get all the data from for the symbol
        features: List(str) -> only get the desired features or price fields, e.g.:  ['open', 'close', 'rsi']
        excludes: List(str) -> return all features exclude the specified fields, e.g.: ['spread', 'bid', 'ask']
        '''
        assert symbol in self.symbols, "Invalid symbol"
        assert window_size >= 0, "Invalid window size"

        idx: int = self.symbols.index(symbol)
        assert self.symbols[idx] == self.data[idx]["symbol"], "Invalid symbol"
        tmp: pd.DataFrame = self.data[idx]["df"].copy()

        tmp = tmp[tmp.columns.difference(excludes)]
        if len(features)>0:
            tmp = tmp[features]

        if window_size == 1:
            tmp = tmp.iloc[self.shift]
        elif window_size > 1 and self.shift > 0:
            assert self.shift >= window_size, "Not enough data"
            tmp = tmp.iloc[self.shift - window_size : self.shift]
        
        return tmp
    
    def add_features(self, symbol: str, features: pd.Series, feature_name: str = "") -> None:
        '''
        Broker.add_features(symbol:str, features: pd.Series, feature_name: str): Adding features to the specify symbol
        symbol: str -> Specifies the symbol for the features
        features: pd.Series -> The feature data
        feature_name: str -> The feature name, now currently support only one column series.
        '''
        assert symbol in self.symbols, "invalid symbol"
        assert len(features) > 0, "No features to add"
        assert features.name != None or feature_name != "", "Feature name is empty"
        assert features.index.equals(self.dt), "Features must be aligned data"

        idx = self.symbols.index(symbol)

        assert features.name not in self.data[idx]["df"].columns, "Feature already exist"
        assert feature_name not in self.data[idx]["df"].columns, "Feature already exist"

        if feature_name == "":
            feature_name = features.name
        
        self.data[idx]["df"][feature_name] = features
    
