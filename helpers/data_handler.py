
import yfinance as yf
import pandas as pd
import numpy as np
import streamlit as st

@st.cache_data(ttl=3600) # Veriyi 1 saat boyunca cache'le
def get_stock_data(hisse_kodu, interval):
    """Belirtilen hisse senedi için yfinance'ten veri çeker."""
    period = "2y" if interval in ["1h", "4h"] else "max"
    veri = yf.download(hisse_kodu, period=period, interval=interval, progress=False, auto_adjust=False)
    if veri.empty:
        return None
    if isinstance(veri.columns, pd.MultiIndex):
        veri.columns = veri.columns.droplevel(1)
    veri.columns = [col.lower() for col in veri.columns]
    # İndeksi zaman dilimi bilgisinden arındır (VWAP uyarısını gidermek için)
    if veri.index.tz is not None:
        veri.index = veri.index.tz_localize(None)
    return veri

def calculate_indicators(veri):
    """Gerekli tüm teknik göstergeleri hesaplar."""
    def calculate_indicators(veri):
    """Gerekli tüm teknik göstergeleri manuel olarak hesaplar."""
    # EMA
    veri['ema_8'] = veri['close'].ewm(span=8, adjust=False).mean()
    veri['ema_13'] = veri['close'].ewm(span=13, adjust=False).mean()
    veri['ema_21'] = veri['close'].ewm(span=21, adjust=False).mean()
    veri['ema_50'] = veri['close'].ewm(span=50, adjust=False).mean()
    veri['ema_200'] = veri['close'].ewm(span=200, adjust=False).mean()

    # Bollinger Bantları
    veri['bbm_20_2.0'] = veri['close'].rolling(window=20).mean()
    veri['bb_std'] = veri['close'].rolling(window=20).std()
    veri['bbu_20_2.0'] = veri['bbm_20_2.0'] + (veri['bb_std'] * 2)
    veri['bbl_20_2.0'] = veri['bbm_20_2.0'] - (veri['bb_std'] * 2)
    veri['bbb_20_2.0'] = (veri['bbu_20_2.0'] - veri['bbl_20_2.0']) / veri['bbm_20_2.0'] * 100 # Bollinger Band Genişliği

    # RSI
    delta = veri['close'].diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    avg_gain = gain.ewm(span=14, adjust=False).mean()
    avg_loss = loss.ewm(span=14, adjust=False).mean()
    rs = avg_gain / avg_loss
    veri['rsi_14'] = 100 - (100 / (1 + rs))

    # MACD
    ema_12 = veri['close'].ewm(span=12, adjust=False).mean()
    ema_26 = veri['close'].ewm(span=26, adjust=False).mean()
    veri['macd_12_26_9'] = ema_12 - ema_26
    veri['macds_12_26_9'] = veri['macd_12_26_9'].ewm(span=9, adjust=False).mean()
    veri['macdh_12_26_9'] = veri['macd_12_26_9'] - veri['macds_12_26_9']

    # ATR
    high_low = veri['high'] - veri['low']
    high_prev_close = abs(veri['high'] - veri['close'].shift())
    low_prev_close = abs(veri['low'] - veri['close'].shift())
    tr = pd.DataFrame({'hl': high_low, 'hpc': high_prev_close, 'lpc': low_prev_close}).max(axis=1)
    veri['atr_14'] = tr.ewm(span=14, adjust=False).mean()
    veri['atrr_14'] = (veri['atr_14'] / veri['close']) * 100 # ATR % olarak

    # ADX
    # DM (Directional Movement)
    veri['up_move'] = veri['high'].diff()
    veri['down_move'] = veri['low'].diff() * -1
    veri['plus_dm'] = np.where((veri['up_move'] > veri['down_move']) & (veri['up_move'] > 0), veri['up_move'], 0)
    veri['minus_dm'] = np.where((veri['down_move'] > veri['up_move']) & (veri['down_move'] > 0), veri['down_move'], 0)

    # TR (True Range) - ATR hesaplamasından alınabilir
    veri['tr'] = tr # ATR hesaplamasındaki tr'yi kullan

    # Smooth DM ve TR
    veri['plus_dm_14'] = veri['plus_dm'].ewm(span=14, adjust=False).mean()
    veri['minus_dm_14'] = veri['minus_dm'].ewm(span=14, adjust=False).mean()
    veri['tr_14'] = veri['tr'].ewm(span=14, adjust=False).mean()

    # DI (Directional Indicator)
    veri['pdi_14'] = (veri['plus_dm_14'] / veri['tr_14']) * 100
    veri['mdi_14'] = (veri['minus_dm_14'] / veri['tr_14']) * 100

    # DX (Directional Index)
    veri['dx_14'] = abs(veri['pdi_14'] - veri['mdi_14']) / (veri['pdi_14'] + veri['mdi_14']) * 100

    # ADX
    veri['adx_14'] = veri['dx_14'].ewm(span=14, adjust=False).mean()
    veri['dmp_14'] = veri['pdi_14'] # +DI
    veri['dmn_14'] = veri['mdi_14'] # -DI

    # OBV
    veri['obv'] = (np.sign(veri['close'].diff()) * veri['volume']).fillna(0).cumsum()

    # StochRSI
    # RSI'ın kendisi üzerinde Stokastik hesapla
    min_rsi = veri['rsi_14'].rolling(window=14).min()
    max_rsi = veri['rsi_14'].rolling(window=14).max()
    veri['stochrsi'] = (veri['rsi_14'] - min_rsi) / (max_rsi - min_rsi)
    veri['stochrsik_14_14_3_3'] = veri['stochrsi'].rolling(window=3).mean() * 100
    veri['stochrsid_14_14_3_3'] = veri['stochrsik_14_14_3_3'].rolling(window=3).mean()

    # VWAP (Günlük VWAP)
    # Her gün için ayrı ayrı hesaplama
    veri['typical_price'] = (veri['high'] + veri['low'] + veri['close']) / 3
    veri['tp_volume'] = veri['typical_price'] * veri['volume']
    
    # Günlük bazda kümülatif toplamlar
    veri['cum_tp_volume'] = veri.groupby(veri.index.date)['tp_volume'].cumsum()
    veri['cum_volume'] = veri.groupby(veri.index.date)['volume'].cumsum()
    veri['vwap_d'] = veri['cum_tp_volume'] / veri['cum_volume']

    # Ichimoku Bulutu
    high_9 = veri['high'].rolling(window=9).max()
    low_9 = veri['low'].rolling(window=9).min()
    veri['itsa_9_26_52'] = (high_9 + low_9) / 2 # Tenkan-sen

    high_26 = veri['high'].rolling(window=26).max()
    low_26 = veri['low'].rolling(window=26).min()
    veri['itsb_9_26_52'] = (high_26 + low_26) / 2 # Kijun-sen

    veri['senkou_a'] = ((veri['itsa_9_26_52'] + veri['itsb_9_26_52']) / 2).shift(26) # Senkou Span A

    high_52 = veri['high'].rolling(window=52).max()
    low_52 = veri['low'].rolling(window=52).min()
    veri['senkou_b'] = ((high_52 + low_52) / 2).shift(26) # Senkou Span B

    veri['is_9_26_52'] = veri['close'].shift(-26) # Chikou Span

    # Sütun adlarını küçük harfe çevirerek tutarlılık sağla
    veri.columns = [col.lower() for col in veri.columns]
    return veri

