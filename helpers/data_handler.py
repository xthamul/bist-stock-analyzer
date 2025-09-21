import pandas_ta as ta
import yfinance as yf
import pandas as pd
import time
from datetime import datetime
from json import JSONDecodeError
import streamlit as st

from helpers.exceptions import DataFetchError
from constants import HISSE_GRUPPARI


def _flatten_columns(df):
    """
    Flattens MultiIndex columns to a single level of strings.
    """
    new_columns = []
    for col in df.columns:
        if isinstance(col, tuple):
            new_columns.append("_".join(filter(None, col)).strip("_"))
        else:
            new_columns.append(str(col))
    df.columns = new_columns
    return df


def get_stock_data(hisse_kodu, interval, end_date=None, retries=3, delay=5):
    """
    Belirtilen hisse senedi için yfinance'ten veri çeker.
    """
    print(f"Attempting to fetch data for {hisse_kodu} with interval {interval}")
    
    if end_date is None:
        end_date = datetime.today().strftime('%Y-%m-%d')

    for i in range(retries):
        try:
            veri = yf.download(
                hisse_kodu,
                start="1990-01-01",
                end=end_date,
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
    veri['ema_5'] = ta.ema(close=veri['close'], length=5)
    veri['ema_20'] = ta.ema(close=veri['close'], length=20)
    veri['ema_50'] = ta.ema(close=veri['close'], length=50)
    veri['ema_200'] = ta.ema(close=veri['close'], length=200)

    bbands = ta.bbands(close=veri['close'], length=20)
    veri['BBL_20_2.0'] = bbands['BBL_20_2.0']
    veri['BBM_20_2.0'] = bbands['BBM_20_2.0']
    veri['BBU_20_2.0'] = bbands['BBU_20_2.0']

    veri['rsi_14'] = ta.rsi(close=veri['close'], length=14)

    macd_data = ta.macd(close=veri['close'])
    veri['macd_12_26_9'] = macd_data['MACD_12_26_9']
    veri['macdh_12_26_9'] = macd_data['MACDh_12_26_9']
    veri['macds_12_26_9'] = macd_data['MACDs_12_26_9']

    veri["atr_14"] = ta.atr(high=veri['high'], low=veri['low'], close=veri['close'], length=14)

    adx_data = ta.adx(high=veri['high'], low=veri['low'], close=veri['close'], length=14)
    veri['adx_14'] = adx_data['ADX_14']
    veri['dmp_14'] = adx_data['DMP_14']
    veri['dmn_14'] = adx_data['DMN_14']

    veri['obv'] = ta.obv(close=veri['close'], volume=veri['volume'])

    stochrsi_data = ta.stochrsi(close=veri['close'])
    veri['STOCHRSIk_14_14_3_3'] = stochrsi_data['STOCHRSIk_14_14_3_3']
    veri['STOCHRSId_14_14_3_3'] = stochrsi_data['STOCHRSId_14_14_3_3']

    veri["typical_price"] = (veri["high"] + veri["low"] + veri["close"]) / 3
    veri["tp_volume"] = veri["typical_price"] * veri["volume"]
    veri["cum_tp_volume"] = veri.groupby(veri.index.date)["tp_volume"].cumsum()
    veri["cum_volume"] = veri.groupby(veri.index.date)["volume"].cumsum()
    veri["vwap_d"] = veri["cum_tp_volume"] / veri["cum_volume"]

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

    veri = _flatten_columns(veri)
    veri.columns = [col.lower() for col in veri.columns]
    veri["atrr_14"] = (veri["atr_14"] / veri["close"]) * 100

    veri['ema_50_prev'] = veri['ema_50'].shift(1)
    veri['ema_200_prev'] = veri['ema_200'].shift(1)

    veri['golden_cross'] = ((veri['ema_50_prev'] < veri['ema_200_prev']) &
                            (veri['ema_50'] > veri['ema_200']))

    veri['death_cross'] = ((veri['ema_50_prev'] > veri['ema_200_prev']) &
                           (veri['ema_50'] < veri['ema_200']))

    veri = veri.drop(columns=['ema_50_prev', 'ema_200_prev'])
    # veri = veri.dropna()
    return veri

def convert_dataframe_for_streamlit(df):
    if df is None:
        return df

    for col in df.columns:
        if pd.api.types.is_timedelta64_dtype(df[col]):
            df[col] = df[col].dt.total_seconds()

    if isinstance(df.index, pd.TimedeltaIndex):
        df.index = df.index.astype(str)

    return df

@st.cache_data(ttl=86400)
def get_fundamental_data(hisse_kodu, retries=3, delay=5):
    """Hisse senedi için temel verileri ve finansal tabloları çeker."""
    for i in range(retries):
        try:
            stock = yf.Ticker(hisse_kodu)
            info = stock.info
            if not info or info.get('quoteType') != 'EQUITY':
                raise DataFetchError(
                    f"{hisse_kodu} için temel veri bilgisi (info) alınamadı veya hisse senedi değil."
                )
            
            financials = stock.financials
            balance_sheet = stock.balance_sheet
            cashflow = stock.cashflow
            dividends = stock.dividends
            actions = stock.actions

            return {
                "info": info,
                "financials": financials,
                "balance_sheet": balance_sheet,
                "cashflow": cashflow,
                "dividends": dividends,
                "actions": actions,
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
        start_ts = pd.to_datetime(start_date).normalize()
        end_ts = pd.to_datetime(end_date).normalize() + pd.Timedelta(days=1)
        return veri[(veri.index >= start_ts) & (veri.index < end_ts)].copy()

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

            bist100 = HISSE_GRUPPARI["BIST 100 Hisseleri"]

            peers = []
            for peer_ticker in bist100:
                if peer_ticker != hisse_kodu.split(".")[0]:
                    try:
                        peer_info = yf.Ticker(f"{peer_ticker}.IS").info
                        time.sleep(0.2)
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

@st.cache_data(ttl=86400)
def get_sector_comparison_data(hisse_kodu):
    """Fetches key ratios for sector peers and calculates the average."""
    sector, peers = get_sector_peers(hisse_kodu)
    if not sector or not peers:
        return sector, None

    peer_ratios = []
    peers_to_process = peers[:15]
    
    progress_bar = st.progress(0, text=f"{sector} sektörü için benzer şirket verileri toplanıyor...")

    for i, peer_ticker in enumerate(peers_to_process):
        try:
            peer_info = yf.Ticker(f"{peer_ticker}.IS").info
            ratios = {
                'Hisse': peer_ticker,
                'F/K': peer_info.get('trailingPE'),
                'PD/DD': peer_info.get('priceToBook'),
                'Kâr Marjı': peer_info.get('profitMargins'),
                'FAVÖK Marjı': peer_info.get('ebitdaMargins'),
                'Borç/Özkaynak': peer_info.get('debtToEquity'),
            }
            peer_ratios.append(ratios)
            time.sleep(0.1)
        except Exception as e:
            print(f"Could not fetch data for peer {peer_ticker}: {e}")
        finally:
            progress_bar.progress((i + 1) / len(peers_to_process), text=f"{peer_ticker} verisi işlendi...")

    progress_bar.empty()

    if not peer_ratios:
        return sector, None

    df = pd.DataFrame(peer_ratios).set_index('Hisse')
    for col in df.columns:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    
    df.dropna(how='all', inplace=True)

    if df.empty:
        return sector, None

    return sector, df.mean()
