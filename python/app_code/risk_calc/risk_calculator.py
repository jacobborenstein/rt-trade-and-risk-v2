import numpy as np

class RiskCalculator:
    def __init__(self, risk_free_rate=0.02):
        self.risk_free_rate = risk_free_rate

    def calculate_standard_deviation(self, returns):
        return np.std(returns)

    def calculate_sharpe_ratio(self, returns):
        avg_return = np.mean(returns)
        std_dev = self.calculate_standard_deviation(returns)
        return (avg_return - self.risk_free_rate) / std_dev if std_dev != 0 else 0

    def calculate_alpha(self, investment_returns, benchmark_returns):
        excess_return = np.mean(investment_returns) - self.risk_free_rate
        benchmark_excess_return = np.mean(benchmark_returns) - self.risk_free_rate
        beta = np.cov(investment_returns, benchmark_returns)[0, 1] / np.var(benchmark_returns)
        alpha = excess_return - beta * benchmark_excess_return
        return alpha

    def calculate_beta(self, investment_returns, benchmark_returns):
        covariance = np.cov(investment_returns, benchmark_returns)[0, 1]
        variance = np.var(benchmark_returns)
        beta = covariance / variance
        return beta

    def calculate_r_squared(self, investment_returns, benchmark_returns):
        correlation_matrix = np.corrcoef(investment_returns, benchmark_returns)
        correlation = correlation_matrix[0, 1]
        r_squared = correlation ** 2
        return r_squared
