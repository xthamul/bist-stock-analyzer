import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import logging
from helpers.data_handler import (
    get_stock_data as get_stock_data_native,
    get_fundamental_data as get_fundamental_data_native,
    filter_data_by_date,
    calculate_indicators,
    convert_dataframe_for_streamlit,
)
from helpers.plotter import plot_candlestick_chart, plot_financial_trends
from helpers.ui_components import (
    generate_technical_summary,
    generate_fundamental_summary,
    display_financial_ratios,
)
from helpers.backtester import run_backtest, optimize_strategy, EmaCross, RsiOscillator
import helpers.database as db
from constants import HISSE_GRUPPARI, ZAMAN_ARALIKLARI

# --- Kurulumlar ---
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s", filename="app.log", filemode="w")
db.init_db()
st.set_page_config(page_title="BIST Hisse Senedi Analiz Platformu", page_icon="📊", layout="wide")

# --- Veri Çekme Fonksiyonları (Cache ile) ---
@st.cache_data(ttl=3600)
def get_stock_data(hisse_kodu, interval):
    try:
        return get_stock_data_native(hisse_kodu, interval)
    except Exception as e:
        st.error(f"{hisse_kodu} için teknik veriler çekilirken hata oluştu: {e}")
        return None

@st.cache_data(ttl=86400)
def get_fundamental_data(hisse_kodu):
    try:
        return get_fundamental_data_native(hisse_kodu)
    except Exception as e:
        st.error(f"{hisse_kodu} için temel veriler çekilirken hata oluştu: {e}")
        return None

# --- Arayüz Gösterim Fonksiyonları ---
@st.cache_data
def convert_df_to_csv(df):
    return df.to_csv().encode("utf-8")

def     display_technical_analysis(veri, hisse_kodu_yf, interval_display, selected_indicators, show_support_resistance, show_fibonacci):
    st.header(f"{hisse_kodu_yf} - Teknik Grafik")
    plotly_fig = plot_candlestick_chart(veri, hisse_kodu_yf, interval_display, "Detaylı", selected_indicators, show_support_resistance, show_fibonacci=show_fibonacci)
    st.plotly_chart(plotly_fig, use_container_width=True)
    csv = convert_df_to_csv(veri)
    st.download_button("📥 Veriyi CSV Olarak İndir", csv, f"{hisse_kodu_yf}_{interval_display}_data.csv", "text/csv")
    with st.expander("Teknik Analiz Özeti ve Yorumlar", expanded=True):
        summary = generate_technical_summary(veri)
        st.markdown(summary)

def display_fundamental_analysis(hisse_kodu_yf):
    st.header(f"{hisse_kodu_yf} - Temel Veriler")
    data = get_fundamental_data(hisse_kodu_yf)
    if data and data.get('info'):
        info, financials, balance_sheet, cashflow = data['info'], data['financials'], data['balance_sheet'], data['cashflow']
        summary_tab, ratios_tab, charts_tab, statements_tab = st.tabs(["Özet", "Oranlar", "Grafikler", "Tablolar"])
        with summary_tab:
            st.subheader("Şirket Künyesi")
            _, key_info_text = generate_fundamental_summary(info, as_markdown=False)
            st.text(key_info_text)
        with ratios_tab:
            ratios_df = display_financial_ratios(info, financials, balance_sheet)
            ratios_df = convert_dataframe_for_streamlit(ratios_df)
            st.dataframe(ratios_df.style.format("{:.2f}"))
        with charts_tab:
            st.plotly_chart(plot_financial_trends(financials, cashflow), use_container_width=True)
        with statements_tab:
            st.subheader("Gelir Tablosu"); financials = convert_dataframe_for_streamlit(financials); st.dataframe(financials)
            st.subheader("Bilanço"); balance_sheet = convert_dataframe_for_streamlit(balance_sheet); st.dataframe(balance_sheet)
            st.subheader("Nakit Akış Tablosu"); cashflow = convert_dataframe_for_streamlit(cashflow); st.dataframe(cashflow)
    else:
        st.warning("Temel veriler alınamadı.")

