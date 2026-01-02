import pandas as pd
import streamlit as st
from helpers.data_handler import get_fundamental_data
import numpy as np

# Bu dosya, hem Streamlit hem de Tkinter uygulamaları için metin tabanlı özetler üretir.


def generate_fundamental_summary(info, as_markdown=True):
    """Temel veriler için yorumlar ve anahtar bilgiler üretir."""
    summary_parts = []

    # Finansal Sağlık
    debt_to_equity = info.get("debtToEquity")
    current_ratio = info.get("currentRatio")
    if debt_to_equity is not None and current_ratio is not None:
        if debt_to_equity < 0.5 and current_ratio > 1.5:
            summary_parts.append(
                "Finansal Sağlık: Güçlü bir finansal yapıya işaret ediyor (Düşük borç, yüksek likidite)."
            )
        elif debt_to_equity < 1.0 and current_ratio > 1.0:
            summary_parts.append("Finansal Sağlık: Finansal durum dengeli görünüyor.")
        else:
            summary_parts.append(
                "Finansal Sağlık: Finansal riskler taşıyabilir (Yüksek borç veya düşük likidite)."
            )

    # Büyüme
    revenue_growth = info.get("revenueGrowth")
    earnings_growth = info.get("earningsGrowth")
    if revenue_growth is not None and earnings_growth is not None:
        if revenue_growth > 0.10 and earnings_growth > 0.15:
            summary_parts.append("Büyüme: Güçlü gelir ve kazanç büyümesi sergiliyor.")
        else:
            summary_parts.append("Büyüme: Büyüme oranları yavaş veya negatif.")

    # Değerleme
    trailing_pe = info.get("trailingPE")
    price_to_book = info.get("priceToBook")
    if trailing_pe is not None and price_to_book is not None:
        if trailing_pe < 15 and price_to_book < 2:
            summary_parts.append(
                "Değerleme: Göstergeler cazip bir değerlemeye işaret edebilir."
            )
        else:
            summary_parts.append(
                "Değerleme: Göstergeler şirketin pahalı olabileceğini gösteriyor."
            )

    # Karlılık
    return_on_equity = info.get("returnOnEquity")
    profit_margins = info.get("profitMargins")
    if return_on_equity is not None and profit_margins is not None:
        if return_on_equity > 0.15 and profit_margins > 0.10:
            summary_parts.append(
                "Karlılık: Yüksek özkaynak karlılığı ve güçlü net kar marjı."
            )
        else:
            summary_parts.append("Karlılık: Karlılık oranları düşük.")

    # Anahtar Bilgiler Metni
    key_info_map = {
        "longName": "Şirket Adı",
        "symbol": "Sembol",
        "sector": "Sektör",
        "marketCap": "Piyasa Değeri",
        "trailingPE": "F/K Oranı",
        "forwardPE": "Tahmini F/K",
        "priceToBook": "PD/DD",
        "dividendYield": "Temettü Verimi",
        "returnOnEquity": "Özkaynak Karlılığı",
        "profitMargins": "Net Kar Marjı",
    }
    key_info_text = ""
    for key, label in key_info_map.items():
        value = info.get(key, "N/A")
        if isinstance(value, (int, float)):
            if "Verim" in label or "Karlılık" in label or "Marjı" in label:
                key_info_text += f"{label:<25}: {value:.2%}\n"
            else:
                key_info_text += f"{label:<25}: {value:,.2f}\n"
        else:
            key_info_text += f"{label:<25}: {value}\n"

    if as_markdown:
        # Streamlit için Markdown formatı
        md_summary = [
            s.replace("Finansal Sağlık:", "**Finansal Sağlık:**")
            .replace("Büyüme:", "**Büyüme:**")
            .replace("Değerleme:", "**Değerleme:**")
            .replace("Karlılık:", "**Karlılık:**")
            for s in summary_parts
        ]
        return "\n\n".join(md_summary)
    else:
        # Tkinter için düz metin formatı
        return "\n".join(summary_parts), key_info_text


