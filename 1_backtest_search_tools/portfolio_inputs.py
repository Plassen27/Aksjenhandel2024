from datetime import datetime

stocks = [
    {"ticker": "PGS.OL", "strategy": 11, "interval": "15m", "period": "30d"},
    {"ticker": "DNO.OL", "strategy": 11, "interval": "15m", "period": "30d"}
]

start_date = datetime(2023, 3, 29)
end_date = datetime(2023, 7, 5)
total_cash = 100_000
order_size = 5000

