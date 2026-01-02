import numpy as np
import pandas as pd

def calculate_portfolio_metrics(portfolio_history, benchmark_history, risk_free_rate=0.0):
    """
    Calculates advanced risk and return metrics for a given portfolio history.

    Args:
        portfolio_history (pd.Series): A Series of daily total portfolio values, indexed by date.
        benchmark_history (pd.Series): A Series of daily benchmark (e.g., index) values.
        risk_free_rate (float): The annual risk-free rate for Sharpe Ratio calculation.

    Returns:
        dict: A dictionary containing the calculated metrics.
    """
    if portfolio_history.empty or benchmark_history.empty:
        return {}

    # Calculate daily returns
    portfolio_returns = portfolio_history.pct_change().dropna()
    benchmark_returns = benchmark_history.pct_change().dropna()
    
    # Align data by index
    aligned_returns = pd.concat([portfolio_returns, benchmark_returns], axis=1, join='inner')
    aligned_returns.columns = ['portfolio', 'benchmark']
    
    if len(aligned_returns) < 2:
        return {} # Not enough data to calculate metrics

    # --- Calculate Metrics ---
    
    # 1. Beta
    covariance = aligned_returns['portfolio'].cov(aligned_returns['benchmark'])
    variance = aligned_returns['benchmark'].var()
    beta = covariance / variance if variance != 0 else 0.0

    # 2. Sharpe Ratio
    # Assuming 252 trading days in a year
    trading_days = 252
    excess_returns = portfolio_returns - (risk_free_rate / trading_days)
    sharpe_ratio = (excess_returns.mean() / excess_returns.std()) * np.sqrt(trading_days) if excess_returns.std() != 0 else 0.0
    
    # 3. Annualized Volatility (Standard Deviation)
    annualized_volatility = portfolio_returns.std() * np.sqrt(trading_days)
    
    # 4. Cumulative Return
    cumulative_return = (portfolio_history.iloc[-1] / portfolio_history.iloc[0]) - 1
    
    # 5. Annualized Return
    total_days = (portfolio_history.index[-1] - portfolio_history.index[0]).days
    annualized_return = ((1 + cumulative_return) ** (365.25 / total_days)) - 1 if total_days > 0 else 0.0

    # 6. Max Drawdown
    cumulative_returns = (1 + portfolio_returns).cumprod()
    peak = cumulative_returns.expanding(min_periods=1).max()
    drawdown = (cumulative_returns/peak) - 1
    max_drawdown = drawdown.min()
    
    return {
        "beta": beta,
        "sharpe_ratio": sharpe_ratio,
        "annualized_volatility": annualized_volatility,
        "annualized_return": annualized_return,
        "max_drawdown": max_drawdown,
        "cumulative_return": cumulative_return
    }

def plot_portfolio_vs_benchmark(portfolio_history, benchmark_history):
    """
    Creates a Plotly figure comparing normalized portfolio performance against a benchmark.
    """
    import plotly.graph_objects as go

    if portfolio_history.empty or benchmark_history.empty:
        return go.Figure().update_layout(title_text="Veri yetersiz.")

    # Normalize both series to start at 100
    portfolio_normalized = (portfolio_history / portfolio_history.iloc[0]) * 100
    benchmark_normalized = (benchmark_history / benchmark_history.iloc[0]) * 100
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=portfolio_normalized.index,
        y=portfolio_normalized,
        mode='lines',
        name='Portföy',
        line=dict(color='cyan', width=2)
    ))
    
    fig.add_trace(go.Scatter(
        x=benchmark_normalized.index,
        y=benchmark_normalized,
        mode='lines',
        name='BIST 100 (XU100)',
        line=dict(color='orange', width=2, dash='dash')
    ))
    
    fig.update_layout(
        title="Portföy Performansı vs. BIST 100 (Normalize Edilmiş)",
        xaxis_title="Tarih",
        yaxis_title="Normalize Edilmiş Değer (Başlangıç = 100)",
        legend_title="Karşılaştırma",
        template="plotly_dark",
    )
    
    return fig

