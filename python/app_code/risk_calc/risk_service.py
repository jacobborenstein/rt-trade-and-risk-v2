import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import redis
import json
import time
from datetime import datetime, timedelta
import numpy as np
import yfinance as yf
from risk_calculator import RiskCalculator
from redis_cache.cache_database import retrieve_position_data

class RiskService:
    def __init__(self, data_source, redis_host='redis', redis_port=6379):
        self.r = redis.Redis(host=redis_host, port=6379)
        self.pubsub = self.r.pubsub()
        self.pubsub.subscribe('position-keys')
        self.risk_calculator = RiskCalculator()
        self.data_source = data_source

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
                            risk_measures = self.calculate_risk(position)
                            #have to publish the risk to the 'risk_calculation' channel
                            self.r.publish('risk_calculation', json.dumps(risk_measures))
            
            except Exception as e:
                print(f"Error: {e}")
                time.sleep(5)

    def calculate_risk(self, position):
        ticker = position.ticker  # Access the ticker correctly
        benchmark_ticker = 'SPY'  # Example benchmark ticker

        returns = self.get_historical_returns(ticker)
        benchmark_returns = self.get_benchmark_returns(benchmark_ticker)

        risk_measures = {
            'account': position.account_id,  # Access the account ID correctly
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
        return risk_measures  # Return the risk measures dictionary

    def get_historical_returns(self, ticker):
        historical_prices = self.data_source.get_historical_prices(ticker)
        returns = self.calculate_returns_from_prices(historical_prices)
        return returns

    def get_benchmark_returns(self, benchmark_ticker):
        benchmark_prices = self.data_source.get_historical_prices(benchmark_ticker)
        benchmark_returns = self.calculate_returns_from_prices(benchmark_prices)
        return benchmark_returns
    
    #def store_risk_measures(self, account_id, ticker, risk_measures):
        # Generate a unique key for the risk measures
        #risk_key = f"risk:{account_id}:{ticker}"
        # Store the risk measures in Redis
        #self.r.set(risk_key, json.dumps(risk_measures))
    
    

    @staticmethod
    def calculate_returns_from_prices(prices):
        returns = np.diff(prices) / prices[:-1]
        return returns

class DataSource:
    def get_historical_prices(self, ticker):
        stock_data = yf.Ticker(ticker)
        historical_data = stock_data.history(period="1y")  # Fetches 1 year of data
        return historical_data['Close'].values

if __name__ == "__main__":
    data_source = DataSource()
    risk_service = RiskService(data_source=data_source)
    risk_service.run()
    