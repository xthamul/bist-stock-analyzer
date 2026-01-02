import streamlit as st
from datetime import datetime, timedelta
import logging
import traceback
import streamlit_bokeh as st_bokeh
import pandas as pd
import plotly.express as px

from helpers.data_handler import (
    get_stock_data,
    get_fundamental_data,
    filter_data_by_date,
    calculate_indicators,
    convert_dataframe_for_streamlit,
    get_sector_comparison_data,
)
from helpers.plotter import (
    display_candlestick_chart,
    display_financial_trends_chart,
    display_balance_sheet_details_chart,
    display_per_share_values_chart,
    display_dividend_history_chart,
    display_portfolio_performance_chart,
    display_asset_allocation_chart,
    plot_price_performance_comparison,
)
from helpers.ui_components import (
    generate_technical_summary,
    generate_fundamental_summary,
    display_financial_ratios,
    display_sector_comparison,
    generate_ai_analysis,
    display_key_metrics_comparison,
)
from helpers.backtester import (
    run_backtest,
    optimize_strategy,
    EmaCross,
    RsiOscillator,
    MacdCross,
    BBandStrategy,
)
import helpers.database as db
from constants import HISSE_GRUPPARI, ZAMAN_ARALIKLARI
from helpers.news_handler import fetch_news_from_rss, analyze_sentiment
from helpers.portfolio_analyzer import calculate_portfolio_metrics, plot_portfolio_vs_benchmark


# --- Kurulumlar ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(message)s",
    filename="app.log",
    filemode="w",
)
db.init_db()
st.set_page_config(
    page_title="BIST Hisse Senedi Analiz Platformu", page_icon="📊", layout="wide"
)


# --- Arayüz Gösterim Fonksiyonları ---
@st.cache_data
def convert_df_to_csv(df):
    return df.to_csv().encode("utf-8")


def display_technical_analysis(
    veri,
    hisse_kodu_yf,
    interval_display,
    selected_indicators,
    show_support_resistance,
    show_fibonacci,
):
    st.header(f"{hisse_kodu_yf} - Teknik Grafik")
    display_candlestick_chart(
        veri,
        hisse_kodu_yf,
        interval_display,
        "Detaylı",
        selected_indicators,
        show_support_resistance,
        show_fibonacci=show_fibonacci,
    )
    csv = convert_df_to_csv(veri)
    st.download_button(
        "📥 Veriyi CSV Olarak İndir",
        csv,
        f"{hisse_kodu_yf}_{interval_display}_data.csv",
        "text/csv",
    )
    with st.expander("Teknik Analiz Özeti ve Yorumlar", expanded=True):
        summary = generate_technical_summary(veri)
        st.markdown(summary)

    with st.expander("Yapay Zeka Destekli Analiz", expanded=True):
        sonuc, analiz_ozeti = generate_ai_analysis(veri)
        st.subheader(f"Yapay Zeka Değerlendirmesi: {sonuc}")
        for kategori, yorumlar in analiz_ozeti.items():
            st.subheader(kategori)
            for yorum in yorumlar:
                st.markdown(f"- {yorum}")


def display_fundamental_analysis(hisse_kodu_yf):
    st.header(f"{hisse_kodu_yf} - Temel Veriler")
    with st.spinner(
        f"{hisse_kodu_yf} için temel veriler ve benzer şirket bilgileri alınıyor..."
    ):
        data = get_fundamental_data(hisse_kodu_yf)

    if data and data.get("info"):
        info = data["info"]
        financials = data["financials"]
        balance_sheet = data["balance_sheet"]
        cashflow = data["cashflow"]
        dividends = data["dividends"]

        tab_titles = [
            "Özet",
            "Oranlar",
            "Sektör Karşılaştırması",
            "Grafikler",
            "Bilanço Detay",
            "Hisse Değerleri",
            "Temettü Geçmişi",
            "Tablolar",
        ]
        (
            summary_tab,
            ratios_tab,
            sector_tab,
            charts_tab,
            balance_detail_tab,
            per_share_tab,
            dividend_tab,
            statements_tab,
        ) = st.tabs(tab_titles)

        with summary_tab:
            st.subheader("Şirket Künyesi")
            _, key_info_text = generate_fundamental_summary(info, as_markdown=False)
            st.text(key_info_text)

        with ratios_tab:
            ratios_df = display_financial_ratios(info, financials, balance_sheet)
            st.dataframe(ratios_df.style.format("{:.2f}"))

        with sector_tab:
            st.subheader("Sektör ve Benzer Şirket Karşılaştırması")
            sector, sector_averages = get_sector_comparison_data(hisse_kodu_yf)
            if sector and sector_averages is not None:
                st.write(f"**Sektör:** {sector}")
                company_ratios = display_financial_ratios(
                    info, financials, balance_sheet
                )["Değer"]
                comparison_styled = display_sector_comparison(
                    company_ratios, sector_averages
                )
                st.dataframe(comparison_styled)
            else:
                st.warning(
                    "Sektör verileri alınamadı veya karşılaştırma için yeterli benzer şirket bulunamadı."
                )

        with charts_tab:
            display_financial_trends_chart(financials, cashflow)

        with balance_detail_tab:
            display_balance_sheet_details_chart(balance_sheet)

        with per_share_tab:
            display_per_share_values_chart(financials, balance_sheet, info)

        with dividend_tab:
            display_dividend_history_chart(dividends)

        with statements_tab:
            st.subheader("Gelir Tablosu")
            st.dataframe(convert_dataframe_for_streamlit(financials))
            st.subheader("Bilanço")
            st.dataframe(convert_dataframe_for_streamlit(balance_sheet))
            st.subheader("Nakit Akış Tablosu")
            st.dataframe(convert_dataframe_for_streamlit(cashflow))
    else:
        st.warning("Temel veriler alınamadı.")


