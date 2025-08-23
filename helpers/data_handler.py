import yfinance as yf
import pandas as pd
import time
from json import JSONDecodeError
import streamlit as st

# Tenacity (retry) kütüphanesine olan bağımlılık kaldırıldı.
# Bu fonksiyon artık sadece veri çekmeye odaklanıyor.
# Tekrar deneme mantığı, bu fonksiyonu çağıran uygulamalar (app.py, analiz.py) tarafından yönetilmelidir.
from helpers.exceptions import DataFetchError
from constants import HISSE_GRUPPARI  # HISSE_GRUPPARI import edildi


def _flatten_columns(df):
    """
    Flattens MultiIndex columns to a single level of strings.
    """
    new_columns = []
    for col in df.columns:
        if isinstance(col, tuple):
            # Join tuple elements with '_' and remove any trailing underscores
            new_columns.append("_".join(filter(None, col)).strip("_"))
        else:
            new_columns.append(str(col))
    df.columns = new_columns
    return df


@st.cache_data
def get_stock_data(hisse_kodu, interval, retries=3, delay=5):
    """Belirtilen hisse senedi için yfinance'ten veri çeker."""
    period = "2y" if interval in ["1h", "4h"] else "max"
    print(
        f"Attempting to fetch data for {hisse_kodu} with interval {interval} and period {period}"
    )
    for i in range(retries):
        try:
            veri = yf.download(
                hisse_kodu,
                period=period,
                interval=interval,
                progress=False,
                auto_adjust=False,
            )
            if not veri.empty:
                if isinstance(veri.columns, pd.MultiIndex):
                    veri.columns = veri.columns.droplevel(1)
                veri.columns = [col.lower() for col in veri.columns]
                if veri.index.tz is not None:
                    veri.index = veri.index.tz_localize(None)
                return veri
        except JSONDecodeError as e:
            print(
                f"Attempt {i+1}/{retries} failed for {hisse_kodu} with JSONDecodeError: {e}"
            )
            if i < retries - 1:
                time.sleep(delay)
        except Exception as e:
            print(f"Attempt {i+1}/{retries} failed for {hisse_kodu}: {e}")
            if i < retries - 1:
                time.sleep(delay)
    raise DataFetchError(f"{hisse_kodu} için yfinance'ten veri bulunamadı.")


@st.cache_data
def calculate_indicators(veri):
    """Gerekli tüm teknik göstergeleri pandas_ta kullanarak hesaplar."""
    # pandas_ta'nın beklediği sütun isimlerini kontrol et
    # Zaten get_stock_data içinde küçük harfe çevriliyor.

    # EMA'lar
    veri.ta.ema(length=8, append=True)
    veri.ta.ema(length=13, append=True)
    veri.ta.ema(length=21, append=True)
    veri.ta.ema(length=50, append=True)
    veri.ta.ema(length=200, append=True)

    # Bollinger Bantları
    veri.ta.bbands(length=20, append=True)

    # RSI
    veri.ta.rsi(length=14, append=True)

    # MACD
    veri.ta.macd(append=True)

    # ATR
    high_low = veri["high"] - veri["low"]
    high_prev_close = abs(veri["high"] - veri["close"].shift())
    low_prev_close = abs(veri["low"] - veri["close"].shift())
    tr = pd.DataFrame(
        {"hl": high_low, "hpc": high_prev_close, "lpc": low_prev_close}
    ).max(axis=1)
    veri["ATR_14"] = tr.ewm(span=14, adjust=False).mean()

    # ADX
    veri.ta.adx(length=14, append=True)

    # OBV
    veri.ta.obv(append=True)

    # StochRSI
    veri.ta.stochrsi(append=True)

    # VWAP (Günlük VWAP için pandas_ta'da doğrudan bir fonksiyon yok, manuel tutalım)
    # Ancak, app.py'deki prediction kısmında da VWAP kullanılıyor.
    # Şimdilik manuel VWAP hesaplamasını koruyalım veya kaldırıp sadece app.py'de kullanalım.
    # Mevcut manuel hesaplamayı koruyalım, çünkü pandas_ta'nın günlük VWAP'ı yok.
    veri["typical_price"] = (veri["high"] + veri["low"] + veri["close"]) / 3
    veri["tp_volume"] = veri["typical_price"] * veri["volume"]
    veri["cum_tp_volume"] = veri.groupby(veri.index.date)["tp_volume"].cumsum()
    veri["cum_volume"] = veri.groupby(veri.index.date)["volume"].cumsum()
    veri["vwap_d"] = veri["cum_tp_volume"] / veri["cum_volume"]

    # Ichimoku
    high_9 = veri["high"].rolling(window=9).max()
    low_9 = veri["low"].rolling(window=9).min()
    veri["its_9"] = (high_9 + low_9) / 2
    high_26 = veri["high"].rolling(window=26).max()
    low_26 = veri["low"].rolling(window=26).min()
    veri["kjs_26"] = (high_26 + low_26) / 2
    veri["isa_9"] = ((veri["its_9"] + veri["kjs_26"]) / 2).shift(26)
    high_52 = veri["high"].rolling(window=52).max()
    low_52 = veri["low"].rolling(window=52).min()
    veri["isb_26"] = ((high_52 + low_52) / 2).shift(26)
    veri["chk_26"] = veri["close"].shift(-26)

    # MultiIndex sütunları düzleştir (eğer varsa)
    veri = _flatten_columns(veri)

    # Tüm sütun adlarını küçük harfe çevir (pandas_ta zaten küçük harf döndürüyor olmalı ama emin olalım)
    veri.columns = [col.lower() for col in veri.columns]

    # ATR yüzdesini manuel hesapla (pandas_ta'da doğrudan yok)
    # Bu hesaplama, sütun adları küçük harfe çevrildikten sonra yapılmalı
    veri["atrr_14"] = (veri["atr_14"] / veri["close"]) * 100

    return veri


