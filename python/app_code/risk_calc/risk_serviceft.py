import json
from datetime import datetime
import numpy as np
from risk_calculatorft import RiskCalculator

class RiskService:
    def __init__(self):
        self.risk_calculatorft = RiskCalculator()

    def calculate_risk(self, position):
        returns = self.simulate_returns(position)
        benchmark_returns = self.simulate_benchmark_returns()

        risk_measures = {
            'account': position['account']['account_id'],
            'ticker': position['ticker'],
            'standard_deviation': self.risk_calculatorft.calculate_standard_deviation(returns),
            'sharpe_ratio': self.risk_calculatorft.calculate_sharpe_ratio(returns),
            'alpha': self.risk_calculatorft.calculate_alpha(returns, benchmark_returns),
            'beta': self.risk_calculatorft.calculate_beta(returns, benchmark_returns),
            'r_squared': self.risk_calculatorft.calculate_r_squared(returns, benchmark_returns),
            'last_updated': datetime.now().isoformat()
        }

        print(f"Calculated risk measures: {risk_measures}")
        return risk_measures

    def simulate_returns(self, position):
        np.random.seed(0)
        returns = np.random.normal(0, 0.1, 100)
        return returns

    def simulate_benchmark_returns(self):
        np.random.seed(1)
        benchmark_returns = np.random.normal(0, 0.1, 100)
        return benchmark_returns

if __name__ == "__main__":
    # Example position data
    position = {
        "account": {
            "account_id": "A123",
            "account_name": "Test Account"
        },
        "ticker": "AAPL",
        "quantity": 100,
        "avgPrice": 150.0,
        "lastUpdated": "2024-07-03T10:00:00Z"
    }

    risk_service = RiskService()
    risk_measures = risk_service.calculate_risk(position)
    #print(risk_measures)
