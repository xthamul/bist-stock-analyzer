import plotly.graph_objects as go
from plotly.subplots import make_subplots
import mplfinance as mpf
import pandas as pd
import numpy as np
from scipy.signal import find_peaks
import logging


def plot_candlestick_chart(veri, hisse_kodu, interval_display, analysis_type, selected_indicators, show_support_resistance, show_fibonacci=False):
    """Ana teknik analiz grafiğini oluşturur."""
    

    # Göstergelerin hangi alt grafiğe ait olduğunu ve başlıklarını tanımla
    indicator_subplot_map = {
        "RSI": ("RSI & StochRSI", 3),
        "StochRSI": ("RSI & StochRSI", 3),
        "MACD": ("MACD", 4),
        "ADX": ("ADX", 5),
        "OBV": ("OBV", 6),
    }

    # Alt grafikleri ve başlıkları dinamik olarak oluştur
    subplot_titles = ["Fiyat ve Göstergeler", "Hacim"]
    active_subplots = {1, 2}  # Fiyat ve Hacim her zaman aktif

    for indicator in selected_indicators:
        if indicator in indicator_subplot_map:
            title, row = indicator_subplot_map[indicator]
            if row not in active_subplots:
                subplot_titles.append(title)
                active_subplots.add(row)

    # Aktif subplot'ları sıralı hale getir ve yeni satır numaralarını map'le
    sorted_active_subplots = sorted(list(active_subplots))
    row_mapping = {
        old_row: new_row for new_row, old_row in enumerate(sorted_active_subplots, 1)
    }

    rows = len(active_subplots)
    row_heights = [0.6] + [0.1] * (rows - 1) if rows > 1 else [1.0]

    if analysis_type == "Basit":
        rows = 3
        row_heights = [0.6, 0.1, 0.1]
        subplot_titles = ["Fiyat ve Hareketli Ortalamalar", "Hacim", "RSI"]
        row_mapping = {1: 1, 2: 2, 3: 3}  # Basit mod için sabit map

    fig = make_subplots(
        rows=rows,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.03,
        row_heights=row_heights,
        subplot_titles=subplot_titles,
    )

    # Ana Grafik - Mumlar
    fig.add_trace(
        go.Candlestick(
            x=veri.index,
            open=veri["open"],
            high=veri["high"],
            low=veri["low"],
            close=veri["close"],
            name="Fiyat",
        ),
        row=1,
        col=1,
    )

    # Hacim
    fig.add_trace(
        go.Bar(x=veri.index, y=veri["volume"], name="Hacim", marker_color="grey"),
        row=row_mapping.get(2, 2),
        col=1,
    )

    # Göstergeler
    if analysis_type == "Basit":
        fig.add_trace(
            go.Scatter(
                x=veri.index, y=veri["ema_50"], name="EMA 50", line=dict(color="orange")
            ),
            row=1,
            col=1,
        )
        fig.add_trace(
            go.Scatter(
                x=veri.index,
                y=veri["ema_200"],
                name="EMA 200",
                line=dict(color="purple"),
            ),
            row=1,
            col=1,
        )
        fig.add_trace(
            go.Scatter(x=veri.index, y=veri["rsi_14"], name="RSI"), row=3, col=1
        )
        fig.add_hline(y=70, line_dash="dash", line_color="red", row=3, col=1)
        fig.add_hline(y=30, line_dash="dash", line_color="green", row=3, col=1)

    else:  # Detaylı
        # Fiyat paneli göstergeleri (her zaman ana panelde)
        

        if "EMA KISA (5, 20)" in selected_indicators:
            fig.add_trace(
                go.Scatter(
                    x=veri.index,
                    y=veri["ema_5"],
                    name="EMA 5",
                    line=dict(color="blue", width=1),
                ),
                row=1,
                col=1,
            )
            fig.add_trace(
                go.Scatter(
                    x=veri.index,
                    y=veri["ema_20"],
                    name="EMA 20",
                    line=dict(color="purple", width=1),
                ),
                row=1,
                col=1,
            )

        if "EMA UZUN (50, 200)" in selected_indicators:
            fig.add_trace(
                go.Scatter(
                    x=veri.index,
                    y=veri["ema_50"],
                    name="EMA 50",
                    line=dict(color="orange", width=1),
                ),
                row=1,
                col=1,
            )
            fig.add_trace(
                go.Scatter(
                    x=veri.index,
                    y=veri["ema_200"],
                    name="EMA 200",
                    line=dict(color="red", width=1),
                ),
                row=1,
                col=1,
            )

        if "Bollinger Bantları" in selected_indicators:
            fig.add_trace(
                go.Scatter(
                    x=veri.index,
                    y=veri["bbu_20_2.0"],
                    name="BB Üst",
                    line=dict(color="green", width=1, dash="dash"),
                ),
                row=1,
                col=1,
            )
            fig.add_trace(
                go.Scatter(
                    x=veri.index,
                    y=veri["bbl_20_2.0"],
                    name="BB Alt",
                    line=dict(color="red", width=1, dash="dash"),
                ),
                row=1,
                col=1,
            )

        if "VWAP" in selected_indicators:
            fig.add_trace(
                go.Scatter(
                    x=veri.index,
                    y=veri["vwap_d"],
                    name="VWAP",
                    line=dict(color="cyan", width=1.5, dash="dot"),
                ),
                row=1,
                col=1,
            )

        if "Ichimoku Cloud" in selected_indicators:
            fig.add_trace(
                go.Scatter(
                    x=veri.index,
                    y=veri["its_9"],
                    name="Tenkan-sen",
                    line=dict(color="#00bcd4", width=1),
                ),
                row=1,
                col=1,
            )
            fig.add_trace(
                go.Scatter(
                    x=veri.index,
                    y=veri["kjs_26"],
                    name="Kijun-sen",
                    line=dict(color="#ff9800", width=1.5),
                ),
                row=1,
                col=1,
            )
            fig.add_trace(
                go.Scatter(
                    x=veri.index,
                    y=veri["chk_26"],
                    name="Chikou Span",
                    line=dict(color="#e91e63", width=1.5, dash="dot"),
                ),
                row=1,
                col=1,
            )
            fig.add_trace(
                go.Scatter(
                    x=veri.index,
                    y=veri["isa_9"],
                    fill=None,
                    mode="lines",
                    line_color="rgba(0,255,0,0.1)",
                    name="Senkou A",
                ),
                row=1,
                col=1,
            )
            fig.add_trace(
                go.Scatter(
                    x=veri.index,
                    y=veri["isb_26"],
                    fill="tonexty",
                    mode="lines",
                    line_color="rgba(255,0,0,0.1)",
                    name="Senkou B",
                ),
                row=1,
                col=1,
            )

        # Alt panel göstergeleri
        if "RSI" in selected_indicators and 3 in row_mapping:
            rsi_row = row_mapping[3]
            fig.add_trace(
                go.Scatter(x=veri.index, y=veri["rsi_14"], name="RSI"),
                row=rsi_row,
                col=1,
            )
            fig.add_hline(y=70, line_dash="dash", line_color="red", row=rsi_row, col=1)
            fig.add_hline(
                y=30, line_dash="dash", line_color="green", row=rsi_row, col=1
            )

        if "StochRSI" in selected_indicators and 3 in row_mapping:
            stoch_row = row_mapping[3]
            fig.add_trace(
                go.Scatter(
                    x=veri.index,
                    y=veri["stochrsik_14_14_3_3"],
                    name="StochRSI K",
                    line=dict(color="cyan"),
                ),
                row=stoch_row,
                col=1,
            )
            fig.add_trace(
                go.Scatter(
                    x=veri.index,
                    y=veri["stochrsid_14_14_3_3"],
                    name="StochRSI D",
                    line=dict(color="magenta"),
                ),
                row=stoch_row,
                col=1,
            )

        if "MACD" in selected_indicators and 4 in row_mapping:
            macd_row = row_mapping[4]
            fig.add_trace(
                go.Scatter(
                    x=veri.index,
                    y=veri["macd_12_26_9"],
                    name="MACD",
                    line=dict(color="blue"),
                ),
                row=macd_row,
                col=1,
            )
            fig.add_trace(
                go.Scatter(
                    x=veri.index,
                    y=veri["macds_12_26_9"],
                    name="Signal",
                    line=dict(color="orange"),
                ),
                row=macd_row,
                col=1,
            )
            fig.add_trace(
                go.Bar(
                    x=veri.index,
                    y=veri["macdh_12_26_9"],
                    name="Histogram",
                    marker_color="grey",
                ),
                row=macd_row,
                col=1,
            )

        if "ADX" in selected_indicators and 5 in row_mapping:
            adx_row = row_mapping[5]
            fig.add_trace(
                go.Scatter(
                    x=veri.index,
                    y=veri["adx_14"],
                    name="ADX",
                    line=dict(color="#ffc107"),
                ),
                row=adx_row,
                col=1,
            )
            fig.add_trace(
                go.Scatter(
                    x=veri.index,
                    y=veri["dmp_14"],
                    name="+DI",
                    line=dict(color="#28a745"),
                ),
                row=adx_row,
                col=1,
            )
            fig.add_trace(
                go.Scatter(
                    x=veri.index,
                    y=veri["dmn_14"],
                    name="-DI",
                    line=dict(color="#dc3545"),
                ),
                row=adx_row,
                col=1,
            )

        if "OBV" in selected_indicators and 6 in row_mapping:
            obv_row = row_mapping[6]
            fig.add_trace(
                go.Scatter(x=veri.index, y=veri["obv"], name="OBV"), row=obv_row, col=1
            )

    # Support and Resistance Levels
    if show_support_resistance:
        try:
            # Find peaks and troughs with their properties
            peak_indices, peak_props = find_peaks(
                veri["high"], prominence=veri["high"].std() * 0.3, distance=15
            )
            trough_indices, trough_props = find_peaks(
                -veri["low"], prominence=veri["low"].std() * 0.3, distance=15
            )

            # Show markers for all detected peaks and troughs
            fig.add_trace(
                go.Scatter(
                    x=veri.index[peak_indices],
                    y=veri["high"].iloc[peak_indices],
                    mode="markers",
                    marker=dict(symbol="triangle-down", color="red", size=10),
                    name="Tepe",
                )
            )
            fig.add_trace(
                go.Scatter(
                    x=veri.index[trough_indices],
                    y=veri["low"].iloc[trough_indices],
                    mode="markers",
                    marker=dict(symbol="triangle-up", color="green", size=10),
                    name="Dip",
                )
            )

            # Get prominences and sort by them to find the most significant ones
            if len(peak_indices) > 0:
                peak_prominences = peak_props["prominences"]
                top_peak_indices = peak_indices[np.argsort(peak_prominences)[-3:]]
                for peak_idx in top_peak_indices:
                    level = veri["high"].iloc[peak_idx]
                    fig.add_hline(
                        y=level,
                        line_dash="dash",
                        line_color="rgba(255, 0, 0, 0.7)",
                        annotation_text=f"Direnç {level:.2f}",
                        annotation_position="bottom right",
                    )

            if len(trough_indices) > 0:
                trough_prominences = trough_props["prominences"]
                top_trough_indices = trough_indices[np.argsort(trough_prominences)[-3:]]
                for trough_idx in top_trough_indices:
                    level = veri["low"].iloc[trough_idx]
                    fig.add_hline(
                        y=level,
                        line_dash="dash",
                        line_color="rgba(0, 255, 0, 0.7)",
                        annotation_text=f"Destek {level:.2f}",
                        annotation_position="bottom right",
                    )

        except Exception as e:
            logging.warning(
                f"Destek/Direnç seviyeleri hesaplanırken bir hata oluştu: {e}"
            )

    # Fibonacci Geri Çekilme Seviyeleri
    if show_fibonacci:
        try:
            max_price = veri['high'].max()
            min_price = veri['low'].min()
            diff = max_price - min_price

            fib_levels = {
                "0%": max_price,
                "23.6%": max_price - 0.236 * diff,
                "38.2%": max_price - 0.382 * diff,
                "50%": max_price - 0.5 * diff,
                "61.8%": max_price - 0.618 * diff,
                "78.6%": max_price - 0.786 * diff,
                "100%": min_price,
            }

            colors = ["red", "orange", "yellow", "green", "blue", "indigo", "violet"]
            for i, (level_name, level_value) in enumerate(fib_levels.items()):
                fig.add_hline(
                    y=level_value,
                    line_dash="dot",
                    line_color=colors[i % len(colors)],
                    annotation_text=f"Fib {level_name} ({level_value:.2f})",
                    annotation_position="top right",
                    row=1, col=1
                )
        except Exception as e:
            logging.warning(f"Fibonacci seviyeleri hesaplanırken bir hata oluştu: {e}")

    # Golden Cross ve Death Cross işaretleri
    if "Golden/Death Cross" in selected_indicators:
        golden_cross_data = veri[veri['golden_cross']]
        death_cross_data = veri[veri['death_cross']]

        if not golden_cross_data.empty:
            fig.add_trace(
                go.Scatter(
                    x=golden_cross_data.index,
                    y=golden_cross_data['ema_50'], # veya 'close'
                    mode='markers+text',
                    marker=dict(symbol='triangle-up', size=15, color='green'),
                    text=['GC'] * len(golden_cross_data), # Kısa etiket
                    textposition='top center',
                    name='Golden Cross',
                    showlegend=True
                ),
                row=1, col=1
            )
            # Dikey çizgiler
            for date in golden_cross_data.index:
                fig.add_vline(x=date, line_width=1, line_dash="dash", line_color="green", row=1, col=1)

        if not death_cross_data.empty:
            fig.add_trace(
                go.Scatter(
                    x=death_cross_data.index,
                    y=death_cross_data['ema_50'], # veya 'close'
                    mode='markers+text',
                    marker=dict(symbol='triangle-down', size=15, color='red'),
                    text=['DC'] * len(death_cross_data), # Kısa etiket
                    textposition='bottom center',
                    name='Death Cross',
                    showlegend=True
                ),
                row=1, col=1
            )
            # Dikey çizgiler
            for date in death_cross_data.index:
                fig.add_vline(x=date, line_width=1, line_dash="dash", line_color="red", row=1, col=1)

    fig.update_layout(
        title=f"{hisse_kodu} Teknik Analiz ({interval_display} - {analysis_type})",
        height=250 * rows,  # Yüksekliği dinamik yap
        xaxis_rangeslider_visible=False,
        legend_orientation="h",
        legend_yanchor="bottom",
        legend_y=1.02,
        legend_xanchor="right",
        legend_x=1,
        template="plotly_dark",
    )
    fig.update_xaxes(showticklabels=True)
    return fig


