
from backtesting import Backtest, Strategy
from backtesting.lib import crossover
import pandas as pd

# Strateji Tanımı
class EmaCross(Strategy):
    # Strateji parametreleri
    n1 = 50  # Hızlı EMA periyodu
    n2 = 200 # Yavaş EMA periyodu

    def init(self):
        # Strateji başlatıldığında çalışır
        close = self.data.Close
        # İki EMA göstergesini hesapla
        self.ema1 = self.I(lambda x: pd.Series(x).ewm(span=self.n1, adjust=False).mean(), close)
        self.ema2 = self.I(lambda x: pd.Series(x).ewm(span=self.n2, adjust=False).mean(), close)

    def next(self):
        # Her bir veri noktası (mum) için çalışır
        # Eğer hızlı EMA, yavaş EMA'yı yukarı keserse (Golden Cross)
        if crossover(self.ema1, self.ema2):
            self.buy() # Alım yap
        # Eğer hızlı EMA, yavaş EMA'yı aşağı keserse (Death Cross)
        elif crossover(self.ema2, self.ema1):
            self.sell() # Satım yap

def run_backtest(data, cash=100000, commission=.002):
    """ 
    Verilen veri üzerinde EMA Cross stratejisini test eder ve sonuçları döndürür.
    """
    # Backtesting için veri formatını hazırla (Sütun adları büyük harfle başlamalı)
    bt_data = data.copy()
    bt_data.columns = [col.capitalize() for col in bt_data.columns]
    
    # Backtest nesnesini oluştur
    bt = Backtest(bt_data, EmaCross, cash=cash, commission=commission)
    
    # Testi çalıştır ve sonuçları al
    stats = bt.run()
    
    # Sonuçları ve çizim grafiğini döndür
    return stats, bt.plot(open_browser=False)
