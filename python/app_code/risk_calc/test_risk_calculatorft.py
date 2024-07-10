import numpy as np
from risk_calculatorft import RiskCalculator

def test_risk_calculator():
    np.random.seed(0)
    returns = np.random.normal(0, 0.1, 100)
    benchmark_returns = np.random.normal(0, 0.1, 100)
    
    risk_calculator = RiskCalculator()
    
    std_dev = risk_calculator.calculate_standard_deviation(returns)
    sharpe_ratio = risk_calculator.calculate_sharpe_ratio(returns)
    alpha = risk_calculator.calculate_alpha(returns, benchmark_returns)
    beta = risk_calculator.calculate_beta(returns, benchmark_returns)
    r_squared = risk_calculator.calculate_r_squared(returns, benchmark_returns)
    
    print(f"Standard Deviation: {std_dev}")
    print(f"Sharpe Ratio: {sharpe_ratio}")
    print(f"Alpha: {alpha}")
    print(f"Beta: {beta}")
    print(f"R-Squared: {r_squared}")

if __name__ == "__main__":
    test_risk_calculator()
