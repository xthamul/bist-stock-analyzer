
from backtesting import Backtest, Strategy
from backtesting.lib import crossover
import pandas as pd
import pandas_ta as ta

# Strateji 1: EMA Kesişimi
class EmaCross(Strategy):
    n1 = 50
    n2 = 200

    def init(self):
        self.ema1 = self.I(ta.ema, pd.Series(self.data.Close), length=self.n1)
        self.ema2 = self.I(ta.ema, pd.Series(self.data.Close), length=self.n2)

    def next(self):
        if crossover(self.ema1, self.ema2):
            self.buy()
        elif crossover(self.ema2, self.ema1):
            self.sell()

# Strateji 2: RSI Osilatörü
class RsiOscillator(Strategy):
    buy_threshold = 30
    sell_threshold = 70
    rsi_window = 14

    def init(self):
        self.rsi = self.I(ta.rsi, pd.Series(self.data.Close), length=self.rsi_window)

    def next(self):
        if crossover(self.rsi, self.buy_threshold):
            self.buy()
        elif crossover(self.sell_threshold, self.rsi):
            self.sell()

def _prepare_data_for_backtesting(data):
    """Gelen veriyi backtesting için hazırlar (günlük frekans, büyük harfli sütunlar)."""
    daily_data = data.copy()
    daily_data.index = pd.to_datetime(daily_data.index)
    daily_data = daily_data.resample('D').agg({
        'open': 'first',
        'high': 'max',
        'low': 'min',
        'close': 'last',
        'volume': 'sum'
    }).dropna()
    daily_data.columns = [col.capitalize() for col in daily_data.columns]
    return daily_data

def run_backtest(strategy_class, data, cash=100000, commission=0.002, **strategy_params):
    """Verilen veri üzerinde seçilen stratejiyi tek bir test olarak çalıştırır."""
    daily_data = _prepare_data_for_backtesting(data)
    bt = Backtest(daily_data, strategy_class, cash=cash, commission=commission)
    stats = bt.run(**strategy_params)
    return stats, bt.plot(open_browser=False)

def optimize_strategy(strategy_class, data, cash=100000, commission=0.002, **optimization_params):
    """Verilen parametre aralıkları için bir stratejinin optimizasyonunu çalıştırır."""
    daily_data = _prepare_data_for_backtesting(data)
    bt = Backtest(daily_data, strategy_class, cash=cash, commission=commission)
    stats = bt.optimize(**optimization_params, maximize='Equity Final [$]')
    return stats, stats._strategy