def display_backtest_summary(stats, initial_cash):
    st.subheader("Performans Sonuçları")

    # Key metrics
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Başlangıç Portföyü", f"{initial_cash:,.2f} $")
    col2.metric("Bitiş Portföyü", f"{stats['Equity Final [$]']:,.2f} $")
    col3.metric("Toplam Getiri [%]", f"{stats['Return [%]']:.2f}%")
    col4.metric("Maks. Düşüş (Drawdown) [%]", f"{stats['Max. Drawdown [%]']:.2f}%")

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Kazanma Oranı (Win Rate) [%]", f"{stats['Win Rate [%]']:.2f}%")
    col2.metric("Sharpe Oranı", f"{stats['Sharpe Ratio']:.2f}")
    col3.metric("Profit Factor", f"{stats['Profit Factor']:.2f}")
    col4.metric("Toplam İşlem Sayısı", f"{stats['# Trades']}")

    with st.expander("Tüm İstatistikleri Gör"):
        stats_df = stats.to_frame(name="Value")
        # Convert entire column to string to avoid Arrow serialization errors with mixed types
        stats_df["Value"] = stats_df["Value"].astype(str)
        st.dataframe(stats_df)


def display_backtesting(veri, hisse_kodu_yf):
    st.header(f"{hisse_kodu_yf} - Strateji Testi ve Optimizasyon")
    test_mode = st.radio(
        "Çalışma Modu", ["Tekli Test", "Optimizasyon"], horizontal=True
    )
    strategy_options = {
        "EMA Kesişimi": EmaCross,
        "RSI Osilatörü": RsiOscillator,
        "MACD Kesişimi": MacdCross,
        "Bollinger Bandı Stratejisi": BBandStrategy,
    }
    selected_strategy_name = st.selectbox(
        "Test Edilecek Strateji:", list(strategy_options.keys())
    )
    selected_strategy_class = strategy_options[selected_strategy_name]

    with st.form(key=f"backtest_form_{selected_strategy_name}_{test_mode}"):
        params = {}

        st.subheader("Genel Parametreler")
        initial_cash = st.number_input("Başlangıç Nakiti", 1000, 1000000, 100000, 1000)
        commission = st.slider("Komisyon Oranı (%)", 0.0, 1.0, 0.2, 0.01) / 100

        st.subheader(f"{selected_strategy_name} Strateji Parametreleri")
        if selected_strategy_name == "EMA Kesişimi":
            if test_mode == "Tekli Test":
                c1, c2 = st.columns(2)
                params["n1"] = c1.number_input("Kısa EMA", 1, 200, 50)
                params["n2"] = c2.number_input("Uzun EMA", 1, 500, 200)
            else:
                c1, c2, c3 = st.columns(3)
                params["n1"] = range(
                    c1.number_input("n1 Başla", 1, 200, 10),
                    c2.number_input("n1 Bitir", 1, 200, 50),
                    c3.number_input("n1 Adım", 1, 20, 5),
                )
                c1, c2, c3 = st.columns(3)
                params["n2"] = range(
                    c1.number_input("n2 Başla", 1, 500, 100),
                    c2.number_input("n2 Bitir", 1, 500, 200),
                    c3.number_input("n2 Adım", 1, 50, 10),
                )
        elif selected_strategy_name == "RSI Osilatörü":
            if test_mode == "Tekli Test":
                c1, c2, c3 = st.columns(3)
                params["rsi_window"] = c1.number_input("RSI Periyodu", 1, 100, 14)
                params["buy_threshold"] = c2.number_input("Alım Eşiği", 1, 100, 30)
                params["sell_threshold"] = c3.number_input("Satım Eşiği", 1, 100, 70)
            else:
                c1, c2, c3 = st.columns(3)
                params["rsi_window"] = range(
                    c1.number_input("RSI Başla", 5, 50, 10),
                    c2.number_input("RSI Bitir", 5, 50, 20),
                    c3.number_input("RSI Adım", 1, 10, 2),
                )
        elif selected_strategy_name == "MACD Kesişimi":
            if test_mode == "Tekli Test":
                c1, c2, c3 = st.columns(3)
                params["fast"] = c1.number_input("Hızlı Periyot", 1, 100, 12)
                params["slow"] = c2.number_input("Yavaş Periyot", 1, 200, 26)
                params["signal"] = c3.number_input("Sinyal Periyodu", 1, 100, 9)
            else:
                c1, c2, c3 = st.columns(3)
                params["fast"] = range(
                    c1.number_input("Hızlı Başla", 5, 50, 10),
                    c2.number_input("Hızlı Bitir", 5, 50, 20),
                    c3.number_input("Hızlı Adım", 1, 10, 2),
                )
                c1, c2, c3 = st.columns(3)
                params["slow"] = range(
                    c1.number_input("Yavaş Başla", 20, 100, 20),
                    c2.number_input("Yavaş Bitir", 20, 100, 50),
                    c3.number_input("Yavaş Adım", 1, 10, 5),
                )
        elif selected_strategy_name == "Bollinger Bandı Stratejisi":
            if test_mode == "Tekli Test":
                c1, c2 = st.columns(2)
                params["length"] = c1.number_input("Periyot", 1, 100, 20)
                params["std"] = c2.number_input("Standart Sapma", 0.1, 5.0, 2.0, 0.1)
            else:
                c1, c2, c3 = st.columns(3)
                params["length"] = range(
                    c1.number_input("Periyot Başla", 5, 50, 10),
                    c2.number_input("Periyot Bitir", 5, 50, 30),
                    c3.number_input("Periyot Adım", 1, 10, 5),
                )
                st.info(
                    "Bollinger Bandı stratejisi için Standart Sapma optimizasyonu şu anda desteklenmemektedir."
                )

        st.subheader("Risk Yönetimi Parametreleri")
        if test_mode == "Tekli Test":
            sl_col, tp_col = st.columns(2)
            sl_val = sl_col.number_input("Stop-Loss (%)", 0.0, 100.0, 5.0, 0.5)
            tp_val = tp_col.number_input("Take-Profit (%)", 0.0, 100.0, 10.0, 0.5)
            params["stop_loss"] = sl_val / 100 if sl_val > 0 else None
            params["take_profit"] = tp_val / 100 if tp_val > 0 else None
        else:  # Optimizasyon
            st.write("Stop-Loss Optimizasyonu (%)")
            sl_c1, sl_c2, sl_c3 = st.columns(3)
            sl_start = sl_c1.number_input("SL Başla", 1, 50, 2, key="sl_start")
            sl_end = sl_c2.number_input("SL Bitir", 1, 50, 10, key="sl_end")
            sl_step = sl_c3.number_input("SL Adım", 1, 10, 2, key="sl_step")
            params["stop_loss"] = [i / 100 for i in range(sl_start, sl_end, sl_step)]

            st.write("Take-Profit Optimizasyonu (%)")
            tp_c1, tp_c2, tp_c3 = st.columns(3)
            tp_start = tp_c1.number_input("TP Başla", 1, 100, 5, key="tp_start")
            tp_end = tp_c2.number_input("TP Bitir", 1, 100, 20, key="tp_end")
            tp_step = tp_c3.number_input("TP Adım", 1, 20, 5, key="tp_step")
            params["take_profit"] = [i / 100 for i in range(tp_start, tp_end, tp_step)]
            
            optimization_metrics = [
                "Equity Final [$]",
                "Return [%]",
                "Sharpe Ratio",
                "Win Rate [%]",
                "Profit Factor",
            ]
            maximize_metric = st.selectbox(
                "Optimize Edilecek Metrik:", optimization_metrics, index=0
            )

        if st.form_submit_button(f"{test_mode} Çalıştır"):
            spinner_msg = (
                "Strateji optimize ediliyor..."
                if test_mode == "Optimizasyon"
                else "Strateji test ediliyor..."
            )
            with st.spinner(spinner_msg):
                try:
                    backtest_data = veri[
                        ["open", "high", "low", "close", "volume"]
                    ].copy()
                    if test_mode == "Tekli Test":
                        stats, plot_fig = run_backtest(
                            selected_strategy_class,
                            backtest_data,
                            initial_cash,
                            commission,
                            **params,
                        )
                        display_backtest_summary(stats, initial_cash)
                        st.subheader("İşlem Grafiği")
                        st_bokeh.bokeh_chart(plot_fig, use_container_width=True)
                    else:
                        heatmap = optimize_strategy(
                            selected_strategy_class,
                            backtest_data,
                            initial_cash,
                            commission,
                            maximize=maximize_metric,
                            **params,
                        )

                        st.subheader("Optimizasyon Sonuçları")
                        if heatmap.empty:
                            st.warning(
                                "Optimizasyon sonucu bulunamadı. Lütfen parametre aralıklarını kontrol edin."
                            )
                        else:
                            results_df = heatmap.reset_index()
                            results_df = results_df.sort_values(
                                by=maximize_metric, ascending=False
                            )

                            st.write(
                                f"En iyi sonuçlar `{maximize_metric}` metriğine göre sıralanmıştır."
                            )
                            st.dataframe(results_df)

                            best_params = results_df.iloc[0]
                            st.subheader("En İyi Strateji Parametreleri")
                            st.json(best_params.to_dict())
                except Exception as e:
                    st.error(f"{test_mode} sırasında bir hata oluştu: {e}")

