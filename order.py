from datetime import datetime, timedelta
from broker import Broker
from enum import IntEnum
from instructment import Instructment
import pandas as pd

class OP(IntEnum):
    BUY = 1
    SELL = -1
    HOLD = 0

class Order:
    #global order id
    id: int = 0
      
    def __init__(self, symbol:Instructment, op:OP, lots:float, applied_price:str='o'):
        '''
        Order constructor:
        Open a new Order for the specific symbol. Use one of price field 'o' (open price), 'c' (close price), 'b' (bid), 'a' (ask) as the applied_price
        '''
        assert op in [OP.BUY, OP.SELL], 'Invalid operation'
        Order.id += 1
        self.order_id:int = Order.id
        self.symbol:Instructment = symbol
        self.broker:Broker = self.symbol.broker
        self.lots: float = lots
        self.op : OP = op
        self.is_closed : bool = False

        self.commission: float = self.symbol.comission*self.lots
        self.margin_hold: float = 0
        self.max_fl : float = 0
        self.max_fp : float = 0
        self.pnl: float = 0
    
        rate: pd.Series = self.broker.get_rate(self.symbol.symbol)
        spread : float = self.symbol.get_spread() if self.op == OP.BUY else 0
        self.open_price: float = rate[applied_price].astype(float) + spread
        self.open_time: datetime = rate.name
        self.close_price: float = rate['c'].astype(float)
        self.close_time: datetime = self.open_time - timedelta(minutes=rate['tf'].item()) - timedelta(seconds=1)

        self.last_swap: datetime = self.open_time
        self.swap: float =0
        self.update()

    def update(self):
        '''
        Update the current order state using current shift information from symbol data
        '''
        rate: pd.Series = self.broker.get_rate(self.symbol.symbol)
        multiplier:float = self.lots*self.symbol.lotsize*self.symbol.get_pt_value()
        self.close_time = rate.name + timedelta(minutes=rate['tf'].item()) - timedelta(seconds=1)
        spread = self.symbol.get_spread() if self.op == OP.SELL else 0

        #h2o
        h2o :float = rate.h.item()-self.open_price + spread
        
        #l2o
        l2o: float = rate.l.item()-self.open_price + spread
        
        #c2o
        c2o: float = rate.c.item()-self.open_price + spread

        self.close_price = rate.c.item()+ spread

        if self.close_time - self.last_swap > timedelta(days=1):
            factor:float = 3 if self.close_time.day_of_week == self.symbol.swap_day else 1
            self.last_swap = self.close_time
            self.swap += (self.symbol.swap_long if self.op==OP.BUY else self.symbol.swap_short)*factor
        
        charges: float = self.commission + self.swap
        
        self.pnl  = round(c2o*multiplier*self.op.value - charges,2)

        self.margin_hold = self.close_price*multiplier/self.symbol.leverage

        fl: float = round((l2o if self.op == OP.BUY else h2o)*multiplier,2)
        fp: float = round((h2o if self.op == OP.BUY else l2o)*multiplier,2)
        self.max_fl = min(self.max_fl, fl)
        self.max_fp = max(self.max_fp, fp)
        
    def close(self):
        '''
        Close Order
        '''
        self.update()
        self.is_closed = True
 
