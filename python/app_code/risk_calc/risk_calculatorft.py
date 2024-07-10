import numpy as np

class RiskCalculator:
    def calculate_standard_deviation(self, returns):
        return np.std(returns)

    def calculate_sharpe_ratio(self, returns, risk_free_rate=0.0):
        return (np.mean(returns) - risk_free_rate) / np.std(returns)

    def calculate_alpha(self, returns, benchmark_returns, risk_free_rate=0.0):
        return np.mean(returns) - (risk_free_rate + self.calculate_beta(returns, benchmark_returns) * (np.mean(benchmark_returns) - risk_free_rate))

    def calculate_beta(self, returns, benchmark_returns):
        covariance = np.cov(returns, benchmark_returns)[0][1]
        variance = np.var(benchmark_returns)
        return covariance / variance

    def calculate_r_squared(self, returns, benchmark_returns):
        correlation_matrix = np.corrcoef(returns, benchmark_returns)
        correlation_xy = correlation_matrix[0, 1]
        return correlation_xy ** 2