def display_comparison(hisse_list, interval, start_date, end_date):
    """Hisselerin karşılaştırmalı analizini gösterir."""
    st.header("Hisse Karşılaştırma Analizi")
    
    hisse_list_yf = [f"{hisse}.IS" for hisse in hisse_list]
    
    with st.spinner("Karşılaştırma için veriler çekiliyor..."):
        all_data = get_stock_data(hisse_list_yf, interval, start_date, end_date)
    
    if all_data is None or all_data.empty:
        st.error("Karşılaştırma için veriler çekilemedi.")
        return
        
    # Fiyat Performans Grafiği
    close_prices = all_data['close']
    close_prices.columns = close_prices.columns.str.replace('.IS', '')
    plot_price_performance_comparison(close_prices)
    
    st.divider()
    
    # Temel Metrikler Tablosu
    display_key_metrics_comparison(hisse_list)

def display_news_and_sentiment(hisse_kodu):
    """İlgili hisse için haberleri ve duyarlılık analizini gösterir."""
    st.header(f"{hisse_kodu} için Haberler ve Piyasa Duyarlılığı")

    # RSS kaynağı - Bu URL'yi daha dinamik hale getirebilir veya daha fazla kaynak ekleyebilirsiniz.
    # Hisse kodunu içeren bir arama yapmak için, haber kaynağının bunu desteklemesi gerekir.
    # Şimdilik genel piyasa haberlerini alıyoruz.
    feed_url = "https://www.yatirimrehberi.com.tr/rss/piyasalar"
    
    with st.spinner("Haberler ve duyarlılık analizi yükleniyor..."):
        news_items = fetch_news_from_rss(feed_url)
        
        if not news_items:
            st.warning("İlgili haber bulunamadı.")
            return

        sentiments = []
        for item in news_items:
            # Hisse kodu haber başlığında veya özetinde geçiyorsa daha ilgili kabul edilebilir
            # Bu basit bir filtreleme, daha gelişmiş yöntemler kullanılabilir
            if hisse_kodu.lower() in item.title.lower() or hisse_kodu.lower() in item.summary.lower():
                item['relevant'] = True # İlgili olarak işaretle
                sentiment = analyze_sentiment(item.title)
                item['sentiment'] = sentiment
                sentiments.append(sentiment)
            else:
                item['relevant'] = False
                item['sentiment'] = "N/A"

    relevant_news = [item for item in news_items if item['relevant']]
    
    if not relevant_news:
        st.info(f"'{hisse_kodu}' için spesifik bir haber bulunamadı. Genel piyasa haberleri gösteriliyor.")
        # İlgili haber yoksa tüm haberleri göster
        relevant_news = news_items 
        sentiments = [analyze_sentiment(item.title) for item in relevant_news]


    # Duyarlılık Dağılımı Grafiği
    if sentiments:
        sentiment_counts = pd.Series(sentiments).value_counts()
        fig = px.pie(
            sentiment_counts, 
            values=sentiment_counts.values, 
            names=sentiment_counts.index, 
            title='Haberlerin Duyarlılık Dağılımı',
            color=sentiment_counts.index,
            color_discrete_map={'Pozitif':'green', 'Negatif':'red', 'Nötr':'gray', 'Analiz Edilemedi': 'black'}
        )
        st.plotly_chart(fig, use_container_width=True)

    # Haberleri Listele
    st.subheader("Haber Başlıkları")
    for item in relevant_news:
        sentiment = item.get('sentiment', 'N/A')
        icon = "🟢" if sentiment == 'Pozitif' else "🔴" if sentiment == 'Negatif' else "⚪"
        st.markdown(f"<h5>{icon} <a href='{item.link}' target='_blank'>{item.title}</a></h5>", unsafe_allow_html=True)
        with st.expander("Özeti Oku"):
            st.markdown(item.summary, unsafe_allow_html=True)


