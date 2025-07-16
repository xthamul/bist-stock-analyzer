
import yfinance as yf
import pandas as pd
import numpy as np
from numpy import NaN as npNaN
import pandas_ta as ta
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
    veri.ta.ema(length=8, append=True, col_names=("EMA_8"))
    veri.ta.ema(length=13, append=True, col_names=("EMA_13"))
    veri.ta.ema(length=21, append=True, col_names=("EMA_21"))
    veri.ta.ema(length=50, append=True, col_names=("EMA_50"))
    veri.ta.ema(length=200, append=True, col_names=("EMA_200"))
    veri.ta.bbands(length=20, append=True)
    veri.ta.stochrsi(append=True)
    veri.ta.macd(append=True)
    veri.ta.rsi(append=True)
    veri.ta.adx(append=True)
    veri.ta.atr(append=True)
    veri.ta.obv(append=True)
    veri.ta.cdl_pattern(name="all", append=True)
    veri.ta.vwap(append=True)
    veri.ta.ichimoku(append=True)
    
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
