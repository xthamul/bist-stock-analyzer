import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from scipy.signal import find_peaks
import logging
import streamlit as st


def plot_candlestick_chart(
    veri,
    hisse_kodu,
    interval_display,
    analysis_type,
    selected_indicators,
    show_support_resistance,
    show_fibonacci=False,
):
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

        if "Super Trend" in selected_indicators:
            fig.add_trace(
                go.Scatter(
                    x=veri.index,
                    y=veri["supertl_7_3.0"],
                    name="Super Trend Long",
                    line=dict(color="green", width=2),
                ),
                row=1,
                col=1,
            )
            fig.add_trace(
                go.Scatter(
                    x=veri.index,
                    y=veri["superts_7_3.0"],
                    name="Super Trend Short",
                    line=dict(color="red", width=2),
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
            max_price = veri["high"].max()
            min_price = veri["low"].min()
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
                    row=1,
                    col=1,
                )
        except Exception as e:
            logging.warning(f"Fibonacci seviyeleri hesaplanırken bir hata oluştu: {e}")

    # Golden Cross ve Death Cross işaretleri
    if "Golden/Death Cross" in selected_indicators:
        golden_cross_data = veri[veri["golden_cross"]]
        death_cross_data = veri[veri["death_cross"]]

        if not golden_cross_data.empty:
            fig.add_trace(
                go.Scatter(
                    x=golden_cross_data.index,
                    y=golden_cross_data["ema_50"],  # veya 'close'
                    mode="markers+text",
                    marker=dict(symbol="triangle-up", size=15, color="green"),
                    text=["GC"] * len(golden_cross_data),  # Kısa etiket
                    textposition="top center",
                    name="Golden Cross",
                    showlegend=True,
                ),
                row=1,
                col=1,
            )
            # Dikey çizgiler
            for date in golden_cross_data.index:
                fig.add_vline(
                    x=date,
                    line_width=1,
                    line_dash="dash",
                    line_color="green",
                    row=1,
                    col=1,
                )

        if not death_cross_data.empty:
            fig.add_trace(
                go.Scatter(
                    x=death_cross_data.index,
                    y=death_cross_data["ema_50"],  # veya 'close'
                    mode="markers+text",
                    marker=dict(symbol="triangle-down", size=15, color="red"),
                    text=["DC"] * len(death_cross_data),  # Kısa etiket
                    textposition="bottom center",
                    name="Death Cross",
                    showlegend=True,
                ),
                row=1,
                col=1,
            )
            # Dikey çizgiler
            for date in death_cross_data.index:
                fig.add_vline(
                    x=date,
                    line_width=1,
                    line_dash="dash",
                    line_color="red",
                    row=1,
                    col=1,
                )

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


def display_candlestick_chart(
    veri,
    hisse_kodu,
    interval_display,
    analysis_type,
    selected_indicators,
    show_support_resistance,
    show_fibonacci=False,
):
    """Generates and displays the candlestick chart in Streamlit."""
    fig = plot_candlestick_chart(
        veri,
        hisse_kodu,
        interval_display,
        analysis_type,
        selected_indicators,
        show_support_resistance,
        show_fibonacci,
    )
    st.plotly_chart(fig, use_container_width=True)


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


def display_financial_trends_chart(financials, cashflow):
    """Generates and displays the financial trends chart in Streamlit."""
    fig = plot_financial_trends(financials, cashflow)
    st.plotly_chart(fig, use_container_width=True)


def plot_balance_sheet_details(balance_sheet):
    """Creates a stacked bar chart for balance sheet composition."""
    # yfinance usually has years as columns, most recent first. Reverse for chronological order.
    df = balance_sheet.iloc[:, ::-1]

    # Select key asset and liability items that are commonly available
    asset_items = [
        "Cash And Cash Equivalents",
        "Receivables",
        "Inventory",
        "Other Current Assets",
        "Net Ppe",
        "Other Non Current Assets",
    ]
    liability_items = [
        "Accounts Payable",
        "Other Current Liabilities",
        "Long Term Debt",
        "Other Non Current Liabilities",
    ]

    # Filter items that exist in the dataframe
    asset_items = [item for item in asset_items if item in df.index]
    liability_items = [item for item in liability_items if item in df.index]

    if not asset_items and not liability_items:
        return go.Figure().update_layout(
            title_text="Detaylı Bilanço Verisi Bulunamadı", template="plotly_dark"
        )

    fig = make_subplots(
        rows=1,
        cols=2,
        subplot_titles=("Varlıkların Dağılımı", "Yükümlülüklerin Dağılımı"),
    )

    # Assets
    for item in asset_items:
        fig.add_trace(
            go.Bar(name=item, x=df.columns.year, y=df.loc[item], text=df.loc[item]),
            row=1,
            col=1,
        )

    # Liabilities
    for item in liability_items:
        fig.add_trace(
            go.Bar(name=item, x=df.columns.year, y=df.loc[item], text=df.loc[item]),
            row=1,
            col=2,
        )

    fig.update_layout(
        barmode="stack",
        title_text="Detaylı Bilanço Analizi",
        template="plotly_dark",
        height=500,
    )
    fig.update_traces(texttemplate="%{y:.2s}", textposition="inside")
    return fig


def display_balance_sheet_details_chart(balance_sheet):
    """Generates and displays the balance sheet details chart in Streamlit."""
    fig = plot_balance_sheet_details(balance_sheet)
    st.plotly_chart(fig, use_container_width=True)


def plot_per_share_values(financials, balance_sheet, info):
    """Calculates and plots EPS and Book Value Per Share."""
    shares_outstanding = info.get("sharesOutstanding")
    if not shares_outstanding:
        return go.Figure().update_layout(
            title_text="Hisse Sayısı Bilgisi Bulunamadığı İçin Hisse Başına Değerler Hesaplanamadı",
            template="plotly_dark",
        )

    fin_df = financials.iloc[:, ::-1]
    bs_df = balance_sheet.iloc[:, ::-1]

    eps = pd.Series(dtype="float64")
    if "Net Income" in fin_df.index:
        eps = fin_df.loc["Net Income"] / shares_outstanding

    bvps = pd.Series(dtype="float64")
    if "Total Stockholder Equity" in bs_df.index:
        bvps = bs_df.loc["Total Stockholder Equity"] / shares_outstanding

    if eps.empty and bvps.empty:
        return go.Figure().update_layout(
            title_text="Hisse Başına Değerler Hesaplanamadı", template="plotly_dark"
        )

    fig = make_subplots(
        rows=1,
        cols=2,
        subplot_titles=("Hisse Başına Kâr (EPS)", "Hisse Başına Defter Değeri (BVPS)"),
    )

    if not eps.empty:
        fig.add_trace(
            go.Bar(name="EPS", x=eps.index.year, y=eps, text=eps), row=1, col=1
        )
    if not bvps.empty:
        fig.add_trace(
            go.Bar(name="BVPS", x=bvps.index.year, y=bvps, text=bvps), row=1, col=2
        )

    fig.update_layout(
        title_text="Hisse Başına Değerlerin Yıllık Değişimi",
        template="plotly_dark",
        height=400,
    )
    fig.update_traces(texttemplate="%{y:.2f}", textposition="auto")
    return fig


def display_per_share_values_chart(financials, balance_sheet, info):
    """Generates and displays the per-share values chart in Streamlit."""
    fig = plot_per_share_values(financials, balance_sheet, info)
    st.plotly_chart(fig, use_container_width=True)


def plot_dividend_history(dividends):
    """Creates a bar chart of historical dividend payments."""
    if dividends is None or dividends.empty:
        return go.Figure().update_layout(
            title_text="Şirketin Geçmiş Temettü Ödemesi Bulunmamaktadır",
            template="plotly_dark",
        )

    fig = go.Figure()
    fig.add_trace(go.Bar(x=dividends.index, y=dividends, name="Hisse Başına Temettü"))

    fig.update_layout(
        title_text="Yıllara Göre Hisse Başına Temettü Ödemeleri (TL)",
        xaxis_title="Tarih",
        yaxis_title="Temettü (TL)",
        template="plotly_dark",
        height=400,
    )
    return fig


def display_dividend_history_chart(dividends):
    """Generates and displays the dividend history chart in Streamlit."""
    fig = plot_dividend_history(dividends)
    st.plotly_chart(fig, use_container_width=True)


def display_portfolio_performance_chart(portfolio_history):
    """Generates and displays the portfolio performance chart."""
    if portfolio_history.empty:
        st.info("Portföy geçmişi grafiği oluşturmak için yeterli veri bulunmuyor.")
        return

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=portfolio_history.index,
            y=portfolio_history["Total Value"],
            mode="lines",
            name="Portföy Değeri",
            fill="tozeroy",
        )
    )

    fig.update_layout(
        title="Portföy Değerinin Zaman İçindeki Değişimi",
        xaxis_title="Tarih",
        yaxis_title="Toplam Değer (TL)",
        template="plotly_dark",
        height=500,
    )
    st.plotly_chart(fig, use_container_width=True)