@st.cache_data
def get_fundamental_data(hisse_kodu, retries=3, delay=5):
    """Hisse senedi için temel verileri ve finansal tabloları çeker."""
    for i in range(retries):
        try:
            stock = yf.Ticker(hisse_kodu)
            info = stock.info
            if not info:
                raise DataFetchError(
                    f"{hisse_kodu} için temel veri bilgisi (info) alınamadı."
                )
            financials = stock.financials
            balance_sheet = stock.balance_sheet
            cashflow = stock.cashflow
            return {
                "info": info,
                "financials": financials,
                "balance_sheet": balance_sheet,
                "cashflow": cashflow,
            }
        except Exception as e:
            print(
                f"Attempt {i+1}/{retries} for fundamental data of {hisse_kodu} failed: {e}"
            )
            if i < retries - 1:
                time.sleep(delay)
    raise DataFetchError(f"{hisse_kodu} için temel veriler çekilemedi.")


def filter_data_by_date(veri, time_delta=None, start_date=None, end_date=None):
    """Veriyi seçilen tarih aralığına veya periyoda göre filtreler."""
    if veri.index.tz is not None:
        veri.index = veri.index.tz_localize(None)

    if time_delta is not None:
        start_ts = veri.index.max() - time_delta
        return veri[veri.index >= start_ts].copy()

    if start_date is not None and end_date is not None:
        start_ts = pd.to_datetime(start_date)
        end_ts = pd.to_datetime(end_date)
        return veri[(veri.index >= start_ts) & (veri.index <= end_ts)].copy()

    return veri


def get_sector_peers(hisse_kodu, retries=3, delay=2):
    """Bir hissenin sektörünü ve sektördeki benzer şirketleri bulur."""
    for i in range(retries):
        try:
            stock = yf.Ticker(hisse_kodu)
            info = stock.info
            if not info:
                print(f"Sektör bilgisi {hisse_kodu} için bulunamadı.")
                return None, None
            sector = info.get("sector")
            if not sector:
                print(f"Sektör bilgisi {hisse_kodu} için bulunamadı.")
                return None, None

            # Bu liste bir dış kaynaktan veya konfigürasyon dosyasından alınabilir.
            bist100 = HISSE_GRUPPARI["BIST 100 Hisseleri"]

            peers = []
            for peer_ticker in bist100:
                if peer_ticker != hisse_kodu.split(".")[0]:
                    try:
                        peer_info = yf.Ticker(f"{peer_ticker}.IS").info
                        time.sleep(0.2)  # API'ye saygılı olmak için küçük bir bekleme
                        if peer_info and peer_info.get("sector") == sector:
                            peers.append(peer_ticker)
                    except Exception:
                        print(f"Peer {peer_ticker} için bilgi alınamadı, atlanıyor.")
                        continue
            return sector, peers
        except Exception as e:
            print(
                f"Attempt {i+1}/{retries} for sector peers of {hisse_kodu} failed: {e}"
            )
            if i < retries - 1:
                time.sleep(delay)
    print(f"Sektör verileri {hisse_kodu} için tüm denemelerden sonra çekilemedi.")
    return None, None
