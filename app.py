import streamlit as st
from datetime import datetime, timedelta
import logging
import traceback
import streamlit_bokeh as st_bokeh
import pandas as pd
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
)
from helpers.ui_components import (
    generate_technical_summary,
    generate_fundamental_summary,
    display_financial_ratios,
    display_sector_comparison,
    generate_ai_analysis,
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


def analyzer_main_page():
    st.sidebar.header("Kontrol Paneli")
    grup_secim = st.sidebar.selectbox(
        "Hisse Grubu:", list(HISSE_GRUPPARI.keys()), index=0
    )
    hisseler = sorted(HISSE_GRUPPARI.get(grup_secim, []))

    default_hisse_index = 0
    if "hisse_secim" in st.session_state and st.session_state.hisse_secim in hisseler:
        default_hisse_index = hisseler.index(st.session_state.hisse_secim)

    hisse_secim = st.sidebar.selectbox(
        "Hisse Senedi:", hisseler, index=default_hisse_index
    )

    today = datetime.today()
    start_date = st.sidebar.date_input("Başlangıç Tarihi", today - timedelta(days=365))
    end_date = st.sidebar.date_input("Bitiş Tarihi", today)
    interval_display = st.sidebar.selectbox(
        "Zaman Aralığı:", list(ZAMAN_ARALIKLARI.keys()), index=3
    )
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
        default=[
            "EMA KISA (5, 20)",
            "EMA UZUN (50, 200)",
            "Bollinger Bantları",
            "RSI",
            "MACD",
        ],
    )
    show_support_resistance = st.sidebar.checkbox("Destek/Direnç Göster", value=True)
    show_fibonacci = st.sidebar.checkbox(
        "Fibonacci Geri Çekilme Seviyeleri Göster", value=False
    )

    if st.sidebar.button("Analiz Et", use_container_width=True, type="primary"):
        if start_date > end_date:
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
            st.session_state.hisse_secim = hisse_secim
            st.session_state.start_date = start_date
            st.session_state.end_date = end_date
            st.session_state.interval_display = interval_display
            st.session_state.selected_indicators = selected_indicators
            st.session_state.show_support_resistance = show_support_resistance
            st.session_state.show_fibonacci = show_fibonacci
            st.rerun()

    if st.session_state.get("analysis_requested", False):
        hisse_kodu_yf = f"{st.session_state.hisse_secim}.IS"
        interval_code = ZAMAN_ARALIKLARI[st.session_state.interval_display]
        with st.spinner(
            f"{hisse_kodu_yf} için veriler çekiliyor ve analiz ediliyor..."
        ):
            veri_raw = get_stock_data(
                hisse_kodu_yf,
                interval_code,
                start_date=st.session_state.start_date,
                end_date=st.session_state.end_date,
            )
            if veri_raw is not None:
                veri_hesaplanmis = calculate_indicators(veri_raw.copy())
                veri_filtrelenmis = filter_data_by_date(
                    veri_hesaplanmis,
                    start_date=st.session_state.start_date,
                    end_date=st.session_state.end_date,
                )
                if veri_filtrelenmis.empty:
                    st.warning("Seçilen tarih aralığı için veri bulunamadı.")
                    return

                st.success(f"{hisse_kodu_yf} analizi tamamlandı.")
                ana_tab, temel_tab, backtest_tab = st.tabs(
                    ["📈 Teknik Analiz", "🏢 Temel Analiz", "🧪 Strateji Testi"]
                )
                with ana_tab:
                    display_technical_analysis(
                        veri_filtrelenmis,
                        hisse_kodu_yf,
                        st.session_state.interval_display,
                        st.session_state.selected_indicators,
                        st.session_state.show_support_resistance,
                        st.session_state.show_fibonacci,
                    )
                with temel_tab:
                    display_fundamental_analysis(hisse_kodu_yf)
                with backtest_tab:
                    display_backtesting(veri_filtrelenmis, hisse_kodu_yf)
            else:
                st.error("Veri çekilemedi.")
    else:
        st.info(
            "Lütfen sol taraftaki menüden bir hisse seçip 'Analiz Et' butonuna tıklayın."
        )


import pandas as pd

# ... (other imports)

from helpers.plotter import (
    display_candlestick_chart,
    display_financial_trends_chart,
    display_balance_sheet_details_chart,
    display_per_share_values_chart,
    display_dividend_history_chart,
    display_portfolio_performance_chart,
)