def analyzer_main_page():
    st.sidebar.header("Kontrol Paneli")

    # --- Kişiselleştirme Verilerini Yükle ---
    favorite_stocks = db.get_preference("favorite_stocks", [])
    default_indicators = db.get_preference(
        "default_indicators",
        [
            "EMA KISA (5, 20)",
            "EMA UZUN (50, 200)",
            "Bollinger Bantları",
            "RSI",
            "MACD",
        ],
    )

    # Hisse gruplarına Favorileri dinamik olarak ekle
    hisse_gruplari_dynamic = HISSE_GRUPPARI.copy()
    if favorite_stocks:
        hisse_gruplari_dynamic["⭐ Favorilerim"] = favorite_stocks

    grup_secim = st.sidebar.selectbox(
        "Hisse Grubu:", list(hisse_gruplari_dynamic.keys()), index=0
    )
    hisseler = sorted(hisse_gruplari_dynamic.get(grup_secim, []))

    # Çoklu hisse seçimi için multiselect kullan
    hisse_secim_list = st.sidebar.multiselect(
        "Hisse Senedi/Senetleri:",
        hisseler,
        default=st.session_state.get("hisse_secim_list", []),
        max_selections=5,  # Karşılaştırma için bir limit belirle
    )

    today = datetime.today()
    start_date = st.sidebar.date_input("Başlangıç Tarihi", today - timedelta(days=365))
    end_date = st.sidebar.date_input("Bitiş Tarihi", today)
    interval_display = st.sidebar.selectbox(
        "Zaman Aralığı:", list(ZAMAN_ARALIKLARI.keys()), index=3
    )
    
    is_single_stock_mode = len(hisse_secim_list) == 1
    
    # --- Ayarlar ve Butonlar ---
    if is_single_stock_mode:
        st.sidebar.subheader("Kişiselleştirme")
        if st.sidebar.button("⭐ Seçili Hisseyi Favorilere Ekle/Kaldır", use_container_width=True):
            stock_to_toggle = hisse_secim_list[0]
            if stock_to_toggle in favorite_stocks:
                favorite_stocks.remove(stock_to_toggle)
                st.sidebar.success(f"{stock_to_toggle} favorilerden kaldırıldı.")
            else:
                favorite_stocks.append(stock_to_toggle)
                st.sidebar.success(f"{stock_to_toggle} favorilere eklendi.")
            db.set_preference("favorite_stocks", sorted(favorite_stocks))
            st.rerun()

    # Çoklu seçimde bazı UI elemanlarını gizle
    selected_indicators = []
    show_support_resistance = False
    show_fibonacci = False

    if is_single_stock_mode:
        st.sidebar.subheader("Tekli Hisse Ayarları")
        available_indicators = [
            "EMA KISA (5, 20)",
            "EMA UZUN (50, 200)",
            "Bollinger Bantları",
            "VWAP",
            "Ichimoku Cloud",
            "RSI",
            "StochRSI",
            "MACD",
            "ADX",
            "OBV",
            "Golden/Death Cross",
            "Super Trend",
        ]
        selected_indicators = st.sidebar.multiselect(
            "Göstergeler:",
            available_indicators,
            default=default_indicators,
        )
        show_support_resistance = st.sidebar.checkbox("Destek/Direnç Göster", value=True)
        show_fibonacci = st.sidebar.checkbox(
            "Fibonacci Geri Çekilme Seviyeleri Göster", value=False
        )
        if st.sidebar.button("Bu Göstergeleri Varsayılan Yap", use_container_width=True):
            db.set_preference("default_indicators", selected_indicators)
            st.sidebar.success("Varsayılan göstergeler kaydedildi!")

    if st.sidebar.button("Analiz Et", use_container_width=True, type="primary"):
        if not hisse_secim_list:
            st.sidebar.warning("Lütfen en az bir hisse senedi seçin.")
        elif start_date > end_date:
            st.sidebar.error("Hata: Başlangıç tarihi, bitiş tarihinden sonra olamaz.")
        else:
            interval_code = ZAMAN_ARALIKLARI[interval_display]

            max_days = None
            if interval_code in ["15m", "30m"]:
                max_days = 59
            elif interval_code == "60m":
                max_days = 729

            if max_days and (end_date - start_date).days > max_days:
                start_date = end_date - timedelta(days=max_days)
                st.sidebar.warning(
                    f"Tarih aralığı, {interval_display} için {max_days} günle sınırlandırıldı."
                )

            st.session_state.analysis_requested = True
            st.session_state.hisse_secim_list = hisse_secim_list
            st.session_state.start_date = start_date
            st.session_state.end_date = end_date
            st.session_state.interval_display = interval_display
            st.session_state.selected_indicators = selected_indicators
            st.session_state.show_support_resistance = show_support_resistance
            st.session_state.show_fibonacci = show_fibonacci
            st.rerun()

    if st.session_state.get("analysis_requested", False):
        # Session state'den bilgileri al
        hisse_list = st.session_state.hisse_secim_list
        start = st.session_state.start_date
        end = st.session_state.end_date
        interval_disp = st.session_state.interval_display
        interval_code = ZAMAN_ARALIKLARI[interval_disp]

        if len(hisse_list) > 1:
            # Karşılaştırma Modu
            display_comparison(hisse_list, interval_code, start, end)
        
        elif len(hisse_list) == 1:
            # Tekli Hisse Modu
            hisse_kodu = hisse_list[0]
            hisse_kodu_yf = f"{hisse_kodu}.IS"
            
            with st.spinner(
                f"{hisse_kodu_yf} için veriler çekiliyor ve analiz ediliyor..."
            ):
                veri_raw = get_stock_data(
                    hisse_kodu_yf,
                    interval_code,
                    start_date=start,
                    end_date=end,
                )
                if veri_raw is not None and not veri_raw.empty:
                    veri_hesaplanmis = calculate_indicators(veri_raw.copy())
                    veri_filtrelenmis = filter_data_by_date(
                        veri_hesaplanmis,
                        start_date=start,
                        end_date=end,
                    )
                    if veri_filtrelenmis.empty:
                        st.warning("Seçilen tarih aralığı için veri bulunamadı.")
                        return

                    st.success(f"{hisse_kodu_yf} analizi tamamlandı.")
                    
                    tab_titles = ["📈 Teknik Analiz", "🏢 Temel Analiz", "🧪 Strateji Testi", "📰 Haberler & Duyarlılık"]
                    ana_tab, temel_tab, backtest_tab, haber_tab = st.tabs(tab_titles)

                    with ana_tab:
                        display_technical_analysis(
                            veri_filtrelenmis,
                            hisse_kodu_yf,
                            interval_disp,
                            st.session_state.selected_indicators,
                            st.session_state.show_support_resistance,
                            st.session_state.show_fibonacci,
                        )
                    with temel_tab:
                        display_fundamental_analysis(hisse_kodu_yf)
                    with backtest_tab:
                        display_backtesting(veri_filtrelenmis, hisse_kodu_yf)
                    with haber_tab:
                        display_news_and_sentiment(hisse_kodu)
                else:
                    st.error(f"{hisse_kodu} için veri çekilemedi.")
    else:
        st.info(
            "Lütfen sol taraftaki menüden bir veya daha fazla hisse seçip 'Analiz Et' butonuna tıklayın."
        )


