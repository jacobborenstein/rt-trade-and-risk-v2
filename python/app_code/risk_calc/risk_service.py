import redis
import json
import time
from datetime import datetime
import numpy as np
from risk_calculator import RiskCalculator
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'redis_cache')))
from cache_database import retrieve_position_data, retrieve_price_data

class RiskService:
    def __init__(self, redis_host='localhost', redis_port=6379):
        self.r = redis.Redis(host=redis_host, port=6379)
        self.pubsub = self.r.pubsub()
        self.pubsub.subscribe('position-keys')
        self.risk_calculator = RiskCalculator()

    def run(self):
        while True:
            try:
                for message in self.pubsub.listen():
                    if message['type'] == 'message':
                        position_key_data = message['data']
                        position_key_dict = json.loads(position_key_data)
                        account_id = position_key_dict['account_id']
                        ticker = position_key_dict['ticker']
                        
                        # Retrieve position data using retrieve_position_data
                        position = retrieve_position_data(self.r, account_id, ticker)
                        if position:
                            self.calculate_risk(position)
            except Exception as e:
                print(f"Error: {e}")
                time.sleep(5)

    def calculate_risk(self, position):
        ticker = position.ticker
        benchmark_ticker = 'SPY'  # Example benchmark ticker

        returns = self.get_historical_returns(ticker)
        benchmark_returns = self.get_benchmark_returns(benchmark_ticker)

        risk_measures = {
            'account': position.account.account_id,
            'ticker': ticker,
            'standard_deviation': self.risk_calculator.calculate_standard_deviation(returns),
            'sharpe_ratio': self.risk_calculator.calculate_sharpe_ratio(returns),
            'alpha': self.risk_calculator.calculate_alpha(returns, benchmark_returns),
            'beta': self.risk_calculator.calculate_beta(returns, benchmark_returns),
            'r_squared': self.risk_calculator.calculate_r_squared(returns, benchmark_returns),
            'last_updated': datetime.now().isoformat()
        }

        print(f"Calculated risk measures: {risk_measures}")
        # Optionally, publish or store the risk measures

    def get_historical_returns(self, ticker):
        # Fetch the historical prices from Redis
        historical_prices = self.get_prices_from_redis(ticker)
        if historical_prices is None:
            print(f"No historical prices found for ticker {ticker}")
            return []

        returns = self.calculate_returns_from_prices(historical_prices)
        return returns

    def get_benchmark_returns(self, benchmark_ticker):
        # Fetch the benchmark historical prices from Redis
        benchmark_prices = self.get_prices_from_redis(benchmark_ticker)
        if benchmark_prices is None:
            print(f"No benchmark prices found for ticker {benchmark_ticker}")
            return []

        benchmark_returns = self.calculate_returns_from_prices(benchmark_prices)
        return benchmark_returns

    def get_prices_from_redis(self, ticker):
        # Retrieve price data from Redis
        prices = retrieve_price_data(self.r, ticker)
        if prices is None:
            print(f"No price data found for ticker {ticker}")
            return None
        return prices

    @staticmethod
    def calculate_returns_from_prices(prices):
        returns = np.diff(prices) / prices[:-1]
        return returns

if __name__ == "__main__":
    risk_service = RiskService()
    risk_service.run()
