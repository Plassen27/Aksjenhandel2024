import pytz
from datetime import datetime

stocks = [
    {"ticker": "SDRL.OL", "strategy": 10, "interval": "15m", "period": "30d", "priority": 2},
    {"ticker": "BWLPG.OL", "strategy": 10, "interval": "15m", "period": "30d", "priority": 1},
    {"ticker": "NAS.OL", "strategy": 13, "interval": "15m", "period": "30d", "priority": 3},
    {"ticker": "AKRBP.OL", "strategy": 9, "interval": "15m", "period": "30d", "priority": 4},
    {"ticker": "AUTO.OL", "strategy": 10, "interval": "15m", "period": "30d", "priority": 5},
    {"ticker": "NEL.OL", "strategy": 10, "interval": "15m", "period": "30d", "priority": 6},
    {"ticker": "PGS.OL", "strategy": 13, "interval": "15m", "period": "30d", "priority": 7},
]

start_date = datetime(2023, 6, 3, 6, 0, 0, tzinfo=pytz.timezone('Europe/Oslo'))

# Set end_date to today's date
end_date = datetime.now()

total_cash = 100000

order_size = 25000

order_size_minimum = 20000

kurtajse = 0.0004

Kolonnevisning = 10