def portfolio_manager_page():
    st.header("💼 Portföy Yönetimi")
    with st.form("transaction_form", clear_on_submit=True):
        st.subheader("Yeni İşlem Ekle")
        col1, col2, col3, col4 = st.columns(4)
        ticker = col1.text_input("Hisse Kodu (örn: GARAN)").upper()
        quantity = col2.number_input("Miktar", min_value=1, step=1)
        price = col3.number_input("Alış Fiyatı", min_value=0.01, format="%.2f")
        date = col4.date_input("Alış Tarihi", datetime.today())
        if st.form_submit_button("Portföye Ekle") and ticker:
            db.add_transaction(ticker, quantity, price, str(date))
            st.success(f"{ticker} portföye eklendi!")
            st.rerun()

    st.divider()

    portfolio_df = db.get_all_transactions()
    if portfolio_df.empty:
        st.info("Portföyünüz boş. Başlamak için yukarıdan bir işlem ekleyin.")
        return

    transactions = portfolio_df.copy()
    transactions["tarih"] = pd.to_datetime(transactions["tarih"])
    start_date = transactions["tarih"].min()
    unique_tickers = transactions["hisse"].unique()
    
    all_prices = pd.DataFrame()

    # --- Optimize Edilmiş Toplu Veri Çekme ---
    with st.spinner("Portföy için geçmiş fiyat verileri toplu olarak çekiliyor..."):
        # Bütün ticker'ları .IS formatına getirip tek bir string'de birleştir
        ticker_list_yf = [f"{ticker}.IS" for ticker in unique_tickers]
        
        if ticker_list_yf:
            try:
                # Tek bir API çağrısı ile tüm hisselerin verisini al
                all_prices_raw = get_stock_data(
                    ticker_list_yf, "1d", start_date=start_date, end_date=datetime.today()
                )

                if all_prices_raw is None or all_prices_raw.empty:
                    st.warning("Portföydeki hisseler için fiyat verisi çekilemedi.")
                    # All prices kalacak boş, aşağıdaki logic handle edecek
                else:
                    # yfinance'den dönen MultiIndex'li sütunları düzenle
                    # Sadece 'close' fiyatlarına ihtiyacımız var
                    all_prices = all_prices_raw.get('close', pd.DataFrame())
                    if not all_prices.empty:
                        # Sütun isimlerinden '.IS' uzantısını kaldır
                        all_prices.columns = all_prices.columns.str.replace('.IS', '')
                
            except Exception as e:
                st.error(f"Geçmiş fiyat verileri çekilirken bir hata oluştu: {e}")
                # Hata durumunda boş all_prices ile devam et
    
    # --- Portföy Geçmişi ve Grafik ---
    st.subheader("Portföy Performansı")
    if not all_prices.empty:
        all_prices.ffill(inplace=True)

        date_range = pd.date_range(start=start_date, end=datetime.today(), freq='D')
        daily_positions = pd.DataFrame(0.0, index=date_range, columns=unique_tickers)

        position_changes = transactions.pivot_table(index='tarih', columns='hisse', values='miktar', aggfunc='sum').fillna(0)
        daily_positions.update(position_changes)
        
        daily_positions = daily_positions.cumsum().ffill()

        # Ensure columns match for multiplication
        shared_tickers = [ticker for ticker in unique_tickers if ticker in all_prices.columns]
        daily_values = daily_positions[shared_tickers].multiply(all_prices[shared_tickers], axis="columns").ffill()
        
        portfolio_history = pd.DataFrame(index=date_range)
        portfolio_history["Total Value"] = daily_values.sum(axis=1)

        display_portfolio_performance_chart(portfolio_history)

    # --- Mevcut Portföy Tablosu ---
    st.subheader("Mevcut Portföy Özeti")
    
    summary_df = transactions.groupby('hisse').apply(lambda x: pd.Series({
        'Miktar': x['miktar'].sum(),
        'Ortalama_Maliyet': (x['alis_fiyati'] * x['miktar']).sum() / x['miktar'].sum()
    })).reset_index()

    # --- Optimize Edilmiş Güncel Fiyat Alma ---
    current_prices = {}
    if not all_prices.empty:
        current_prices = all_prices.iloc[-1].to_dict()
    else:
        # Toplu çekme başarısız olduysa tekli deneme (fallback)
        with st.spinner("Güncel fiyatlar tek tek çekiliyor..."):
            for t in unique_tickers:
                data = get_stock_data(f"{t}.IS", "1d")
                if data is not None and not data.empty:
                    current_prices[t] = data['close'].iloc[-1]
                else:
                    current_prices[t] = 0

    summary_df["Güncel Fiyat"] = summary_df['hisse'].map(current_prices).fillna(0)
    summary_df["Toplam Maliyet"] = summary_df["Miktar"] * summary_df["Ortalama_Maliyet"]
    summary_df["Güncel Değer"] = summary_df["Miktar"] * summary_df["Güncel Fiyat"]
    summary_df["Kar/Zarar"] = summary_df["Güncel Değer"] - summary_df["Toplam Maliyet"]
    
    col1, col2 = st.columns([3, 2]) # Tabloya daha fazla yer ver
    with col1:
        st.dataframe(summary_df.style.format({
            "Ortalama_Maliyet": "{:,.2f} TL",
            "Güncel Fiyat": "{:,.2f} TL",
            "Toplam Maliyet": "{:,.2f} TL",
            "Güncel Değer": "{:,.2f} TL",
            "Kar/Zarar": "{:,.2f} TL"
        }), use_container_width=True)
    with col2:
        display_asset_allocation_chart(summary_df)

    st.divider()

    # --- Gelişmiş Portföy Analizi ---
    st.subheader("Gelişmiş Risk ve Getiri Analizi")
    
    # Benchmark verisini çek
    benchmark_data = get_stock_data("XU100.IS", "1d", start_date, datetime.today())
    
    if 'portfolio_history' in locals() and portfolio_history is not None and not portfolio_history.empty and benchmark_data is not None:
        metrics = calculate_portfolio_metrics(portfolio_history['Total Value'], benchmark_data['close'])
        
        if metrics:
            m_col1, m_col2, m_col3 = st.columns(3)
            m_col1.metric("Portföy Beta", f"{metrics.get('beta', 0):.2f}", help="Portföyün piyasaya (BIST 100) göre volatilitesi. 1'den büyük olması daha volatil, küçük olması daha az volatil olduğunu gösterir.")
            m_col2.metric("Yıllık Volatilite", f"{metrics.get('annualized_volatility', 0):.2%}", help="Portföy getirisinin yıllık standart sapması. Yüksek değer daha fazla risk anlamına gelir.")
            m_col3.metric("Sharpe Oranı", f"{metrics.get('sharpe_ratio', 0):.2f}", help="Risk başına getiri ölçüsü. Daha yüksek bir Sharpe oranı, daha iyi bir risk-ayarlı getiri anlamına gelir.")
            
            # Karşılaştırma grafiği
            st.plotly_chart(plot_portfolio_vs_benchmark(portfolio_history['Total Value'], benchmark_data['close']), use_container_width=True)

    total_value = summary_df["Güncel Değer"].sum()
    total_cost = summary_df["Toplam Maliyet"].sum()
    total_pnl = total_value - total_cost
    total_return = (total_pnl / total_cost * 100) if total_cost != 0 else 0

    val_col, pnl_col, ret_col = st.columns(3)
    val_col.metric("Toplam Portföy Değeri", f"{total_value:,.2f} TL")
    pnl_col.metric("Toplam Kar/Zarar", f"{total_pnl:,.2f} TL", delta=f"{total_return:.2f}%")
    ret_col.metric("Toplam Getiri", f"{total_return:.2f}%")

    # --- İşlem Silme ---
    with st.expander("İşlem Geçmişi ve Silme"):
        st.dataframe(portfolio_df)
        ids_to_remove = st.multiselect(
            "Silmek istediğiniz işlemleri seçin (ID'ye göre):", portfolio_df['id']
        )
        if st.button("Seçili İşlemleri Sil") and ids_to_remove:
            db.remove_transactions(ids_to_remove)
            st.rerun()