# ... (rest of the file until portfolio_manager_page)

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

    # --- Portföy Geçmişi ve Grafik ---
    st.subheader("Portföy Performansı")

    transactions = portfolio_df.copy()
    transactions["tarih"] = pd.to_datetime(transactions["tarih"])

    start_date = transactions["tarih"].min()
    unique_tickers = transactions["hisse"].unique()

    all_prices = pd.DataFrame()
    with st.spinner("Portföy geçmişi için fiyat verileri çekiliyor..."):
        for ticker in unique_tickers:
            try:
                data = get_stock_data(
                    f"{ticker}.IS", "1d", start_date=start_date, end_date=datetime.today()
                )
                if data is not None and not data.empty:
                    all_prices[ticker] = data["close"]
            except Exception as e:
                st.warning(f"{ticker} için geçmiş fiyat verisi çekilemedi: {e}")

    if not all_prices.empty:
        all_prices = all_prices.ffill()

        date_range = pd.date_range(start=start_date, end=datetime.today(), freq='D')
        daily_positions = pd.DataFrame(0.0, index=date_range, columns=unique_tickers)

        # Calculate position changes on transaction dates
        position_changes = transactions.pivot_table(index='tarih', columns='hisse', values='miktar', aggfunc='sum').fillna(0)
        daily_positions.update(position_changes)
        
        # Cumulatively sum positions
        daily_positions = daily_positions.cumsum().ffill()


        daily_values = daily_positions.multiply(all_prices, axis="columns").ffill()
        
        portfolio_history = pd.DataFrame(index=date_range)
        portfolio_history["Total Value"] = daily_values.sum(axis=1)

        display_portfolio_performance_chart(portfolio_history)

    # --- Mevcut Portföy Tablosu ---
    st.subheader("Mevcut Portföy Özeti")
    
    # Calculate weighted average cost and total quantity
    summary_df = transactions.groupby('hisse').apply(lambda x: pd.Series({
        'Miktar': x['miktar'].sum(),
        'Ortalama_Maliyet': (x['alis_fiyati'] * x['miktar']).sum() / x['miktar'].sum()
    })).reset_index()


    current_prices = {}
    with st.spinner("Güncel fiyatlar çekiliyor..."):
        for t in unique_tickers:
            if t in all_prices and not all_prices[t].dropna().empty:
                 current_prices[t] = all_prices[t].dropna().iloc[-1]
            else:
                # Fallback if historical data failed for some reason
                data = get_stock_data(f"{t}.IS", "1d")
                if data is not None and not data.empty:
                    current_prices[t] = data['close'].iloc[-1]
                else:
                    current_prices[t] = 0
    
    summary_df["Güncel Fiyat"] = summary_df['hisse'].map(current_prices)
    summary_df["Toplam Maliyet"] = summary_df["Miktar"] * summary_df["Ortalama_Maliyet"]
    summary_df["Güncel Değer"] = summary_df["Miktar"] * summary_df["Güncel Fiyat"]
    summary_df["Kar/Zarar"] = summary_df["Güncel Değer"] - summary_df["Toplam Maliyet"]
    
    col1, col2 = st.columns(2)
    with col1:
        st.dataframe(summary_df.style.format({
            "Ortalama_Maliyet": "{:,.2f} TL",
            "Güncel Fiyat": "{:,.2f} TL",
            "Toplam Maliyet": "{:,.2f} TL",
            "Güncel Değer": "{:,.2f} TL",
            "Kar/Zarar": "{:,.2f} TL"
        }))
    with col2:
        display_asset_allocation_chart(summary_df)


    total_value = summary_df["Güncel Değer"].sum()
    total_cost = summary_df["Toplam Maliyet"].sum()
    total_pnl = total_value - total_cost
    total_return = (total_pnl / total_cost * 100) if total_cost != 0 else 0

    val_col, pnl_col, ret_col = st.columns(3)
    val_col.metric("Toplam Portföy Değeri", f"{total_value:,.2f} TL")
    pnl_col.metric("Toplam Kar/Zarar", f"{total_pnl:,.2f} TL")
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



# --- ANA UYGULAMA AKIŞI ---
def main():
    st.title("📊 BIST Hisse Senedi Analiz ve Portföy Platformu")
    analysis_tab, portfolio_tab = st.tabs(
        ["📈 Analiz Platformu", "💼 Portföy Yönetimi"]
    )
    with analysis_tab:
        analyzer_main_page()
    with portfolio_tab:
        portfolio_manager_page()


if __name__ == "__main__":
    main()