def display_backtesting(veri, hisse_kodu_yf):
    st.header(f"{hisse_kodu_yf} - Strateji Testi ve Optimizasyon")
    test_mode = st.radio("Çalışma Modu", ["Tekli Test", "Optimizasyon"], horizontal=True)
    strategy_options = {"EMA Kesişimi": EmaCross, "RSI Osilatörü": RsiOscillator}
    selected_strategy_name = st.selectbox("Test Edilecek Strateji:", list(strategy_options.keys()))
    selected_strategy_class = strategy_options[selected_strategy_name]

    with st.form(key=f"backtest_form_{selected_strategy_name}_{test_mode}"):
        st.subheader(f"{selected_strategy_name} Parametreleri - {test_mode}")
        params = {}
        initial_cash = st.number_input("Başlangıç Nakiti", 1000, 1000000, 100000, 1000)
        commission = st.slider("Komisyon Oranı (%)", 0.0, 1.0, 0.2, 0.01) / 100

        if selected_strategy_name == "EMA Kesişimi":
            if test_mode == "Tekli Test":
                params['n1'], params['n2'] = st.number_input("Kısa EMA", 1, 200, 50), st.number_input("Uzun EMA", 1, 500, 200)
            else:
                c1, c2, c3 = st.columns(3); params['n1'] = range(c1.number_input("n1 Başla", 1, 200, 10), c2.number_input("n1 Bitir", 1, 200, 50), c3.number_input("n1 Adım", 1, 20, 5))
                c1, c2, c3 = st.columns(3); params['n2'] = range(c1.number_input("n2 Başla", 1, 500, 100), c2.number_input("n2 Bitir", 1, 500, 200), c3.number_input("n2 Adım", 1, 50, 10))
        elif selected_strategy_name == "RSI Osilatörü":
            if test_mode == "Tekli Test":
                params['rsi_window'], params['buy_threshold'], params['sell_threshold'] = st.number_input("RSI Per.", 1, 100, 14), st.number_input("Alım Eşiği", 1, 100, 30), st.number_input("Satım Eşiği", 1, 100, 70)
            else:
                c1, c2, c3 = st.columns(3); params['rsi_window'] = range(c1.number_input("RSI Başla", 5, 50, 10), c2.number_input("RSI Bitir", 5, 50, 20), c3.number_input("RSI Adım", 1, 10, 2))

        if st.form_submit_button(f"{test_mode} Çalıştır"):
            spinner_msg = "Strateji optimize ediliyor..." if test_mode == "Optimizasyon" else "Strateji test ediliyor..."
            with st.spinner(spinner_msg):
                try:
                    backtest_data = veri[['open', 'high', 'low', 'close', 'volume']].copy()
                    if test_mode == "Tekli Test":
                        stats, plot_fig = run_backtest(selected_strategy_class, backtest_data, initial_cash, commission, **params)
                        st.subheader("Performans Sonuçları"); stats_df = stats.to_frame(name='Value'); st.dataframe(stats_df)
                        st.subheader("İşlem Grafiği"); st.bokeh_chart(plot_fig, use_container_width=True)
                    else:
                        stats, best_strategy = optimize_strategy(selected_strategy_class, backtest_data, initial_cash, commission, **params)
                        st.subheader("Optimizasyon Sonuçları"); stats = convert_dataframe_for_streamlit(stats); st.dataframe(stats)
                        st.subheader("En İyi Strateji Parametreleri"); st.write(best_strategy)
                except Exception as e:
                    st.error(f"{test_mode} sırasında bir hata oluştu: {e}")