def display_asset_allocation_chart(summary_df):
    """Generates and displays the asset allocation pie chart."""
    if summary_df.empty or 'Güncel Değer' not in summary_df.columns or 'hisse' not in summary_df.columns:
        st.info("Varlık dağılımı grafiği için veri bulunmuyor.")
        return

    fig = px.pie(
        summary_df, 
        values='Güncel Değer', 
        names='hisse', 
        title='Portföy Varlık Dağılımı',
        hole=.3
    )
    fig.update_traces(textposition='inside', textinfo='percent+label')
    fig.update_layout(template="plotly_dark")
    st.plotly_chart(fig, use_container_width=True)

def plot_price_performance_comparison(data):
    """
    Plots the normalized price performance for multiple stocks.
    """
    if data.empty:
        return go.Figure().update_layout(
            title_text="Karşılaştırma için fiyat verisi bulunamadı.", template="plotly_dark"
        )
        
    # Normalize the price data
    normalized_data = (data / data.iloc[0] * 100)
    
    fig = px.line(
        normalized_data,
        x=normalized_data.index,
        y=normalized_data.columns,
        title="Seçilen Hisselerin Normalize Edilmiş Fiyat Performansı (Başlangıç = 100)",
    )
    
    fig.update_layout(
        yaxis_title="Normalize Edilmiş Fiyat",
        xaxis_title="Tarih",
        legend_title="Hisseler",
        template="plotly_dark",
        height=500,
    )
    
    st.plotly_chart(fig, use_container_width=True)