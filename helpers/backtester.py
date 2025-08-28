
from backtesting import Backtest, Strategy
from backtesting.lib import crossover
import pandas as pd
import pandas_ta as ta

# Strateji 1: EMA Kesişimi
class EmaCross(Strategy):
    n1 = 50
    n2 = 200
    stop_loss = None
    take_profit = None

    def init(self):
        self.ema1 = self.I(ta.ema, pd.Series(self.data.Close), length=self.n1)
        self.ema2 = self.I(ta.ema, pd.Series(self.data.Close), length=self.n2)

    def next(self):
        if crossover(self.ema1, self.ema2):
            if not self.position:
                sl = self.data.Close[-1] * (1 - self.stop_loss) if self.stop_loss else None
                tp = self.data.Close[-1] * (1 + self.take_profit) if self.take_profit else None
                self.buy(sl=sl, tp=tp)
        elif crossover(self.ema2, self.ema1):
            self.position.close()

# Strateji 2: RSI Osilatörü
class RsiOscillator(Strategy):
    buy_threshold = 30
    sell_threshold = 70
    rsi_window = 14
    stop_loss = None
    take_profit = None

    def init(self):
        self.rsi = self.I(ta.rsi, pd.Series(self.data.Close), length=self.rsi_window)

    def next(self):
        if crossover(self.rsi, self.buy_threshold):
            if not self.position:
                sl = self.data.Close[-1] * (1 - self.stop_loss) if self.stop_loss else None
                tp = self.data.Close[-1] * (1 + self.take_profit) if self.take_profit else None
                self.buy(sl=sl, tp=tp)
        elif crossover(self.sell_threshold, self.rsi):
            self.position.close()

# Strateji 3: MACD Kesişimi
class MacdCross(Strategy):
    fast = 12
    slow = 26
    signal = 9
    stop_loss = None
    take_profit = None

    def init(self):
        # ta.macd returns a DataFrame, self.I will return a tuple of arrays
        macd_data = self.I(ta.macd, pd.Series(self.data.Close), fast=self.fast, slow=self.slow, signal=self.signal)
        self.macd_line = macd_data[0]
        self.signal_line = macd_data[2] # macd_data[1] is the histogram

    def next(self):
        if crossover(self.macd_line, self.signal_line):
            if not self.position:
                sl = self.data.Close[-1] * (1 - self.stop_loss) if self.stop_loss else None
                tp = self.data.Close[-1] * (1 + self.take_profit) if self.take_profit else None
                self.buy(sl=sl, tp=tp)
        elif crossover(self.signal_line, self.macd_line):
            self.position.close()

# Strateji 4: Bollinger Bandı Stratejisi
class BBandStrategy(Strategy):
    length = 20
    std = 2.0
    stop_loss = None
    take_profit = None

    def init(self):
        bbands = self.I(ta.bbands, pd.Series(self.data.Close), length=self.length, std=self.std)
        self.lower_band = bbands[0]
        self.upper_band = bbands[2]

    def next(self):
        if crossover(self.lower_band, self.data.Close):
            if not self.position:
                sl = self.data.Close[-1] * (1 - self.stop_loss) if self.stop_loss else None
                tp = self.data.Close[-1] * (1 + self.take_profit) if self.take_profit else None
                self.buy(sl=sl, tp=tp)
        elif crossover(self.data.Close, self.upper_band):
            self.position.close()

def _prepare_data_for_backtesting(data):
    """Gelen veriyi backtesting için hazırlar (günlük frekans, büyük harfli sütunlar)."""
    daily_data = data.copy()
    daily_data.index = pd.to_datetime(daily_data.index)
    # Ensure there are no duplicate indices
    daily_data = daily_data[~daily_data.index.duplicated(keep='first')]
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
    bt = Backtest(daily_data, strategy_class, cash=cash, commission=commission, trade_on_close=True)
    stats = bt.run(**strategy_params)
    if pd.api.types.is_timedelta64_dtype(stats):
        stats = stats.apply(lambda x: x.total_seconds())
    if isinstance(stats.index, pd.TimedeltaIndex):
        stats.index = stats.index.astype(str)
    return stats, bt.plot(open_browser=False)

def optimize_strategy(strategy_class, data, cash=100000, commission=0.002, maximize='Equity Final [$]', **optimization_params):
    """Verilen parametre aralıkları için bir stratejinin optimizasyonunu çalıştırır."""
    daily_data = _prepare_data_for_backtesting(data)
    bt = Backtest(daily_data, strategy_class, cash=cash, commission=commission, trade_on_close=True)
    
    # Optimizasyonu çalıştır ve tüm sonuçları içeren bir heatmap serisi al
    heatmap = bt.optimize(**optimization_params, maximize=maximize, return_heatmap=True)
    
    # Timedelta içeren sütunları dönüştür (eğer varsa, genellikle olmaz ama tedbir amaçlı)
    if isinstance(heatmap, pd.Series):
        if pd.api.types.is_timedelta64_dtype(heatmap):
            heatmap = heatmap.apply(lambda x: x.total_seconds())
        if isinstance(heatmap.index, pd.TimedeltaIndex):
            heatmap.index = heatmap.index.astype(str)
            
    return heatmap
