from enum import IntEnum
from typing import List, Dict

class AssetType(IntEnum):
    FOREX = 0
    CFD = 1

class SpreadMode(IntEnum):
    BIDASK = 0
    RANDOM = 1
    IGNORE = 2
    FIXED = 3
    SESSIONAL = 4

class Op(IntEnum):
    LONG = 0
    SHORT = 1
    HOLD = 2
    CLOSEALL = 3

class Config:
    datafile:str = './2021617-60.csv'

    fields:Dict = {
        "symbol" : "symbol",
        "dt" : "dt",
        "tf" : "tf",
        "open" : "open",
        "high" : "high",
        "low" : "low",
        "close" : "close",
        "vol" : "volume",
        "bid" : "bid",
        "ask" : "ask"}
    
    symbols: List[Dict] = [{
        "name" : "USDJPY",
        "asset_type": AssetType.FOREX,
        "leverage": 100,
        "quote" : "JPY",
        "base" : "USD",
        "digits" : 3,
        "commission" : 7,
        "min_lot" : 0.01,
        "max_lot" : 1,
        "lot_step" : 0.01,
        "lot_size" : 100000,
        "swap_long" : 2.30,
        "swap_short" : 2.75,
        "swap_day" : 2,
        "min_spread" : 1,
        "max_spread" : 10,
        "fixed_spread": 3,
        "spread_mode" : SpreadMode.RANDOM,
        "fixed_pt_value" : 1
    },
    {
        "name" : "EURUSD",
        "asset_type": AssetType.FOREX,
        "leverage": 100,
        "quote" : "USD",
        "base" : "EUR",
        "digits" : 5,
        "commission" : 0,
        "min_lot" : 0.01,
        "max_lot" : 1,
        "lot_step" : 0.01,
        "lot_size" : 100000,
        "swap_long" : 0,
        "swap_short" : 0,
        "swap_day" : 2,
        "min_spread" : 1,
        "max_spread" : 10,
        "fixed_spread": 3,
        "spread_mode" : SpreadMode.IGNORE,
        "fixed_pt_value" : 1
    }]

    account: Dict = {
        "balance": 10000.00,
        "stop_out": 0.5,
        "currency": "USD",
        "fields": ["balance", "equity", "last_pnl", "total_orders", "margin_hold", "margin_free", "max_fl", "max_fp", "max_dd", "win_counts", "loss_count", "break_even"]
    }

    env: Dict = {
        "window_size": 12,
        "allow_multi_orders": False,
        "obs_price_features": [],
        "obs_price_exclude": ["tf", "symbol", "bid", "ask"],
        #"obs_account_features": ["balance", "equity", "total_orders", "margin_hold", "margin_free", "max_fl", "max_fp", "win_counts", "loss_count", "break_even"]
        "obs_account_features": ["balance", "equity", "win_counts", "loss_count", "break_even"]
    }