def generate_technical_summary(veri, as_markdown=True):
    """Teknik veriler için yorumlar üretir."""
    son_veri = veri.iloc[-1]
    summary = []

    # Genel Teknik Görünüm (EMA'lar)
    if "ema_50" in son_veri and "ema_200" in son_veri:
        if (
            son_veri["ema_50"] > son_veri["ema_200"]
            and son_veri["close"] > son_veri["ema_50"]
        ):
            summary.append(
                "Genel Görünüm: Güçlü Yükseliş Eğilimi (Fiyatlar EMA50 ve EMA200 üzerinde, EMA50 > EMA200)."
            )
        elif (
            son_veri["ema_50"] < son_veri["ema_200"]
            and son_veri["close"] < son_veri["ema_50"]
        ):
            summary.append(
                "Genel Görünüm: Güçlü Düşüş Eğilimi (Fiyatlar EMA50 ve EMA200 altında, EMA50 < EMA200)."
            )
        elif (
            son_veri["ema_50"] > son_veri["ema_200"]
            and son_veri["close"] < son_veri["ema_50"]
        ):
            summary.append(
                "Genel Görünüm: Yükseliş eğilimi zayıflıyor veya düzeltme yaşanıyor."
            )
        elif (
            son_veri["ema_50"] < son_veri["ema_200"]
            and son_veri["close"] > son_veri["ema_50"]
        ):
            summary.append(
                "Genel Görünüm: Düşüş eğilimi zayıflıyor veya toparlanma yaşanıyor."
            )
        else:
            summary.append("Genel Görünüm: Yatay veya belirsiz eğilim.")

    # RSI
    if "rsi_14" in son_veri:
        if son_veri["rsi_14"] > 70:
            summary.append(
                f"RSI ({son_veri['rsi_14']:.2f}): Aşırı alım bölgesinde, düzeltme veya düşüş riski olabilir."
            )
        elif son_veri["rsi_14"] < 30:
            summary.append(
                f"RSI ({son_veri['rsi_14']:.2f}): Aşırı satım bölgesinde, toparlanma veya yükseliş potansiyeli olabilir."
            )
        else:
            summary.append(f"RSI ({son_veri['rsi_14']:.2f}): Nötr bölgede.")

    # MACD
    if (
        "macd_12_26_9" in son_veri
        and "macds_12_26_9" in son_veri
        and "macdh_12_26_9" in son_veri
    ):
        if (
            son_veri["macd_12_26_9"] > son_veri["macds_12_26_9"]
            and son_veri["macdh_12_26_9"] > 0
        ):
            summary.append(
                "MACD: Pozitif bölgede ve sinyal çizgisinin üzerinde, yükseliş eğilimi devam ediyor."
            )
        elif (
            son_veri["macd_12_26_9"] < son_veri["macds_12_26_9"]
            and son_veri["macdh_12_26_9"] < 0
        ):
            summary.append(
                "MACD: Negatif bölgede ve sinyal çizgisinin altında, düşüş eğilimi devam ediyor."
            )
        else:
            summary.append("MACD: Yön belirsiz veya zayıf.")

    # ADX
    if "adx_14" in son_veri and "dmp_14" in son_veri and "dmn_14" in son_veri:
        if son_veri["adx_14"] > 25:
            if son_veri["dmp_14"] > son_veri["dmn_14"]:
                summary.append(
                    f"ADX ({son_veri['adx_14']:.2f}): Güçlü bir yükseliş trendi mevcut."
                )
            else:
                summary.append(
                    f"ADX ({son_veri['adx_14']:.2f}): Güçlü bir düşüş trendi mevcut."
                )
        else:
            summary.append(
                f"ADX ({son_veri['adx_14']:.2f}): Zayıf veya trendsiz piyasa."
            )

    # OBV
    if "obv" in son_veri:
        if len(veri["obv"]) > 1 and son_veri["obv"] > veri["obv"].iloc[-2]:
            summary.append(
                "OBV: Yükseliyor, alıcı baskısı artıyor ve mevcut trendi destekliyor."
            )
        elif len(veri["obv"]) > 1 and son_veri["obv"] < veri["obv"].iloc[-2]:
            summary.append(
                "OBV: Düşüyor, satıcı baskısı artıyor ve mevcut trendi zayıflatıyor."
            )
        else:
            summary.append("OBV: Yatay seyrediyor, belirsizlik mevcut.")

    # Bollinger Band Genişliği (BBW)
    if "bbb_20_2.0" in son_veri:
        # Ortalama BBW'yi tüm veri setinden al, son 20 periyot yerine
        mean_bbw = veri["bbb_20_2.0"].mean()
        if (
            son_veri["bbb_20_2.0"] > mean_bbw * 1.5
        ):  # Ortalama genişliğin 1.5 katından fazlaysa
            summary.append(
                f"Bollinger Band Genişliği ({son_veri['bbb_20_2.0']:.2f}): Yüksek volatiliteye işaret ediyor, büyük fiyat hareketleri beklenebilir."
            )
        elif (
            son_veri["bbb_20_2.0"] < mean_bbw * 0.5
        ):  # Ortalama genişliğin yarısından azsa
            summary.append(
                f"Bollinger Band Genişliği ({son_veri['bbb_20_2.0']:.2f}): Düşük volatiliteye işaret ediyor, sıkışma sonrası büyük fiyat hareketleri beklenebilir."
            )
        else:
            summary.append(
                f"Bollinger Band Genişliği ({son_veri['bbb_20_2.0']:.2f}): Normal seviyelerde, volatilite dengeli."
            )

    # Stokastik RSI
    if "stochrsik_14_14_3_3" in son_veri and "stochrsid_14_14_3_3" in son_veri:
        if (
            son_veri["stochrsik_14_14_3_3"] > 80
            and son_veri["stochrsik_14_14_3_3"] < son_veri["stochrsid_14_14_3_3"]
        ):
            summary.append(
                f"Stokastik RSI ({son_veri['stochrsik_14_14_3_3']:.2f}, {son_veri['stochrsid_14_14_3_3']:.2f}): Aşırı alım bölgesinde aşağı kesişim, düşüş sinyali olabilir."
            )
        elif (
            son_veri["stochrsik_14_14_3_3"] < 20
            and son_veri["stochrsik_14_14_3_3"] > son_veri["stochrsid_14_14_3_3"]
        ):
            summary.append(
                f"Stokastik RSI ({son_veri['stochrsik_14_14_3_3']:.2f}, {son_veri['stochrsid_14_14_3_3']:.2f}): Aşırı satım bölgesinde yukarı kesişim, yükseliş sinyali olabilir."
            )
        else:
            summary.append(
                f"Stokastik RSI ({son_veri['stochrsik_14_14_3_3']:.2f}, {son_veri['stochrsid_14_14_3_3']:.2f}): Nötr bölgede."
            )

    # Ichimoku Bulutu
    if "its_9" in son_veri and "kjs_26" in son_veri and "close" in son_veri:
        # NaN değerlerini kontrol et
        if not pd.isna(son_veri["its_9"]) and not pd.isna(son_veri["kjs_26"]):
            if son_veri["close"] > max(son_veri["its_9"], son_veri["kjs_26"]):
                summary.append(
                    "Ichimoku: Fiyat bulutun üzerinde, yükseliş eğilimi destekleniyor."
                )
            elif son_veri["close"] < min(son_veri["its_9"], son_veri["kjs_26"]):
                summary.append(
                    "Ichimoku: Fiyat bulutun altında, düşüş eğilimi destekleniyor."
                )
            else:
                summary.append(
                    "Ichimoku: Fiyat bulut içinde, belirsizlik veya konsolidasyon."
                )
        else:
            summary.append("Ichimoku: Ichimoku bulutu verileri eksik veya geçersiz.")

    if as_markdown:
        # Streamlit için Markdown formatı
        return "\n\n".join([f"- {s}" for s in summary])
    else:
        # Tkinter için düz metin formatı
        return "\n".join(summary)


