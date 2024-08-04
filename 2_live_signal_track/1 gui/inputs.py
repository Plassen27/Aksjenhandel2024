import pytz
from datetime import datetime

stocks = [
    {"ticker": "DOGE-USD", "strategy": 11, "interval": "15m", "period": "30d", "priority": 2},
    {"ticker": "SHIB-USD", "strategy": 11, "interval": "15m", "period": "30d", "priority": 1}
]


start_date = datetime(2023, 7, 10, 6, 0, 0, tzinfo=pytz.timezone('Europe/Oslo'))

total_cash = 100000

order_size = 1000

kurtajse = 0.0004

Kolonnevisning = 10