def plot_comparison_plotly(data1, data2, hisse1, hisse2):
    """İki hissenin normalize edilmiş fiyat performansını karşılaştırır."""
    # Fiyatları başlangıç noktasına göre normalize et (Yüzdesel Değişim)
    norm_data1 = (data1["close"] / data1["close"].iloc[0] - 1) * 100
    norm_data2 = (data2["close"] / data2["close"].iloc[0] - 1) * 100

    fig = go.Figure()

    fig.add_trace(
        go.Scatter(x=norm_data1.index, y=norm_data1, name=hisse1, line=dict(width=2))
    )
    fig.add_trace(
        go.Scatter(x=norm_data2.index, y=norm_data2, name=hisse2, line=dict(width=2))
    )

    fig.update_layout(
        title=f"{hisse1} vs. {hisse2} Normalize Edilmiş Performans",
        yaxis_title="Yüzdesel Değişim (%)",
        height=600,
        template="plotly_dark",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    fig.update_yaxes(zeroline=True, zerolinewidth=2, zerolinecolor="Gray")

    return fig


def plot_analysis_mpl(veri, hisse_kodu, interval_display, analysis_type):
    """Matplotlib/mplfinance kullanarak teknik analiz grafiği oluşturur."""
    veri.index.name = "Date"
    apds = []  # addplot listesi

    # Panelleri ve oranları dinamik olarak ayarla
    if analysis_type == "Basit":
        apds.extend(
            [
                mpf.make_addplot(veri["EMA_50"], color="orange", panel=0),
                mpf.make_addplot(veri["EMA_200"], color="purple", panel=0),
                mpf.make_addplot(
                    veri["volume"], panel=1, type="bar", color="gray", ylabel="Hacim"
                ),
                mpf.make_addplot(veri["RSI_14"], panel=2, color="blue", ylabel="RSI"),
                mpf.make_addplot(
                    pd.Series(70, index=veri.index),
                    panel=2,
                    color="gray",
                    linestyle="--",
                    width=0.7,
                ),
                mpf.make_addplot(
                    pd.Series(30, index=veri.index),
                    panel=2,
                    color="gray",
                    linestyle="--",
                    width=0.7,
                ),
            ]
        )
        panel_ratios = (3, 1, 1)
    else:  # Detaylı
        apds.extend(
            [
                # Panel 0: Fiyat ve Ortalamalar
                mpf.make_addplot(veri["ema_5"], color="#007bff", panel=0),
                mpf.make_addplot(veri["ema_20"], color="#6f42c1", panel=0),
                mpf.make_addplot(veri["ema_50"], color="#fd7e14", panel=0),
                mpf.make_addplot(veri["ema_200"], color="#ff00ff", panel=0),
                mpf.make_addplot(
                    veri["BBL_20_2.0"], color="#28a745", linestyle="--", panel=0
                ),
                mpf.make_addplot(
                    veri["BBU_20_2.0"], color="#dc3545", linestyle="--", panel=0
                ),
                mpf.make_addplot(veri["vwap_d"], color="cyan", linestyle="-.", panel=0),
                # Ichimoku Bulutu
                mpf.make_addplot(veri["its_9"], color="#00bcd4", panel=0),
                mpf.make_addplot(veri["kjs_26"], color="#ff9800", panel=0),
                mpf.make_addplot(
                    veri["chk_26"], color="#e91e63", linestyle="dotted", panel=0
                ),
                mpf.make_addplot(
                    veri["isa_9"],
                    color="rgba(0,255,0,0.1)",
                    panel=0,
                    fill_between=dict(y2=veri["isb_26"], color="rgba(255,0,0,0.1)"),
                ),
                mpf.make_addplot(veri["isb_26"], color="rgba(255,0,0,0.1)", panel=0),
                # Panel 1: Hacim
                mpf.make_addplot(
                    veri["volume"], panel=1, type="bar", color="gray", ylabel="Hacim"
                ),
                # Panel 2: RSI & StochRSI
                mpf.make_addplot(
                    veri["RSI_14"], panel=2, color="blue", ylabel="RSI/Stoch"
                ),
                mpf.make_addplot(
                    pd.Series(70, index=veri.index),
                    panel=2,
                    color="gray",
                    linestyle="--",
                    width=0.7,
                ),
                mpf.make_addplot(
                    pd.Series(30, index=veri.index),
                    panel=2,
                    color="gray",
                    linestyle="--",
                    width=0.7,
                ),
                mpf.make_addplot(veri["STOCHRSIk_14_14_3_3"], panel=2, color="cyan"),
                mpf.make_addplot(veri["STOCHRSId_14_14_3_3"], panel=2, color="magenta"),
                # Panel 3: MACD
                mpf.make_addplot(
                    veri["MACD_12_26_9"], panel=3, color="blue", ylabel="MACD"
                ),
                mpf.make_addplot(veri["MACDS_12_26_9"], panel=3, color="orange"),
                mpf.make_addplot(
                    veri["MACDH_12_26_9"], type="bar", panel=3, color="gray"
                ),
                # Panel 4: ADX
                mpf.make_addplot(
                    veri["ADX_14"], panel=4, color="#ffc107", ylabel="ADX"
                ),
                mpf.make_addplot(veri["DMP_14"], panel=4, color="#28a745"),
                mpf.make_addplot(veri["DMN_14"], panel=4, color="#dc3545"),
                # Panel 5: OBV
                mpf.make_addplot(veri["OBV"], panel=5, color="#ffc107", ylabel="OBV"),
            ]
        )
        panel_ratios = (6, 1, 2, 2, 2, 2)

    s = mpf.make_mpf_style(base_mpf_style="yahoo", rc={"figure.facecolor": "white"})
    fig, axes = mpf.plot(
        veri,
        type="candle",
        style=s,
        title=f"{hisse_kodu} Teknik Analiz ({interval_display} - {analysis_type})",
        ylabel="Fiyat",
        volume=False,  # Hacim ayrı panelde
        addplot=apds,
        panel_ratios=panel_ratios,
        figscale=1.5,
        returnfig=True,
        columns=["open", "high", "low", "close", "volume"],
    )
    return fig, axes


def plot_financial_trends(financials, cashflow):
    """Gelir tablosu ve nakit akışı trendlerini gösteren bir grafik oluşturur."""
    # yfinance verileri genellikle en son yılı ilk sütun olarak verir, bu yüzden ters çeviriyoruz
    financials = financials.iloc[:, ::-1]
    cashflow = cashflow.iloc[:, ::-1]

    fig = make_subplots(
        rows=2,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.1,
        subplot_titles=("Yıllık Gelir ve Kar Trendi", "Yıllık Nakit Akışı Trendi"),
    )

    # Gelir ve Kar Trendi
    if "Total Revenue" in financials.index and "Net Income" in financials.index:
        fig.add_trace(
            go.Bar(
                x=financials.columns,
                y=financials.loc["Total Revenue"],
                name="Toplam Gelir",
            ),
            row=1,
            col=1,
        )
        fig.add_trace(
            go.Scatter(
                x=financials.columns,
                y=financials.loc["Net Income"],
                name="Net Kar",
                mode="lines+markers",
            ),
            row=1,
            col=1,
        )

    # Nakit Akışı Trendi
    if (
        "Operating Cash Flow" in cashflow.index
        and "Capital Expenditure" in cashflow.index
    ):
        operating_cash_flow = cashflow.loc["Operating Cash Flow"]
        capital_expenditure = cashflow.loc["Capital Expenditure"]
        free_cash_flow = operating_cash_flow + capital_expenditure
        fig.add_trace(
            go.Bar(
                x=cashflow.columns, y=operating_cash_flow, name="Faaliyet Nakit Akışı"
            ),
            row=2,
            col=1,
        )
        fig.add_trace(
            go.Scatter(
                x=cashflow.columns,
                y=free_cash_flow,
                name="Serbest Nakit Akışı",
                mode="lines+markers",
            ),
            row=2,
            col=1,
        )

    fig.update_layout(
        height=600,
        template="plotly_dark",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    return fig


def plot_prediction_results(test_results, close_prices):
    """Tahmin sonuçlarını görselleştirir."""
    fig = go.Figure()

    # Gerçek kapanış fiyatları
    fig.add_trace(
        go.Scatter(
            x=close_prices.index,
            y=close_prices,
            name="Gerçek Kapanış Fiyatı",
            line=dict(color="blue"),
        )
    )

    # Doğru tahminler için yeşil, yanlış tahminler için kırmızı noktalar
    correct_predictions = test_results[
        test_results["actual"] == test_results["predicted"]
    ]
    incorrect_predictions = test_results[
        test_results["actual"] != test_results["predicted"]
    ]

    fig.add_trace(
        go.Scatter(
            x=correct_predictions.index,
            y=close_prices.loc[correct_predictions.index],
            mode="markers",
            name="Doğru Tahmin",
            marker=dict(color="green", size=8, symbol="circle"),
        )
    )
    fig.add_trace(
        go.Scatter(
            x=incorrect_predictions.index,
            y=close_prices.loc[incorrect_predictions.index],
            mode="markers",
            name="Yanlış Tahmin",
            marker=dict(color="red", size=8, symbol="x"),
        )
    )

    fig.update_layout(
        title="Model Tahminlerinin Görselleştirilmesi",
        xaxis_title="Tarih",
        yaxis_title="Fiyat",
        height=600,
        template="plotly_dark",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    return fig


def plot_backtesting_results(equity_curve, signals, data, strategy_name, initial_cash):
    """Backtesting sonuçlarını görselleştiren bir grafik oluşturur."""
    fig = make_subplots(
        rows=2,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.05,
        row_heights=[0.7, 0.3],
        subplot_titles=(
            f"{strategy_name} Stratejisi - Varlık Eğrisi ve İşlemler",
            "Sinyaller",
        ),
    )

    # Panel 1: Varlık Eğrisi ve Fiyat
    fig.add_trace(
        go.Scatter(
            x=equity_curve.index,
            y=equity_curve,
            name="Varlık Değeri",
            line=dict(color="blue"),
        ),
        row=1,
        col=1,
    )
    fig.add_trace(
        go.Scatter(
            x=data.index,
            y=data["close"],
            name="Kapanış Fiyatı",
            line=dict(color="grey", dash="dot"),
            opacity=0.7,
        ),
        row=1,
        col=1,
    )

    # Alış ve Satış Sinyallerini İşaretle
    buy_signals = signals[signals["signal"] == 1]
    sell_signals = signals[signals["signal"] == -1]

    fig.add_trace(
        go.Scatter(
            x=buy_signals.index,
            y=data.loc[buy_signals.index]["close"],
            mode="markers",
            marker=dict(symbol="triangle-up", color="green", size=10),
            name="Alış Sinyali",
        ),
        row=1,
        col=1,
    )
    fig.add_trace(
        go.Scatter(
            x=sell_signals.index,
            y=data.loc[sell_signals.index]["close"],
            mode="markers",
            marker=dict(symbol="triangle-down", color="red", size=10),
            name="Satış Sinyali",
        ),
        row=1,
        col=1,
    )

    # Panel 2: Sinyaller
    fig.add_trace(
        go.Scatter(
            x=signals.index,
            y=signals["signal"],
            name="Sinyal Değeri",
            line=dict(color="orange"),
        ),
        row=2,
        col=1,
    )

    fig.update_layout(
        title=f"Backtesting Sonuçları: {strategy_name}",
        height=800,
        template="plotly_dark",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    fig.update_yaxes(title_text="Varlık Değeri (TL)", row=1, col=1)
    fig.update_yaxes(title_text="Sinyal (1: Al, -1: Sat)", row=2, col=1)

    return fig


def plot_balance_sheet_details(balance_sheet):
    """Creates a stacked bar chart for balance sheet composition."""
    # yfinance usually has years as columns, most recent first. Reverse for chronological order.
    df = balance_sheet.iloc[:, ::-1]
    
    # Select key asset and liability items that are commonly available
    asset_items = ['Cash And Cash Equivalents', 'Receivables', 'Inventory', 'Other Current Assets', 'Net Ppe', 'Other Non Current Assets']
    liability_items = ['Accounts Payable', 'Other Current Liabilities', 'Long Term Debt', 'Other Non Current Liabilities']
    
    # Filter items that exist in the dataframe
    asset_items = [item for item in asset_items if item in df.index]
    liability_items = [item for item in liability_items if item in df.index]

    if not asset_items and not liability_items:
        return go.Figure().update_layout(title_text="Detaylı Bilanço Verisi Bulunamadı", template='plotly_dark')

    fig = make_subplots(rows=1, cols=2, subplot_titles=('Varlıkların Dağılımı', 'Yükümlülüklerin Dağılımı'))

    # Assets
    for item in asset_items:
        fig.add_trace(go.Bar(name=item, x=df.columns.year, y=df.loc[item], text=df.loc[item]), row=1, col=1)
        
    # Liabilities
    for item in liability_items:
        fig.add_trace(go.Bar(name=item, x=df.columns.year, y=df.loc[item], text=df.loc[item]), row=1, col=2)

    fig.update_layout(barmode='stack', title_text='Detaylı Bilanço Analizi', template='plotly_dark', height=500)
    fig.update_traces(texttemplate='%{y:.2s}', textposition='inside')
    return fig

def plot_per_share_values(financials, balance_sheet, info):
    """Calculates and plots EPS and Book Value Per Share."""
    shares_outstanding = info.get('sharesOutstanding')
    if not shares_outstanding:
        return go.Figure().update_layout(title_text="Hisse Sayısı Bilgisi Bulunamadığı İçin Hisse Başına Değerler Hesaplanamadı", template='plotly_dark')

    fin_df = financials.iloc[:, ::-1]
    bs_df = balance_sheet.iloc[:, ::-1]
    
    eps = pd.Series(dtype='float64')
    if 'Net Income' in fin_df.index:
        eps = fin_df.loc['Net Income'] / shares_outstanding

    bvps = pd.Series(dtype='float64')
    if 'Total Stockholder Equity' in bs_df.index:
        bvps = bs_df.loc['Total Stockholder Equity'] / shares_outstanding

    if eps.empty and bvps.empty:
        return go.Figure().update_layout(title_text="Hisse Başına Değerler Hesaplanamadı", template='plotly_dark')

    fig = make_subplots(rows=1, cols=2, subplot_titles=('Hisse Başına Kâr (EPS)', 'Hisse Başına Defter Değeri (BVPS)'))

    if not eps.empty:
        fig.add_trace(go.Bar(name='EPS', x=eps.index.year, y=eps, text=eps), row=1, col=1)
    if not bvps.empty:
        fig.add_trace(go.Bar(name='BVPS', x=bvps.index.year, y=bvps, text=bvps), row=1, col=2)

    fig.update_layout(title_text='Hisse Başına Değerlerin Yıllık Değişimi', template='plotly_dark', height=400)
    fig.update_traces(texttemplate='%{y:.2f}', textposition='auto')
    return fig

def plot_dividend_history(dividends):
    """Creates a bar chart of historical dividend payments."""
    if dividends is None or dividends.empty:
        return go.Figure().update_layout(title_text="Şirketin Geçmiş Temettü Ödemesi Bulunmamaktadır", template='plotly_dark')

    fig = go.Figure()
    fig.add_trace(go.Bar(x=dividends.index, y=dividends, name='Hisse Başına Temettü'))
    
    fig.update_layout(
        title_text='Yıllara Göre Hisse Başına Temettü Ödemeleri (TL)',
        xaxis_title='Tarih',
        yaxis_title='Temettü (TL)',
        template='plotly_dark',
        height=400
    )
    return fig