def display_financial_ratios(info, financials, balance_sheet):
    """Hesaplanan finansal oranları bir DataFrame içinde gösterir."""
    ratios = {}

    # Değerleme Oranları
    ratios["Fiyat/Kazanç (F/K)"] = info.get("trailingPE")
    ratios["Piyasa Değeri/Defter Değeri (PD/DD)"] = info.get("priceToBook")
    ratios["Firma Değeri/FAVÖK (FD/FAVÖK)"] = info.get("enterpriseToEbitda")
    ratios["Fiyat/Satış (F/S)"] = info.get("priceToSalesTrailing12Months")

    # Karlılık Oranları
    ratios["Brüt Kar Marjı"] = info.get("grossMargins")
    ratios["Faaliyet Kar Marjı"] = info.get("operatingMargins")
    ratios["Net Kar Marjı"] = info.get("profitMargins")
    ratios["Özkaynak Karlılığı (ROE)"] = info.get("returnOnEquity")
    ratios["Aktif Karlılığı (ROA)"] = info.get("returnOnAssets")

    # Bilanço Oranları
    ratios["Cari Oran"] = info.get("currentRatio")
    ratios["Hızlı Oran"] = info.get("quickRatio")
    ratios["Toplam Borç/Özkaynak"] = info.get("debtToEquity")

    # Nakit Akış Oranları
    if (
        financials is not None
        and "Operating Cash Flow" in financials
        and "Capital Expenditure" in financials
    ):
        operating_cash_flow = (
            financials.loc["Operating Cash Flow"].iloc[0]
            if not financials.loc["Operating Cash Flow"].empty
            else 0
        )
        capital_expenditure = (
            financials.loc["Capital Expenditure"].iloc[0]
            if not financials.loc["Capital Expenditure"].empty
            else 0
        )
        free_cash_flow = (
            operating_cash_flow + capital_expenditure
        )  # CapEx is usually negative
        ratios["Serbest Nakit Akışı"] = free_cash_flow

    df_ratios = pd.DataFrame.from_dict(ratios, orient="index", columns=["Değer"])
    df_ratios.index.name = "Oran"
    return df_ratios