# --- ANA SAYFA YAPILARI ---
def analyzer_main_page():
    st.sidebar.header("Kontrol Paneli")
    grup_secim = st.sidebar.selectbox("Hisse Grubu:", list(HISSE_GRUPPARI.keys()), index=0)
    hisseler = sorted(HISSE_GRUPPARI.get(grup_secim, []))
    
    default_hisse_index = 0
    if 'hisse_secim' in st.session_state and st.session_state.hisse_secim in hisseler:
        default_hisse_index = hisseler.index(st.session_state.hisse_secim)

    hisse_secim = st.sidebar.selectbox("Hisse Senedi:", hisseler, index=default_hisse_index)
    
    today = datetime.today()
    start_date = st.sidebar.date_input('Başlangıç Tarihi', today - timedelta(days=365))
    end_date = st.sidebar.date_input('Bitiş Tarihi', today)
    interval_display = st.sidebar.selectbox("Zaman Aralığı:", list(ZAMAN_ARALIKLARI.keys()), index=3)
    available_indicators = ["EMA (8, 13, 21)", "Bollinger Bantları", "VWAP", "Ichimoku Cloud", "RSI", "StochRSI", "MACD", "ADX", "OBV"]
    selected_indicators = st.sidebar.multiselect("Göstergeler:", available_indicators, default=available_indicators)
    show_support_resistance = st.sidebar.checkbox("Destek/Direnç Göster", value=True)
    show_fibonacci = st.sidebar.checkbox("Fibonacci Geri Çekilme Seviyeleri Göster", value=False)

    if st.sidebar.button("Analiz Et", use_container_width=True, type="primary"):
        if start_date > end_date:
            st.sidebar.error("Hata: Başlangıç tarihi, bitiş tarihinden sonra olamaz.")
        else:
            st.session_state.analysis_requested = True
            st.session_state.hisse_secim = hisse_secim
            st.session_state.start_date = start_date
            st.session_state.end_date = end_date
            st.session_state.interval_display = interval_display
            st.session_state.selected_indicators = selected_indicators
            st.session_state.show_support_resistance = show_support_resistance
            st.session_state.show_fibonacci = show_fibonacci
            st.rerun()

    if st.session_state.get('analysis_requested', False):
        hisse_kodu_yf = f"{st.session_state.hisse_secim}.IS"
        interval_code = ZAMAN_ARALIKLARI[st.session_state.interval_display]
        with st.spinner(f"{hisse_kodu_yf} için veriler çekiliyor ve analiz ediliyor..."):
            veri_raw = get_stock_data(hisse_kodu_yf, interval_code)
            if veri_raw is not None:
                veri_hesaplanmis = calculate_indicators(veri_raw.copy())
                veri_filtrelenmis = filter_data_by_date(veri_hesaplanmis, start_date=st.session_state.start_date, end_date=st.session_state.end_date)
                if veri_filtrelenmis.empty:
                    st.warning("Seçilen tarih aralığı için veri bulunamadı.")
                    return

                st.success(f"{hisse_kodu_yf} analizi tamamlandı.")
                ana_tab, temel_tab, backtest_tab = st.tabs(["📈 Teknik Analiz", "🏢 Temel Analiz", "🧪 Strateji Testi"])
                with ana_tab:
                    display_technical_analysis(veri_filtrelenmis, hisse_kodu_yf, st.session_state.interval_display, st.session_state.selected_indicators, st.session_state.show_support_resistance, st.session_state.show_fibonacci)
                with temel_tab:
                    display_fundamental_analysis(hisse_kodu_yf)
                with backtest_tab:
                    display_backtesting(veri_filtrelenmis, hisse_kodu_yf)
            else:
                st.error("Veri çekilemedi.")
    else:
        st.info("Lütfen sol taraftaki menüden bir hisse seçip 'Analiz Et' butonuna tıklayın.")

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
            db.add_transaction(ticker, quantity, price, date)
            st.success(f"{ticker} portföye eklendi!")

    st.divider()
    portfolio_df = db.get_all_transactions()
    if portfolio_df.empty:
        st.info("Portföyünüz boş.")
        return

    st.subheader("Mevcut Portföy")
    display_df = portfolio_df.copy()
    unique_tickers = display_df['hisse'].unique()
    current_prices = {}
    with st.spinner("Güncel fiyatlar çekiliyor..."):
        for t in unique_tickers:
            data = get_stock_data(f"{t}.IS", "1d")
            if data is not None and not data.empty:
                current_prices[t] = data['close'].iloc[-1]
            else:
                current_prices[t] = 0

    display_df["Güncel Fiyat"] = display_df['hisse'].map(current_prices)
    display_df["Maliyet"] = display_df["miktar"] * display_df["alis_fiyati"]
    display_df["Güncel Değer"] = display_df["miktar"] * display_df["Güncel Fiyat"]
    display_df["Kar/Zarar"] = display_df["Güncel Değer"] - display_df["Maliyet"]
    display_df = convert_dataframe_for_streamlit(display_df)
    st.dataframe(display_df.style.format(precision=2))

    total_value = display_df["Güncel Değer"].sum()
    st.metric("Toplam Portföy Değeri", f"{total_value:,.2f} TL")

    st.subheader("İşlem Sil")
    ids_to_remove = st.multiselect("Silmek istediğiniz işlemleri seçin (ID'ye göre):", portfolio_df['id'])
    if st.button("Seçili İşlemleri Sil") and ids_to_remove:
        db.remove_transactions(ids_to_remove)
        st.rerun()

# --- ANA UYGULAMA AKIŞI ---
def main():
    st.title("📊 BIST Hisse Senedi Analiz ve Portföy Platformu")
    analysis_tab, portfolio_tab = st.tabs(["📈 Analiz Platformu", "💼 Portföy Yönetimi"])
    with analysis_tab:
        analyzer_main_page()
    with portfolio_tab:
        portfolio_manager_page()

if __name__ == "__main__":
    main()