import plotly.graph_objects as go
from plotly.subplots import make_subplots
import mplfinance as mpf
import pandas as pd

def plot_analysis_plotly(veri, hisse_kodu, interval_display, analysis_type):
    """Ana teknik analiz grafiğini oluşturur."""
    rows = 3 if analysis_type == "Basit" else 6
    row_heights = [0.6] + [0.1] * (rows - 1)
    
    fig = make_subplots(
        rows=rows, cols=1, shared_xaxes=True,
        vertical_spacing=0.03,
        row_heights=row_heights,
        subplot_titles=(["Fiyat ve Hareketli Ortalamalar", "Hacim", "RSI"] if analysis_type == "Basit" 
                        else ["Fiyat ve Göstergeler", "Hacim", "RSI & StochRSI", "MACD", "ADX", "OBV"])
    )

    # Ana Grafik - Mumlar
    fig.add_trace(go.Candlestick(x=veri.index, open=veri['open'], high=veri['high'],
                                 low=veri['low'], close=veri['close'], name='Fiyat'), row=1, col=1)

    # Hacim
    fig.add_trace(go.Bar(x=veri.index, y=veri['volume'], name='Hacim', marker_color='grey'), row=2, col=1)

    # Göstergeler
    if analysis_type == "Basit":
        fig.add_trace(go.Scatter(x=veri.index, y=veri['ema_50'], name='EMA 50', line=dict(color='orange')), row=1, col=1)
        fig.add_trace(go.Scatter(x=veri.index, y=veri['ema_200'], name='EMA 200', line=dict(color='purple')), row=1, col=1)
        
        # RSI
        fig.add_trace(go.Scatter(x=veri.index, y=veri['rsi_14'], name='RSI'), row=3, col=1)
        fig.add_hline(y=70, line_dash="dash", line_color="red", row=3, col=1)
        fig.add_hline(y=30, line_dash="dash", line_color="green", row=3, col=1)
    else: # Detaylı
        # Fiyat paneli göstergeleri
        fig.add_trace(go.Scatter(x=veri.index, y=veri['ema_8'], name='EMA 8', line=dict(color='blue', width=1)), row=1, col=1)
        fig.add_trace(go.Scatter(x=veri.index, y=veri['ema_13'], name='EMA 13', line=dict(color='purple', width=1)), row=1, col=1)
        fig.add_trace(go.Scatter(x=veri.index, y=veri['ema_21'], name='EMA 21', line=dict(color='orange', width=1)), row=1, col=1)
        fig.add_trace(go.Scatter(x=veri.index, y=veri['bbu_20_2.0'], name='BB Üst', line=dict(color='green', width=1, dash='dash')), row=1, col=1)
        fig.add_trace(go.Scatter(x=veri.index, y=veri['bbl_20_2.0'], name='BB Alt', line=dict(color='red', width=1, dash='dash')), row=1, col=1)
        fig.add_trace(go.Scatter(x=veri.index, y=veri['vwap_d'], name='VWAP', line=dict(color='cyan', width=1.5, dash='dot')), row=1, col=1)

        # Ichimoku Bulutu
        fig.add_trace(go.Scatter(x=veri.index, y=veri['itsa_9_26_52'], name='Tenkan-sen', line=dict(color='#00bcd4', width=1)), row=1, col=1)
        fig.add_trace(go.Scatter(x=veri.index, y=veri['itsb_9_26_52'], name='Kijun-sen', line=dict(color='#ff9800', width=1.5)), row=1, col=1)
        fig.add_trace(go.Scatter(x=veri.index, y=veri['is_9_26_52'], name='Chikou Span', line=dict(color='#e91e63', width=1.5, dash='dot')), row=1, col=1)
        # Kumo Bulutu (Senkou Span A ve B arası)
        fig.add_trace(go.Scatter(x=veri.index, y=veri['senkou_a'], fill=None, mode='lines', line_color='rgba(0,255,0,0.1)', name='Senkou A'), row=1, col=1)
        fig.add_trace(go.Scatter(x=veri.index, y=veri['senkou_b'], fill='tonexty', mode='lines', line_color='rgba(255,0,0,0.1)', name='Senkou B'), row=1, col=1)

        # RSI & StochRSI Paneli
        fig.add_trace(go.Scatter(x=veri.index, y=veri['rsi_14'], name='RSI'), row=3, col=1)
        fig.add_hline(y=70, line_dash="dash", line_color="red", row=3, col=1)
        fig.add_hline(y=30, line_dash="dash", line_color="green", row=3, col=1)
        fig.add_trace(go.Scatter(x=veri.index, y=veri['stochrsik_14_14_3_3'], name='StochRSI K', line=dict(color='cyan')), row=3, col=1)
        fig.add_trace(go.Scatter(x=veri.index, y=veri['stochrsid_14_14_3_3'], name='StochRSI D', line=dict(color='magenta')), row=3, col=1)

        # MACD Paneli
        fig.add_trace(go.Scatter(x=veri.index, y=veri['macd_12_26_9'], name='MACD', line=dict(color='blue')), row=4, col=1)
        fig.add_trace(go.Scatter(x=veri.index, y=veri['macds_12_26_9'], name='Signal', line=dict(color='orange')), row=4, col=1)
        fig.add_trace(go.Bar(x=veri.index, y=veri['macdh_12_26_9'], name='Histogram', marker_color='grey'), row=4, col=1)

        # ADX Paneli
        fig.add_trace(go.Scatter(x=veri.index, y=veri['adx_14'], name='ADX', line=dict(color='#ffc107')), row=5, col=1)
        fig.add_trace(go.Scatter(x=veri.index, y=veri['dmp_14'], name='+DI', line=dict(color='#28a745')), row=5, col=1)
        fig.add_trace(go.Scatter(x=veri.index, y=veri['dmn_14'], name='-DI', line=dict(color='#dc3545')), row=5, col=1)

        # OBV Paneli
        fig.add_trace(go.Scatter(x=veri.index, y=veri['obv'], name='OBV'), row=6, col=1)

    fig.update_layout(
        title=f'{hisse_kodu} Teknik Analiz ({interval_display} - {analysis_type})',
        height=800,
        xaxis_rangeslider_visible=False,
        legend_orientation="h",
        legend_yanchor="bottom",
        legend_y=1.02,
        legend_xanchor="right",
        legend_x=1,
        template="plotly_dark"
    )
    fig.update_xaxes(showticklabels=True)
    return fig