def display_sector_comparison(company_ratios, sector_averages):
    """
    Creates a DataFrame to compare a company's ratios with sector averages.
    """
    if sector_averages is None or sector_averages.empty:
        return None

    # Create a DataFrame from the company's ratios Series
    company_df = company_ratios.to_frame(name="Şirket Değeri")

    # Create a DataFrame for the comparison
    comparison_df = pd.DataFrame(index=sector_averages.index)
    comparison_df["Sektör Ortalaması"] = sector_averages
    comparison_df["Şirket Değeri"] = company_df["Şirket Değeri"]

    # Drop rows where both values are NaN and format the display
    comparison_df.dropna(how="all", inplace=True)

    # Highlight differences
    def highlight_diff(row):
        style = [""] * len(row)
        if pd.notna(row["Şirket Değeri"]) and pd.notna(row["Sektör Ortalaması"]):
            # For ratios where lower is better (like P/E, P/B), highlight green if company is lower
            if any(metric in row.name for metric in ["F/K", "PD/DD", "Borç/Özkaynak"]):
                if row["Şirket Değeri"] < row["Sektör Ortalaması"]:
                    style[0] = "background-color: #2a5c2a"  # Green
                else:
                    style[0] = "background-color: #6e2b2b"  # Red
            # For ratios where higher is better (like margins, ROE), highlight green if company is higher
            elif any(metric in row.name for metric in ["Marjı", "ROE"]):
                if row["Şirket Değeri"] > row["Sektör Ortalaması"]:
                    style[0] = "background-color: #2a5c2a"  # Green
                else:
                    style[0] = "background-color: #6e2b2b"  # Red
        return style

    return comparison_df.style.apply(highlight_diff, axis=1).format("{:.2f}")


