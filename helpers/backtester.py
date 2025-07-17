
from backtesting import Backtest, Strategy
from backtesting.lib import crossover
import pandas as pd

# Strateji Tanımı
class EmaCross(Strategy):
    n1 = 50
    n2 = 200

    def init(self):
        close = self.data.Close
        # EMA'ları backtesting kütüphanesinin kendi gösterge fonksiyonuyla (self.I) tanımla
        # Bu, veri serisini doğru şekilde işlemesini sağlar.
        self.ema1 = self.I(lambda x: pd.Series(x).ewm(span=self.n1, adjust=False).mean(), self.data.Close)
        self.ema2 = self.I(lambda x: pd.Series(x).ewm(span=self.n2, adjust=False).mean(), self.data.Close)

    def next(self):
        if crossover(self.ema1, self.ema2):
            self.buy()
        elif crossover(self.ema2, self.ema1):
            self.sell()

def run_backtest(data, cash=100000, commission=.002):
    """ 
    Verilen veri üzerinde EMA Cross stratejisini test eder ve sonuçları döndürür.
    Gelen veriyi her zaman günlük frekansa dönüştürür.
    """
    # --- Veriyi Günlük Frekansa Çevirme ---
    # Gelen verinin zaman damgasını (index) datetime nesnesine dönüştür
    daily_data = data.copy()
    daily_data.index = pd.to_datetime(daily_data.index)

    # Veriyi günlük olarak yeniden örnekle (resample)
    # Her günün Kapanış (Close) fiyatını o günün son fiyatı olarak al
    # Açılış (Open), En Yüksek (High), En Düşük (Low) ve Hacim (Volume) için de uygun birleştirme yöntemleri kullan
    daily_data = daily_data.resample('D').agg({
        'open': 'first',
        'high': 'max',
        'low': 'min',
        'close': 'last',
        'volume': 'sum'
    }).dropna() # Veri olmayan günleri (hafta sonları vb.) kaldır

    # Backtesting için sütun adlarını büyük harfle başlat
    daily_data.columns = [col.capitalize() for col in daily_data.columns]
    
    # Backtest nesnesini oluştur
    bt = Backtest(daily_data, EmaCross, cash=cash, commission=commission)
    
    # Testi çalıştır ve sonuçları al
    stats = bt.run()
    
    # Sonuçları ve çizim grafiğini döndür
    return stats, bt.plot(open_browser=False)