def alarm_manager_page():
    """Alarmları yönetmek için kullanıcı arayüzü."""
    st.header("🔔 Fiyat Alarmları Yönetimi")

    st.info(
        """
        Bu özellik, belirlediğiniz bir hisse senedi hedef fiyata ulaştığında size **masaüstü bildirimi** gönderir.
        
        **Kullanım:**
        1. Aşağıdaki formu kullanarak bir veya daha fazla alarm kurun.
        2. Alarmların aktif olarak kontrol edilmesi için, bu Streamlit uygulamasının çalıştığı terminale ek olarak **yeni bir terminal penceresi** açın.
        3. Yeni terminalde `python alarm_checker.py` komutunu çalıştırın.
        
        *Bu komutu çalıştırdığınız pencere açık kaldığı sürece alarmlarınız kontrol edilecektir.*
        """
    )
    
    st.subheader("Yeni Alarm Kur")
    with st.form("new_alarm_form", clear_on_submit=True):
        all_stocks = sorted(list(set(stock for group in HISSE_GRUPPARI.values() for stock in group)))
        
        c1, c2, c3 = st.columns(3)
        hisse = c1.selectbox("Hisse Kodu", all_stocks)
        condition = c2.selectbox("Koşul", ["Fiyat >=", "Fiyat <="])
        value = c3.number_input("Hedef Fiyat", min_value=0.01, format="%.2f")
        
        if st.form_submit_button("Alarm Kur", use_container_width=True):
            if hisse and condition and value > 0:
                db.add_alarm(hisse, condition, value)
                st.success(f"{hisse} için alarm başarıyla kuruldu: {condition} {value}")
                st.rerun()
            else:
                st.warning("Lütfen tüm alanları doğru bir şekilde doldurun.")

    st.divider()

    st.subheader("Mevcut Alarmlar")
    all_alarms_df = db.get_all_alarms()

    if all_alarms_df.empty:
        st.info("Henüz kurulmuş bir alarmınız yok.")
    else:
        # Silme butonları için her satırı işle
        for index, row in all_alarms_df.iterrows():
            col1, col2, col3, col4, col5 = st.columns([2, 2, 2, 2, 1])
            col1.text(row['hisse'])
            col2.text(f"{row['condition_type']} {row['value']:.2f}")
            
            status = row['status']
            if status == 'active':
                col3.success("Aktif")
            elif status == 'triggered':
                col3.error("Tetiklendi")
            else:
                col3.write(status)
                
            col4.text(pd.to_datetime(row['created_at']).strftime('%Y-%m-%d %H:%M'))
            
            # Her satır için benzersiz bir anahtar ile silme butonu
            if col5.button("Sil", key=f"delete_{row['id']}"):
                db.delete_alarm(row['id'])
                st.rerun()


# --- ANA UYGULAMA AKIŞI ---
def main():
    st.title("📊 BIST Hisse Senedi Analiz ve Portföy Platformu")
    
    # Ana sekmeleri oluştur
    analysis_tab, portfolio_tab, alarm_tab = st.tabs(
        ["📈 Analiz Platformu", "💼 Portföy Yönetimi", "🔔 Alarmlar"]
    )
    with analysis_tab:
        analyzer_main_page()
    with portfolio_tab:
        portfolio_manager_page()
    with alarm_tab:
        alarm_manager_page()


if __name__ == "__main__":
    main()
