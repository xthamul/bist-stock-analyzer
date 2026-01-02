import unittest
import pandas as pd
import numpy as np

from helpers.portfolio_analyzer import calculate_portfolio_metrics

class TestPortfolioAnalyzer(unittest.TestCase):

    def setUp(self):
        """Her test için örnek portföy ve benchmark verisi oluştur."""
        dates = pd.to_datetime(pd.date_range(start="2023-01-01", periods=10, freq='D'))
        
        # Senaryo 1: Portföy, piyasa ile aynı hareket ediyor (Beta ~ 1)
        self.portfolio_history_beta_1 = pd.Series([100, 101, 102, 103, 104, 105, 106, 107, 108, 109], index=dates)
        self.benchmark_history_beta_1 = pd.Series([1000, 1010, 1020, 1030, 1040, 1050, 1060, 1070, 1080, 1090], index=dates)

        # Senaryo 2: Portföy, piyasanın yarısı kadar hareket ediyor (Beta ~ 0.5)
        self.portfolio_history_beta_0_5 = pd.Series([100, 100.5, 101, 101.5, 102, 102.5, 103, 103.5, 104, 104.5], index=dates)
        
        # Senaryo 3: Risksiz, sabit getirili portföy (Volatility = 0, Sharpe tanımsız/sıfır olmalı)
        self.portfolio_constant = pd.Series([100] * 10, index=dates)

    def test_calculate_beta(self):
        """Beta hesaplamasını test et."""
        # Test Beta = 1
        metrics_1 = calculate_portfolio_metrics(self.portfolio_history_beta_1, self.benchmark_history_beta_1)
        self.assertAlmostEqual(metrics_1['beta'], 1.0, places=5, msg="Beta should be almost 1.0 when portfolio moves with market")

        # Test Beta = 0.5
        metrics_0_5 = calculate_portfolio_metrics(self.portfolio_history_beta_0_5, self.benchmark_history_beta_1)
        self.assertAlmostEqual(metrics_0_5['beta'], 0.5, places=5, msg="Beta should be almost 0.5 when portfolio moves half as much as market")
        
        # Test Beta = 0
        metrics_0 = calculate_portfolio_metrics(self.portfolio_constant, self.benchmark_history_beta_1)
        self.assertAlmostEqual(metrics_0['beta'], 0.0, places=5, msg="Beta should be 0.0 for a constant value portfolio")

    def test_calculate_sharpe_and_volatility(self):
        """Sharpe Oranı ve Volatilite hesaplamalarını test et."""
        metrics = calculate_portfolio_metrics(self.portfolio_history_beta_1, self.benchmark_history_beta_1, risk_free_rate=0.0)

        # Volatilite'nin pozitif bir sayı olup olmadığını kontrol et
        self.assertGreater(metrics['annualized_volatility'], 0, "Annualized volatility should be a positive number for a volatile portfolio")

        # Sharpe Oranı'nın pozitif bir sayı olup olmadığını kontrol et (pozitif getiri olduğu için)
        self.assertGreater(metrics['sharpe_ratio'], 0, "Sharpe ratio should be positive for a portfolio with positive returns")

        # Sabit değerli portföy için test
        metrics_constant = calculate_portfolio_metrics(self.portfolio_constant, self.benchmark_history_beta_1)
        self.assertAlmostEqual(metrics_constant['annualized_volatility'], 0.0, places=5, "Volatility should be 0.0 for a constant portfolio")
        self.assertAlmostEqual(metrics_constant['sharpe_ratio'], 0.0, places=5, "Sharpe Ratio should be 0.0 for a constant portfolio")
        
    def test_calculate_returns(self):
        """Kümülatif ve yıllık getiri hesaplamalarını test et."""
        metrics = calculate_portfolio_metrics(self.portfolio_history_beta_1, self.benchmark_history_beta_1)
        
        # Kümülatif getiri: (109 / 100) - 1 = 0.09
        self.assertAlmostEqual(metrics['cumulative_return'], 0.09, places=5)
        
        # Yıllık getiri (sadece pozitif olmasını kontrol et, formül karmaşık)
        self.assertGreater(metrics['annualized_return'], 0)

if __name__ == '__main__':
    unittest.main()
