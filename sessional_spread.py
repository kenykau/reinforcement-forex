from datetime import datetime, time
from typing import List, Dict


class SessionalSpread:
    def __init__(self) -> None:
        self.spreads: List[Dict] = []
    
    def add_spread(self, begin: time, end: time, spread: float) -> None:
        self.spreads.append({
            "begin": begin,
            "end": end,
            "spread": spread
        })
    
    def get_spread(self, dt: datetime) -> float:
        t = dt.time()
        result = list(filter(lambda x: t >= x["begin"] and t <= x["end"], self.spreads))
        assert len(result) == 1, "None or more than 1 spread found at {}".format(dt)
        return result[0]["spread"]
