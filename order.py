from datetime import datetime, timedelta

from broker import Broker
from config import AssetType, Config, Op
from instrument import Symbol
from typing import Union, List, Dict

class Order:
    # A global Id for each order
    id:int = 0
    def __init__(self, symbol: Symbol, action: Op, lots: float, applied_price: str = "open") -> None:
        assert action in [Op.LONG, Op.SHORT], "Invalid action"
        assert isinstance(symbol, Symbol), "Invalid symbol object"
        assert applied_price in ['open', 'close', 'bid', 'ask'], "Invalid applied price for opening order"
        assert lots >= symbol.info["min_lot"], f"Invalid lots {lots}"
        self.id: int = -1
        self.symbol: Symbol = symbol
        self.lots: float = lots
        self.position: Op = action

        rates: Dict = self.symbol.get_rate()
        
        self.open_time: datetime = rates["dt"]
        spread : float = 0 if self.position == Op.SHORT else self.symbol.get_spread()
        
        self.open_price: float = rates["open"] + spread
        self.commission: float = self.symbol.info["commission"] * self.lots
        self.last_swap: datetime = rates["dt"]
        self.swap: float = 0
        self.margin: float = self.comp_margin(applied_price)
        self.pnl: float = 0
        self.max_fl: float = 0
        self.max_fp: float = 0

        self.closed: bool = False

    def update(self) -> None:
        assert self.id >= 0, "Order open operation not complete"
        
        rate: Dict = self.symbol.get_rate()
        spread: float = 0 if self.position == Op.LONG else self.symbol.get_spread()
        sign: int = 1 if self.position == Op.LONG else -1
        multiplier: float = sign * self.lots * self.symbol.info["lot_size"] * self.symbol.get_pt_value() 

        h2o: float = rate["high"] + spread - self.open_price
        l2o: float = rate["low"] + spread - self.open_price
        c2o: float = rate["close"] + spread - self.open_price

        self.close_time = rate["dt_close"]
        self.close_price = rate["close"] + spread
        self.comp_swap()
        fl: float = h2o if self.position == Op.SHORT else l2o
        fp: float = h2o if self.position == Op.LONG else l2o
 

        self.max_fl = min(self.max_fl, round(fl * multiplier - self.commission - self.swap, 2))
        self.max_fp = max(self.max_fp, round(fp * multiplier - self.commission - self.swap, 2))
        self.pnl = round(c2o * multiplier - self.commission - self.swap, 2)
      
    def comp_margin(self, applied_price: str = "open") -> float:
        result: float = 0.0
        multiplier: float = self.lots * self.symbol.info["lot_size"]/self.symbol.info["leverage"]
        if self.symbol.info["asset_type"] != AssetType.FOREX:
            result = self.open_price * multiplier * self.symbol.info["fixed_pt_value"]
        else:
            if self.symbol.info["base"] == Config.account["currency"]:
                result = multiplier
            else:
                rates = self.symbol.broker.get_data(symbol = self.symbol.cash_pair, window_size=1, features=[applied_price])
                result = multiplier/rates.open
        assert result > 0, "Invalid margin"
        return round(result, 2)

    def comp_swap(self) -> None:
        rates: Dict = self.symbol.get_rate()
        if rates["dt_close"]  - self.last_swap >= timedelta(days=1):
            multiplier: int = 3 if rates["dt_close"].weekday() == self.symbol.info["swap_day"] else 1
            swap_rate: float = self.symbol.info["swap_long"] if self.position == Op.LONG else self.symbol.info["swap_short"]
            self.swap += round(multiplier * swap_rate * self.lots, 2)

    def close(self, applied_price="open") -> bool:
        assert not self.closed, f"Order Id: {self.id} already closed."
        rates: Dict = self.symbol.get_rate()
        sign: int = 1 if self.position == Op.LONG else -1
        multiplier: float = sign * self.lots * self.symbol.info["lot_size"] * self.symbol.get_pt_value()

        spread: float = 0 if self.position == Op.LONG else self.symbol.get_spread()

        self.close_price = rates[applied_price] + spread
        self.close_time = rates["dt"]
        self.pnl = round((self.close_price - self.open_price) * multiplier - self.commission - self.swap, 2)
        self.max_fl = min(self.max_fl, self.pnl)
        self.max_fp = max(self.max_fp, self.pnl)
        self.closed = True
        #print(f"Order {self.id} Closed")

    def info(self) -> Dict:
        result: Dict = {
            "id": self.id,
            "symbol": self.symbol.info["name"],
            "open_time": self.open_time,
            "open_price": self.open_price,
            "margin": self.margin,
            "lot_size": self.lots,
            "op": self.position,
            "close_time": self.close_time,
            "close_price": self.close_price,
            "pnl": self.pnl,
            "max_fl": self.max_fl,
            "max_fp": self.max_fp
        }
        return result 

    def open(self):
        Order.id += 1
        self.id = Order.id 
        #print(f"Order {self.id} opened.")