def generate_ai_analysis(veri):
    """Daha akıllı ve detaylı yapay zeka destekli teknik analiz üretir."""
    if veri.empty or len(veri) < 2:
        return "Veri Yetersiz", {}

    son_veri = veri.iloc[-1]
    onceki_veri = veri.iloc[-2]

    # Sinyalleri ve skorları saklamak için yapılar
    trend_sinyalleri = {}
    momentum_sinyalleri = {}
    hacim_sinyalleri = {}
    
    # --- Trend Sinyalleri ---
    # EMA Trend
    ema_score = 0
    if son_veri['close'] > son_veri['ema_20']: ema_score += 1
    if son_veri['close'] > son_veri['ema_50']: ema_score += 1
    if son_veri['ema_50'] > son_veri['ema_200']: ema_score += 2 # Golden Cross durumu daha ağırlıklı
    trend_sinyalleri['EMA Trend'] = {'skor': ema_score, 'yorum': f"Fiyatın EMA'lara göre konumu ve EMA sıralaması (Skor: {ema_score})"}
    
    # SuperTrend
    st_skor = 0
    if 'supertd_7_3.0' in son_veri and not pd.isna(son_veri['supertd_7_3.0']):
        if son_veri['supertd_7_3.0'] == 1:
            st_skor = 2
            yorum = "SuperTrend 'Yükseliş' sinyali veriyor."
        else:
            st_skor = -2
            yorum = "SuperTrend 'Düşüş' sinyali veriyor."
        trend_sinyalleri['SuperTrend'] = {'skor': st_skor, 'yorum': yorum}

    # ADX Trend Gücü
    adx_skor = 0
    if son_veri['adx_14'] > 25:
        adx_skor = np.sign(son_veri['dmp_14'] - son_veri['dmn_14']) * 2
        yorum = f"ADX ({son_veri['adx_14']:.1f}) güçlü bir trende işaret ediyor. Yön: {'Pozitif' if adx_skor > 0 else 'Negatif'}. "
    else:
        yorum = f"ADX ({son_veri['adx_14']:.1f}) zayıf veya trendsiz bir piyasa gösteriyor."
    trend_sinyalleri['ADX'] = {'skor': adx_skor, 'yorum': yorum}

    # --- Momentum Sinyalleri ---
    # RSI
    rsi_skor = 0
    if son_veri['rsi_14'] > 70: rsi_skor = -2
    elif son_veri['rsi_14'] < 30: rsi_skor = 2
    elif son_veri['rsi_14'] > 50: rsi_skor = 1
    else: rsi_skor = -1
    momentum_sinyalleri['RSI'] = {'skor': rsi_skor, 'yorum': f"RSI değeri {son_veri['rsi_14']:.2f}. Aşırı alım/satım ve 50 çizgisine göre momentum (Skor: {rsi_skor})"}

    # MACD
    macd_skor = 0
    if son_veri['macd_12_26_9'] > son_veri['macds_12_26_9']: macd_skor += 1
    else: macd_skor -=1
    if son_veri['macdh_12_26_9'] > onceki_veri['macdh_12_26_9']: macd_skor += 1
    else: macd_skor -= 1
    momentum_sinyalleri['MACD'] = {'skor': macd_skor, 'yorum': f"MACD kesişimi ve histogram momentumu (Skor: {macd_skor})"}

    # Stokastik RSI
    stoch_skor = 0
    k, d = son_veri['stochrsik_14_14_3_3'], son_veri['stochrsid_14_14_3_3']
    prev_k, prev_d = onceki_veri['stochrsik_14_14_3_3'], onceki_veri['stochrsid_14_14_3_3']
    if k > d and prev_k < prev_d and k < 20: stoch_skor = 2 # Alım kesişimi
    elif k < d and prev_k > prev_d and k > 80: stoch_skor = -2 # Satım kesişimi
    momentum_sinyalleri['Stokastik RSI'] = {'skor': stoch_skor, 'yorum': f"Stokastik RSI {('alım' if stoch_skor > 0 else 'satım' if stoch_skor < 0 else 'nötr')} sinyali üretiyor (Skor: {stoch_skor})."}


    # --- Hacim ve Volatilite Sinyalleri ---
    # Hacim
    hacim_skor = 0
    if son_veri['volume'] > son_veri['volume_ma_20'] * 1.5: # Ortalamanın %50 üzerindeyse
        hacim_skor = np.sign(son_veri['close'] - onceki_veri['close']) # Fiyat artıyorsa pozitif, düşüyorsa negatif
        yorum = f"Hacim ortalamanın üzerinde ve fiyat {'yükseliyor' if hacim_skor > 0 else 'düşüyor'} "
    else:
        yorum = "Hacim normal seviyelerde."
    hacim_sinyalleri['Hacim'] = {'skor': hacim_skor, 'yorum': yorum}

    # Bollinger Bantları
    bb_skor = 0
    if son_veri['close'] > son_veri['bbu_20_2.0']: bb_skor = -1 # Direnç
    elif son_veri['close'] < son_veri['bbl_20_2.0']: bb_skor = 1 # Destek
    
    # BBW ile sıkışma kontrolü
    if 'bbw_20_2.0' in veri.columns and son_veri['bbw_20_2.0'] < veri['bbw_20_2.0'].quantile(0.1):
        yorum = f"Fiyat Bollinger bantları içinde. Bant genişliği çok düşük (sıkışma var)."
    else:
        yorum = f"Fiyat Bollinger bantları {'üstünde' if bb_skor < 0 else 'altında' if bb_skor > 0 else 'içinde'} "
    hacim_sinyalleri['Bollinger Bantları'] = {'skor': bb_skor, 'yorum': yorum}

    # --- Toplam Skor ve Sonuç ---
    toplam_skor = sum(s['skor'] for kat in [trend_sinyalleri, momentum_sinyalleri, hacim_sinyalleri] for s in kat.values())

    if toplam_skor >= 7:
        sonuc = "Güçlü Al"
    elif toplam_skor >= 3:
        sonuc = "Al"
    elif toplam_skor <= -7:
        sonuc = "Güçlü Sat"
    elif toplam_skor <= -3:
        sonuc = "Sat"
    else:
        sonuc = "Nötr"

    analiz_ozeti = {
        "Trend": [f"{k}: {v['yorum']}" for k, v in trend_sinyalleri.items()],
        "Momentum": [f"{k}: {v['yorum']}" for k, v in momentum_sinyalleri.items()],
        "Hacim ve Volatilite": [f"{k}: {v['yorum']}" for k, v in hacim_sinyalleri.items()],
    }

    return sonuc, analiz_ozeti

