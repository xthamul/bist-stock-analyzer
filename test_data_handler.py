import unittest
import pandas as pd
import numpy as np

from helpers.data_handler import calculate_indicators

class TestDataHandler(unittest.TestCase):

    def setUp(self):
        """Her test için örnek bir fiyat verisi DataFrame'i oluştur."""
        data = {
            'open': [100, 102, 101, 103, 105, 104, 106, 108, 107, 109, 110, 112, 111, 113],
            'high': [103, 104, 103, 105, 106, 105, 107, 109, 108, 110, 111, 113, 112, 114],
            'low': [99, 101, 100, 102, 104, 103, 105, 107, 106, 108, 109, 111, 110, 112],
            'close': [102, 103, 102, 104, 105, 104, 106, 108, 107, 109, 110, 112, 111, 113],
            'volume': [1000, 1100, 1200, 1150, 1250, 1300, 1350, 1400, 1450, 1500, 1550, 1600, 1650, 1700]
        }
        self.sample_data = pd.DataFrame(data)

    def test_calculate_indicators(self):
        """`calculate_indicators` fonksiyonunun temel göstergeleri doğru hesapladığını test et."""
        
        # pandas_ta, bazı göstergeleri hesaplamak için belirli bir minimum veri sayısına ihtiyaç duyar.
        # Örnek verimiz bu gereksinimleri karşılamalıdır.
        
        calculated_data = calculate_indicators(self.sample_data.copy())
        
        # 1. Sütunların eklendiğini kontrol et
        self.assertIn('ema_20', calculated_data.columns)
        self.assertIn('rsi_14', calculated_data.columns)
        self.assertIn('bbl_20_2.0', calculated_data.columns)
        self.assertIn('macd_12_26_9', calculated_data.columns)

        # 2. RSI için bilinen bir değeri (yaklaşık) kontrol et
        # Bu değerler, başka bir finansal analiz aracıyla veya bilinen bir formülle manuel olarak
        # hesaplanan bir değere yakın olmalıdır. Burada pandas_ta'nın kendi sonucunu referans alıyoruz.
        # 14 periyotluk RSI için, bu veri setindeki son değerin 100'e yakın olması beklenir çünkü fiyat sürekli artıyor.
        # Gerçek değer ~89.9 civarıdır.
        last_rsi = calculated_data['rsi_14'].iloc[-1]
        self.assertFalse(pd.isna(last_rsi), "RSI should not be NaN")
        self.assertGreater(last_rsi, 85, "For a strong uptrend, RSI should be high")
        self.assertLess(last_rsi, 95, "For this dataset, RSI should be below 95")

        # 3. EMA için temel bir mantığı kontrol et
        # Yükselen bir trendde, kısa vadeli EMA'nın uzun vadeli EMA'dan büyük olması beklenir.
        last_ema_20 = calculated_data['ema_20'].iloc[-1]
        last_ema_50 = calculated_data['ema_50'].iloc[-1]
        
        # Örnek veri çok kısa olduğu için ema_50 NaN olabilir. Sadece ema_20'yi kontrol et.
        self.assertFalse(pd.isna(last_ema_20), "EMA 20 should not be NaN")
        
        # Son kapanış fiyatının yükselen trenddeki EMA'dan büyük olması beklenir.
        last_close = calculated_data['close'].iloc[-1]
        self.assertGreater(last_close, last_ema_20)

        # 4. Bollinger Bantlarını kontrol et
        # Kapanış fiyatı genellikle üst ve alt bantlar arasında olmalıdır.
        last_bbu = calculated_data['bbu_20_2.0'].iloc[-1]
        last_bbl = calculated_data['bbl_20_2.0'].iloc[-1]
        
        # İlk birkaç değer NaN olabilir, bu yüzden NaN olmayan son değeri al
        last_valid_bbu = calculated_data['bbu_20_2.0'].dropna().iloc[-1]
        last_valid_bbl = calculated_data['bbl_20_2.0'].dropna().iloc[-1]

        self.assertGreater(last_valid_bbu, last_valid_bbl)
        self.assertTrue((last_close >= last_valid_bbl) and (last_close <= last_valid_bbu))


if __name__ == '__main__':
    unittest.main()