@st.cache_data(ttl=3600)
def get_fundamental_data(hisse_kodu):
    """Hisse senedi için temel verileri ve finansal tabloları çeker."""
    try:
        stock = yf.Ticker(hisse_kodu)
        info = stock.info
        financials = stock.financials
        balance_sheet = stock.balance_sheet
        cashflow = stock.cashflow
        return {
            "info": info,
            "financials": financials,
            "balance_sheet": balance_sheet,
            "cashflow": cashflow
        }
    except Exception:
        return None

def filter_data_by_date(veri, start_date, end_date):
    """Veriyi seçilen tarih aralığına göre filtreler."""
    # DataFrame indeksinin zaman dilimi bilgisini kaldır (karşılaştırma için)
    if veri.index.tz is not None:
        veri.index = veri.index.tz_localize(None)

    # start_date ve end_date'i zaman dilimi bilgisi olmayan Timestamps'e dönüştür
    start_ts = pd.to_datetime(start_date)
    end_ts = pd.to_datetime(end_date)

    return veri[(veri.index >= start_ts) & (veri.index <= end_ts)].copy()

@st.cache_data(ttl=86400) # Günde bir kez cache'le
def get_sector_peers(hisse_kodu):
    """Bir hissenin sektörünü ve sektördeki benzer şirketleri bulur."""
    try:
        stock = yf.Ticker(hisse_kodu)
        info = stock.info
        sector = info.get('sector')
        if not sector:
            return None, None
        
        # Bu kısım normalde daha karmaşık bir API veya veri tabanı gerektirir.
        # yfinance doğrudan peer listesi vermediği için, BIST100 listesini 
        # sektör bazında filtreleyerek bir "yaklaşım" sergiliyoruz.
        # Gerçek bir uygulamada bu listenin daha güvenilir bir kaynaktan gelmesi gerekir.
        bist100 = [
            "AKBNK", "GARAN", "ISCTR", "YKBNK", "VAKBN", "THYAO", "ASELS", "TUPRS", "KCHOL", "BIMAS",
            "FROTO", "SISE", "ENKAI", "PETKM", "KOZAL", "TOASO", "KRDMD", "SAHOL", "SASA", "EREGL",
            "ARCLK", "PGSUS", "ALARK", "HEKTS", "TAVHL", "TCELL", "ODAS", "KORDS", "DOHOL", "ZOREN",
            "GWIND", "AGHOL", "AKSA", "OYAKC", "CCOLA", "TRKCM", "ADEL", "ULKER", "LOGO", "ISGYO",
            "MGROS", "GENIL", "ISDMR", "BRISA", "ALKIM", "AKGRT", "BANVT", "CIMSA", "ENJSA", "KARSN",
            "TTRAK", "GOZDE", "SOKM", "ALFAS", "BIOEN", "QUAGR", "BURCE", "DGNMO", "EKGYO", "GUBRF",
            "IZMDC", "MPARK", "NETAS", "PENTA", "TMSN", "TUCLK", "ULAS", "VERUS", "YUNSA"
        ]
        
        peers = []
        for peer_ticker in bist100:
            if peer_ticker != hisse_kodu.split('.')[0]:
                try:
                    peer_info = yf.Ticker(f"{peer_ticker}.IS").info
                    if peer_info.get('sector') == sector:
                        peers.append(peer_ticker)
                except Exception:
                    continue # Peer verisi alınamazsa atla
        return sector, peers
    except Exception:
        return None, None