def plot_comparison_plotly(data1, data2, hisse1, hisse2):
    """İki hissenin normalize edilmiş fiyat performansını karşılaştırır."""
    # Fiyatları başlangıç noktasına göre normalize et (Yüzdesel Değişim)
    norm_data1 = (data1['close'] / data1['close'].iloc[0] - 1) * 100
    norm_data2 = (data2['close'] / data2['close'].iloc[0] - 1) * 100

    fig = go.Figure()

    fig.add_trace(go.Scatter(x=norm_data1.index, y=norm_data1, name=hisse1, line=dict(width=2)))
    fig.add_trace(go.Scatter(x=norm_data2.index, y=norm_data2, name=hisse2, line=dict(width=2)))

    fig.update_layout(
        title=f'{hisse1} vs. {hisse2} Normalize Edilmiş Performans',
        yaxis_title="Yüzdesel Değişim (%)",
        height=600,
        template="plotly_dark",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    fig.update_yaxes(zeroline=True, zerolinewidth=2, zerolinecolor='Gray')
    
    return fig

def plot_analysis_mpl(veri, hisse_kodu, interval_display, analysis_type):
    """Matplotlib/mplfinance kullanarak teknik analiz grafiği oluşturur."""
    veri.index.name = 'Date'
    apds = [] # addplot listesi

    # Panelleri ve oranları dinamik olarak ayarla
    if analysis_type == "Basit":
        apds.extend([
            mpf.make_addplot(veri['ema_50'], color='orange', panel=0),
            mpf.make_addplot(veri['ema_200'], color='purple', panel=0),
            mpf.make_addplot(veri['volume'], panel=1, type='bar', color='gray', ylabel='Hacim'),
            mpf.make_addplot(veri['rsi_14'], panel=2, color='blue', ylabel='RSI'),
            mpf.make_addplot(pd.Series(70, index=veri.index), panel=2, color='gray', linestyle='--', width=0.7),
            mpf.make_addplot(pd.Series(30, index=veri.index), panel=2, color='gray', linestyle='--', width=0.7)
        ])
        panel_ratios = (3, 1, 1)
    else: # Detaylı
        apds.extend([
            # Panel 0: Fiyat ve Ortalamalar
            mpf.make_addplot(veri['ema_8'], color='#007bff', panel=0),
            mpf.make_addplot(veri['ema_13'], color='#6f42c1', panel=0),
            mpf.make_addplot(veri['ema_21'], color='#fd7e14', panel=0),
            mpf.make_addplot(veri['bbu_20_2.0'], color='#28a745', linestyle='--', panel=0),
            mpf.make_addplot(veri['bbl_20_2.0'], color='#dc3545', linestyle='--', panel=0),
            mpf.make_addplot(veri['vwap_d'], color='cyan', linestyle='-.', panel=0),
            # Panel 1: Hacim
            mpf.make_addplot(veri['volume'], panel=1, type='bar', color='gray', ylabel='Hacim'),
            # Panel 2: RSI & StochRSI
            mpf.make_addplot(veri['rsi_14'], panel=2, color='blue', ylabel='RSI/Stoch'),
            mpf.make_addplot(pd.Series(70, index=veri.index), panel=2, color='gray', linestyle='--', width=0.7),
            mpf.make_addplot(pd.Series(30, index=veri.index), panel=2, color='gray', linestyle='--', width=0.7),
            mpf.make_addplot(veri['stochrsik_14_14_3_3'], panel=2, color='cyan'),
            mpf.make_addplot(veri['stochrsid_14_14_3_3'], panel=2, color='magenta'),
            # Panel 3: MACD
            mpf.make_addplot(veri['macd_12_26_9'], panel=3, color='blue', ylabel='MACD'),
            mpf.make_addplot(veri['macds_12_26_9'], panel=3, color='orange'),
            mpf.make_addplot(veri['macdh_12_26_9'], type='bar', panel=3, color='gray'),
            # Panel 4: ADX
            mpf.make_addplot(veri['adx_14'], panel=4, color='#ffc107', ylabel='ADX'),
            mpf.make_addplot(veri['dmp_14'], panel=4, color='#28a745'),
            mpf.make_addplot(veri['dmn_14'], panel=4, color='#dc3545'),
            # Panel 5: OBV
            mpf.make_addplot(veri['obv'], panel=5, color='#ffc107', ylabel='OBV')
        ])
        panel_ratios = (6, 1, 2, 2, 2, 2)

    s = mpf.make_mpf_style(base_mpf_style='yahoo', rc={'figure.facecolor': 'white'})
    fig, axes = mpf.plot(veri,
                         type='candle',
                         style=s,
                         title=f'{hisse_kodu} Teknik Analiz ({interval_display} - {analysis_type})',
                         ylabel='Fiyat',
                         volume=False, # Hacim ayrı panelde
                         addplot=apds,
                         panel_ratios=panel_ratios,
                         figscale=1.5,
                         returnfig=True,
                         columns=['open', 'high', 'low', 'close', 'volume'])
    return fig, axes