import datetime
from broker import Broker
from cfd_spread import CFDSpread
from datetime import date, time
from typing import List
import pandas as pd
import numpy as np

class Instructment:
    def __init__(self, 
        broker:Broker,
        symbol:str,
        account_currency:str='USD',
        leverage:int=100,
        lotsize:int=100000,
        asset_type:str='forex',
        point_cash_value:float=0.0,
        swap_long:float=2.5,
        swap_short:float=3.5,
        swap_day:int=2,
        comission:float=7,
        spread_ranges:List[int]=[2,7],
        spread_mode:str='random',
        fixed_spread:float=0,
    )->None:
        '''
        Instructment constructor
        broker: an instance of the Broker
        symbol: the name of symbol
        account_currency: the account currency
        leverage: the leverage of the symbol
        lotsize: the size per lot, usually 100000 for forex trading
        asset_type: forex, index or commodity
        swap_long: swap charges for long position -> +ve means charges will be debit from the account
        swap_short: swap charges for short position -> -ve means charges will be credit to the account
        swap_day: the day of week when the swap will be debit or credit for sat and sun
        commission: some ECN account will charge fixed commission for each lot when opening a position
        spread_ranges: the range for generating a random spread
        spread_mode: either fixed, included or random, fixed spread can be set by fixed_spread parameter; random spread will generate the spread randomly within the spread ranges; included should need to provide the bid and ask field in the raw data file
        fixed_spread: the fixed spread for the symbol
        '''
        self.broker:Broker = broker
        self.symbol:str = symbol
        self.account_currency:str = account_currency
        self.leverage:int = leverage
        self.lotsize:int = lotsize
        self.asset_type:str = asset_type
        self.swap_long:float = swap_long
        self.swap_short:float = swap_short
        self.swap_day:int = swap_day
        self.comission:float = comission
        self.spread_ranges:List[int] = spread_ranges
        self.spread_mode:str = spread_mode
        self.fixed_spread:float = fixed_spread
        self.pt_value:float = point_cash_value
        self.cash_pair:str = self.get_cashpair()
        self.cfd_spread:CFDSpread = None
        
        #set digits from the raw data
        tmp = broker.get_data(symbol)
        _d =tmp[['o','h','l','c']].apply(lambda x: x.astype(str).str.extract('\.(.*)', expand=False).astype(str).str.len())
        self.digits = (_d.max()).max()
        

    def get_cashpair(self)->str:
        '''
        for forex asset only, as the asset need to convert back to the account currency
        '''
        result: str = None
        if self.asset_type == 'forex':
            quote: str = self.symbol[-3:]
            if quote == self.account_currency:
                result = self.symbol
            else:
                cash_pair: str = list(filter(lambda x: quote in x and self.account_currency in x, self.broker.symbols))
                assert len(cash_pair) == 1, f'Error in getting point cash value of the underlying asset.'
                result = cash_pair[0]
        return result

    def set_spread(self)->None:
        '''
        compute the random or fixed spread for forex asset and spread mode
        '''
        assert self.asset_type=='forex', f'Error! Use set_cfd_spread for the underlying asset.'
        tmp : pd.DataFrame = self.broker.get_data(self.symbol)
        if self.spread_mode == 'random':
            spread_range:List[float] = [self.spread_ranges[0]/(10**self.digits)*1.0, self.spread_ranges[1]/(10**self.digits)*1.0]
            s = pd.Series(
                np.round(
                    np.random.uniform(
                        low=spread_range[0], 
                        high=spread_range[1], 
                        size=len(tmp.index)
                    ),
                    decimals=self.digits), 
                index=tmp.index, name='s')
            self.broker.add_feature(symbol=self.symbol, feature=s, feature_name='s')
        elif self.spread_mode == 'fixed':
            self.broker.add_feature(symbol=self.symbol, feature=pd.Series(self.fixed_spread, index=self.broker.dt, name='s'))
        else:
            assert 'a' in tmp.columns and 'b' in tmp.columns, f'Error in getting bid ask fields of the underlying asset.'
            self.broker.add_feature(symbol=self.symbol, feature=pd.Series(tmp['a']-tmp['b'], index=tmp.index, name='s'), feature_name='s')

    def set_cfd_spread(self, cfd_spread:CFDSpread)->None:
        '''
        the function is setting up the spread of time session related asset like index or commodity
        '''
        assert self.asset_type!='forex', f'Error! Use set_spread for the underlying asset.'
        assert self.cfd_spread is None, f'Error! spread has been already set.'
        assert cfd_spread is not None, f'Error! cfd_spread is None.'
        
        self.cfd_spread = cfd_spread

    def get_spread(self)->float:
        '''
        get the spread of the asset base on the current position of the shift
        '''
        if self.asset_type=='forex':
            return self.broker.get_rate(self.symbol)['s']
        else:
            assert self.cfd_spread is not None, f'Error in getting spread of the underlying asset.'
            dt: datetime = self.broker.dt[self.broker.shift]
            return self.cfd_spread.get_spread(dt)

    def get_pt_value(self, applied_price='c')->float:
        '''
        convert the point value to account currency, only open, close, bid, ask will convert back to account currency as it is not sync. for the high and low price field 
        for other type of asset, it is assumed the quote currency is the account currency. Therefore a fix point_value is return
        '''
        assert applied_price in ['o', 'c', 'b', 'a'], f'Error in getting point cash value of the underlying asset.'
        if self.asset_type=='forex':
            return self.broker.get_rate(self.cash_pair)[applied_price]
        else:
            return self.pt_value