def display_key_metrics_comparison(hisse_list):
    """
    Fetches and displays a comparison table of key fundamental metrics for a list of stocks.
    """
    metrics_data = []
    
    st.subheader("Temel Metrikler Karşılaştırması")
    
    progress_text = "Temel metrikler çekiliyor..."
    progress_bar = st.progress(0, text=progress_text)
    
    for i, hisse in enumerate(hisse_list):
        hisse_yf = f"{hisse}.IS"
        try:
            data = get_fundamental_data(hisse_yf)
            if data and data.get("info"):
                info = data["info"]
                metrics = {
                    "Hisse": hisse,
                    "Piy. Değ. (mn)": info.get("marketCap", 0) / 1_000_000,
                    "F/K": info.get("trailingPE"),
                    "PD/DD": info.get("priceToBook"),
                    "Kâr Marjı (%)": info.get("profitMargins", 0) * 100,
                    "Özkaynak Kâr. (%)": info.get("returnOnEquity", 0) * 100,
                    "Borç/Özkaynak": info.get("debtToEquity"),
                }
                metrics_data.append(metrics)
            else:
                metrics_data.append({"Hisse": hisse, "F/K": "Veri Yok"})
        except Exception as e:
            st.warning(f"{hisse} için temel veriler alınırken hata oluştu: {e}")
            metrics_data.append({"Hisse": hisse, "F/K": "Hata"})
            
        progress_bar.progress((i + 1) / len(hisse_list), text=f"{progress_text} ({hisse} tamamlandı)")

    progress_bar.empty()

    if not metrics_data:
        st.warning("Karşılaştırma için hiçbir hisseden veri alınamadı.")
        return

    df = pd.DataFrame(metrics_data)
    df = df.set_index("Hisse")
    
    # Sütunları formatla
    st.dataframe(
        df.style.format({
            "Piy. Değ. (mn)": "{:,.0f}",
            "F/K": "{:.2f}",
            "PD/DD": "{:.2f}",
            "Kâr Marjı (%)": "{:.2f}%",
            "Özkaynak Kâr. (%)": "{:.2f}%",
            "Borç/Özkaynak": "{:.2f}",
        }).background_gradient(
            cmap='viridis', subset=["F/K", "PD/DD", "Borç/Özkaynak"]
        ).background_gradient(
            cmap='viridis_r', subset=["Kâr Marjı (%)", "Özkaynak Kâr. (%)"]
        )
    )