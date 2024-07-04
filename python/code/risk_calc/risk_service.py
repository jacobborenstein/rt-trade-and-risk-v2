# risk_service.py
import redis
import json
import time
from datetime import datetime
import numpy as np
from risk_calculator import RiskCalculator

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
                        position_data = message['data']
                        position_dict = json.loads(position_data)
                        self.calculate_risk(position_dict)
            except Exception as e:
                print(f"Error: {e}")
                time.sleep(5)

    def calculate_risk(self, position):
        returns = self.simulate_returns(position)
        benchmark_returns = self.simulate_benchmark_returns()

        risk_measures = {
            'account': position['account'],
            'ticker': position['ticker'],
            'standard_deviation': self.risk_calculator.calculate_standard_deviation(returns),
            'sharpe_ratio': self.risk_calculator.calculate_sharpe_ratio(returns),
            'alpha': self.risk_calculator.calculate_alpha(returns, benchmark_returns),
            'beta': self.risk_calculator.calculate_beta(returns, benchmark_returns),
            'r_squared': self.risk_calculator.calculate_r_squared(returns, benchmark_returns),
            'last_updated': datetime.now().isoformat()
        }

        print(f"Calculated risk measures: {risk_measures}")
        # Optionally, publish or store the risk measures

    def simulate_returns(self, position):
        np.random.seed(0)
        returns = np.random.normal(0, 0.1, 100)
        return returns

    def simulate_benchmark_returns(self):
        np.random.seed(1)
        benchmark_returns = np.random.normal(0, 0.1, 100)
        return benchmark_returns

if __name__ == "__main__":
    risk_service = RiskService()
    risk_service.run()
