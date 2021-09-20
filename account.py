from datetime import datetime
from os import access
from symbol import sym_name
from broker import Broker
from config import Config, Op
from order import Order
from instrument import Symbol
from typing import List, Dict, Union
import pandas as pd

class Account:
    def __init__(self, broker: Broker, symbol: Symbol) -> None:
        '''
        Account(): Initialize a new account object with the desire trading symbol
        '''
        self.broker: Broker = broker
        self.symbol: Symbol = symbol
        self.df: pd.DataFrame = pd.DataFrame(0.00, columns=Config.account["fields"], index=self.broker.dt)
        self.df.balance = Config.account["balance"]
        self.df.equity = Config.account["balance"]
        self.df.margin_free = Config.account["balance"]
        self.orders: List[Order] = []
        self.history: List[Order] = []
        self.balance: float = Config.account["balance"]
        self.equity: float = self.balance
        self.margin_hold: float = 0
        self.margin_free: float = self.equity 
        self.stop_out: float = Config.account["stop_out"]
        self.max_fl: float = 0.0
        self.max_fp: float = 0.0
        self.max_dd: float = 0
        self.win_count: int = 0
        self.loss_count: int = 0
        self.break_even: int = 0
        self.last_pnl: float = 0
        
    def action(self, action: Op, lots: float = 0, applied_price: str = "open") -> None:
        '''
        Account.action(action: Op, lots: float = 0, applied_price: str = 'open'):
        The account will perform a action either (Long, Short, Close all, Hold) for each time step
        '''
        assert action in [Op.LONG, Op.SHORT, Op.CLOSEALL, Op.HOLD], "Invalid Operation"
        prev_balance: float = self.balance
        if action != Op.HOLD:

            if action in [Op.LONG, Op.SHORT, Op.CLOSEALL]:
                for o in self.orders:
                    if o.position != action:
                        o.close(applied_price=applied_price)
                        self.history.insert(len(self.history), self.orders.pop(self.orders.index(o)))
                
            if len(self.orders) == 0:
                self.max_fp = self.max_fl = 0
            
            if action in [Op.LONG, Op.SHORT]:
                order: Order = Order(symbol=self.symbol, action=action, lots=lots, applied_price=applied_price)
                if order.margin < self.margin_free:
                    flag: bool = True
                    if not Config.env["allow_multi_orders"]:
                        assert len(self.orders) < 2, "Multiple Orders are not allow"
                        if len(self.orders) == 1:
                            flag = False
                    if flag:
                        order.open()
                        self.orders.append(order)
                

        for o in self.orders:
            o.update()
        
        self.balance = Config.account["balance"] + sum(o.pnl for o in self.history)
        self.equity = self.balance + sum(o.pnl for o in self.orders)
        self.last_pnl = self.balance - prev_balance
        self.total_orders = len(self.orders)
        pnl = self.equity - self.balance
        self.max_fl = min(self.max_fl, pnl)
        self.max_fp = max(self.max_fp, pnl)
        self.max_dd = min(self.max_dd, self.last_pnl)

        self.margin_hold = sum(o.margin for o in self.orders)
        self.margin_free = self.equity - self.margin_hold
        
        self.win_count = sum(1 for o in self.history if o.pnl > 0)
        self.loss_count = sum(1 for o in self.history if o.pnl < 0)
        self.break_even = len(self.history) - self.win_count - self.loss_count

        self.df.iloc[self.broker.shift].balance = self.balance
        self.df.iloc[self.broker.shift].equity = self.equity
        self.df.iloc[self.broker.shift].last_pnl = self.last_pnl
        self.df.iloc[self.broker.shift].total_orders = self.total_orders
        self.df.iloc[self.broker.shift].margin_hold = self.margin_hold
        self.df.iloc[self.broker.shift].margin_free = self.margin_free
        self.df.iloc[self.broker.shift].max_fl = self.max_fl
        self.df.iloc[self.broker.shift].max_fp = self.max_fp
        self.df.iloc[self.broker.shift].max_dd = self.max_dd
        self.df.iloc[self.broker.shift].win_count = self.win_count
        self.df.iloc[self.broker.shift].loss_count = self.loss_count
        self.df.iloc[self.broker.shift].break_even = self.break_even

    def info(self) -> Dict:
        result: Dict = {
            "balance": round(self.balance,2),
            "equity": round(self.equity,2),
            "last_pnl": round(self.last_pnl,2),
            "order_count": len(self.orders),
            "margin_hold": round(self.margin_hold,2),
            "margin_free": round(self.margin_free,2),
            "wins": self.win_count,
            "loss": self.loss_count,
            "break_even": self.break_even,
            "max_dd": round(self.max_dd, 2)
        }
        return result


    def save(self, name: str, id: int) -> None:
        '''
        Account.save(): save the account movement to a csv file
        '''
        tmp: List[Dict] = [o.info() for o in self.history]
        orders: pd.DataFrame = pd.DataFrame(tmp)
        #print(orders)
        orders.to_csv(f"./record/Order-{name}-{id}-{datetime.now():m%d%H%M}.csv")
        self.df.to_csv(f"./record/Account-{name}-{id}-{datetime.now():%m%d%H%M}.csv")

    def get_features(self, features: List[str], window_size = 1) -> Union[pd.DataFrame, pd.Series]:
        '''
        Account.get_features()
        This is to get the account features for the current timestep
        '''
        assert set(features) <= set(self.df.columns), "Some features not exists in account data"
        assert window_size >=0, "window size is less than 0"
        assert window_size <= self.broker.shift, "window size should not greater than the price data shift (broker.shift)"
        result: pd.DataFrame = None

        if window_size == 0:
            result = self.df.iloc[:self.broker.shift+1,]
        elif window_size == 1:
            result = self.df.iloc[self.broker.shift]
        else:
            result = self.df.iloc[self.broker.shift-window_size+1, self.broker.shift+1]
            assert result.index[-1] == self.broker.dt[self.broker.shift], "Account features alignment has problem"
        assert result is not None, "Error in getting account feature"
        return result
