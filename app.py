import streamlit as st
import pandas as pd
import numpy as np
import traceback
from datetime import datetime, timedelta
from tenacity import retry, stop_after_attempt, wait_fixed
from helpers.exceptions import DataFetchError
import logging

# --- Logging Kurulumu ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='app.log',
    filemode='w' # Her çalıştırmada log dosyasını baştan yaz
)

# Helper modüllerini ve sabitleri import et
from helpers.data_handler import (
    get_stock_data as get_stock_data_native,
    get_fundamental_data as get_fundamental_data_native,
    filter_data_by_date,
    get_sector_peers as get_sector_peers_native,
    calculate_indicators # Moved to the end
)
from helpers.plotter import plot_analysis_plotly, plot_comparison_plotly, plot_financial_trends, plot_prediction_results
from helpers.ui_components import generate_technical_summary, generate_fundamental_summary, display_financial_ratios
from helpers.backtester import run_backtest
from helpers.predictor import (
    get_stock_data_for_prediction,
    calculate_prediction_features,
    create_target_variable,
    train_prediction_model,
    get_latest_prediction
)
from constants import HISSE_GRUPPARI, ZAMAN_ARALIKLARI

# --- Sayfa Konfigürasyonu ---
st.set_page_config(
    page_title="BIST Hisse Senedi Analiz Platformu",
    page_icon="📊",
    layout="wide"
)

# --- Streamlit'e Özgü Veri Çekme ve Önbelleğe Alma Fonksiyonları ---
@st.cache_data(ttl=3600)
@retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
def get_stock_data(hisse_kodu, interval):
    """Native veri çekme fonksiyonunu retry ve cache ile sarmalar."""
    try:
        return get_stock_data_native(hisse_kodu, interval)
    except Exception as e:
        logging.error(f"{hisse_kodu} için teknik veriler çekilirken hata oluştu: {traceback.format_exc()}")
        st.error(f"{hisse_kodu} için teknik veriler çekilirken hata oluştu: {e}")
        raise e # Tenacity'nin tekrar denemesi için hatayı yeniden fırlat

@st.cache_data(ttl=3600)
@retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
def get_fundamental_data(hisse_kodu):
    """Native temel veri çekme fonksiyonunu retry ve cache ile sarmalar."""
    try:
        return get_fundamental_data_native(hisse_kodu)
    except Exception as e:
        logging.error(f"{hisse_kodu} için temel veriler çekilirken hata oluştu: {traceback.format_exc()}")
        st.error(f"{hisse_kodu} için temel veriler çekilirken hata oluştu: {e}")
        raise e

@st.cache_data(ttl=86400)
def get_sector_peers(hisse_kodu):
    try:
        return get_sector_peers_native(hisse_kodu)
    except Exception as e:
        logging.error(f"{hisse_kodu} için sektör verileri çekilirken hata oluştu: {traceback.format_exc()}")
        st.error(f"{hisse_kodu} için sektör verileri çekilirken hata oluştu: {e}")
        return None, None

# --- Ana Arayüz Fonksiyonları ---
@st.cache_data
def convert_df_to_csv(df):
    return df.to_csv().encode('utf-8')

def display_technical_analysis(veri, hisse_kodu_yf, interval_display, analysis_type, selected_indicators, show_support_resistance=False):
    st.header(f"{hisse_kodu_yf} - Teknik Grafik")
    plotly_fig = plot_analysis_plotly(veri, hisse_kodu_yf, interval_display, analysis_type, selected_indicators, show_support_resistance=show_support_resistance)
    st.plotly_chart(plotly_fig, use_container_width=True)
    
    csv = convert_df_to_csv(veri)
    st.download_button(
        label="📥 Veriyi CSV Olarak İndir",
        data=csv,
        file_name=f'{hisse_kodu_yf}_{interval_display}_data.csv',
        mime='text/csv',
    )

    with st.expander("Teknik Analiz Özeti ve Yorumlar", expanded=True):
        summary = generate_technical_summary(veri)
        st.markdown(summary)

def display_prediction(hisse_kodu_yf):
    st.header(f"{hisse_kodu_yf} - Fiyat Yönü Tahmini")
    st.info("Bu bölüm, geçmiş verilere dayanarak hisse senedinin bir sonraki günkü kapanış fiyatının yönünü (artış/azalış) tahmin eder. Model, en iyi parametreleri bulmak için GridSearchCV kullanır, bu nedenle eğitim süresi biraz daha uzun olabilir.")

    with st.spinner("En iyi tahmin modeli bulunuyor ve eğitiliyor... Bu işlem birkaç dakika sürebilir."):
        try:
            # Veri çekme
            data = get_stock_data_for_prediction(hisse_kodu_yf)

            if data is not None and not data.empty:
                # Özellik hesaplama
                data_with_features = calculate_prediction_features(data)
                
                # Hedef değişken oluşturma
                data_final = create_target_variable(data_with_features)

                if not data_final.empty:
                    # Modeli eğitme ve sonuçları alma
                    model, features, accuracy, report_df, test_results, best_params = train_prediction_model(data_final)
                    
                    # En son tahmin
                    latest_prediction_text = get_latest_prediction(model, data_final, features)
                    st.success("Tahmin başarıyla tamamlandı!")
                    st.subheader("Güncel Tahmin")
                    st.write(f"**Tahmin Sonucu:** {latest_prediction_text}")

                    st.subheader("Model Performansı (Test Verisi Üzerinden)")
                    st.write(f"En iyi model parametreleri: `{best_params}`")
                    col1, col2 = st.columns(2)
                    col1.metric("Model Doğruluğu", f"{accuracy:.2%}")
                    
                    st.write("**Sınıflandırma Raporu:**")
                    st.dataframe(report_df)

                    st.subheader("Tahmin Sonuçlarının Görselleştirilmesi")
                    # Test periyodundaki kapanış fiyatlarını al
                    test_close_prices = data['close'].loc[test_results.index]
                    prediction_fig = plot_prediction_results(test_results, test_close_prices)
                    st.plotly_chart(prediction_fig, use_container_width=True)

                else:
                    st.warning("Tahmin için yeterli veri bulunamadı veya hedef değişken oluşturulamadı.")
            else:
                st.warning(f"{hisse_kodu_yf} için tahmin verisi çekilemedi.")
        except Exception as e:
            logging.error(f"Tahmin sırasında bir hata oluştu: {traceback.format_exc()}")
            st.error(f"Tahmin sırasında bir hata oluştu: {e}")
            st.code(traceback.format_exc())

def display_sector_analysis(hisse_kodu_yf, info):
    st.subheader("Sektör Karşılaştırması")
    sector, peers = get_sector_peers(hisse_kodu_yf)
    
    if not sector or not peers:
        st.info("Sektör verisi veya karşılaştırılacak benzer şirket bulunamadı.")
        return

    st.write(f"**{info.get('longName')}** şirketi **{sector}** sektöründe yer almaktadır.")
    st.write(f"Bu sektördeki benzer şirketler: {(', '.join(peers))}")

    metrics = ['trailingPE', 'priceToBook', 'dividendYield', 'returnOnEquity', 'profitMargins']
    peer_data = []

    progress_bar = st.progress(0, text="Benzer şirket verileri çekiliyor...")
    for i, peer_ticker in enumerate(peers):
        try:
            peer_info_data = get_fundamental_data(f"{peer_ticker}.IS")
            if peer_info_data and peer_info_data.get('info'):
                peer_info = peer_info_data['info']
                peer_metrics = {'Hisse': peer_ticker}
                for metric in metrics:
                    peer_metrics[metric] = peer_info.get(metric)
                peer_data.append(peer_metrics)
        except Exception:
            continue
        finally:
            progress_bar.progress((i + 1) / len(peers))
    progress_bar.empty()

    if not peer_data:
        st.warning("Sektördeki diğer şirketler için veri toplanamadı.")
        return

    df_peers = pd.DataFrame(peer_data).set_index('Hisse').astype(float)
    df_sector_mean = df_peers.mean().to_frame(name="Sektör Ortalaması")

    main_stock_data = {}
    for metric in metrics:
        main_stock_data[metric] = info.get(metric)
    df_main_stock = pd.Series(main_stock_data, name=hisse_kodu_yf.split('.')[0]).to_frame()

    df_comparison = pd.concat([df_main_stock, df_sector_mean], axis=1)
    df_comparison.index.name = "Metrik"
    st.dataframe(df_comparison.style.format("{:.2f}"))

def display_fundamental_analysis(hisse_kodu_yf):
    st.header(f"{hisse_kodu_yf} - Temel Veriler")
    try:
        data = get_fundamental_data(hisse_kodu_yf)
        if data and data.get('info'):
            info = data['info']
            financials = data.get('financials')
            balance_sheet = data.get('balance_sheet')
            cashflow = data.get('cashflow')

            summary_tab, ratios_tab, charts_tab, statements_tab = st.tabs(["Özet ve Yorumlar", "Finansal Oranlar", "Finansal Grafikler", "Finansal Tablolar"])

            with summary_tab:
                st.subheader("Şirket Künyesi")
                _, key_info_text = generate_fundamental_summary(info, as_markdown=False)
                st.text(key_info_text)

                st.subheader("Yapay Zeka Destekli Temel Yorumlar")
                fundamental_summary = generate_fundamental_summary(info, as_markdown=True)
                st.markdown(fundamental_summary)
                
                st.subheader("Sektör Karşılaştırması")
                display_sector_analysis(hisse_kodu_yf, info)

            with ratios_tab:
                st.subheader("Finansal Oranlar")
                ratios_df = display_financial_ratios(info, financials, balance_sheet)
                st.dataframe(ratios_df.style.format("{:.2f}"))

            with charts_tab:
                st.subheader("Finansal Trend Grafikleri")
                financial_trends_fig = plot_financial_trends(financials, cashflow)
                st.plotly_chart(financial_trends_fig, use_container_width=True)

            with statements_tab:
                st.subheader("Finansal Tablolar")
                tablo_gelir, tablo_bilanco, tablo_nakit = st.tabs(["Gelir Tablosu", "Bilanço", "Nakit Akış Tablosu"])
                with tablo_gelir:
                    st.dataframe(financials, use_container_width=True)
                with tablo_bilanco:
                    st.dataframe(balance_sheet, use_container_width=True)
                with tablo_nakit:
                    st.dataframe(cashflow, use_container_width=True)
        else:
            st.warning("Temel veriler alınamadı.")
    except DataFetchError as e:
        logging.error(f"Temel veri hatası: {traceback.format_exc()}")
        st.error(f"Temel veriler çekilirken bir hata oluştu: {e}")
    except Exception as e:
        logging.error(f"Beklenmedik bir temel veri hatası: {traceback.format_exc()}")
        st.error(f"Beklenmedik bir hata oluştu: {e}")
        st.code(traceback.format_exc())

def display_comparison(hisseler, hisse_secim, interval_code, start_date, end_date):
    st.header("Hisse Karşılaştırma")
    hisse2_secim = st.selectbox(
        "Karşılaştırılacak Hisse:", 
        [h for h in hisseler if h != hisse_secim],
        index=0
    )

    if hisse2_secim:
        hisse1_yf = f"{hisse_secim}.IS"
        hisse2_yf = f"{hisse2_secim}.IS"

        with st.spinner(f'{hisse1_yf} ve {hisse2_yf} verileri çekiliyor...'):
            try:
                data1 = get_stock_data(hisse1_yf, interval_code)
                data2 = get_stock_data(hisse2_yf, interval_code)

                if data1 is not None and data2 is not None:
                    filtered_data1 = filter_data_by_date(data1, start_date=start_date, end_date=end_date)
                    filtered_data2 = filter_data_by_date(data2, start_date=start_date, end_date=end_date)

                    if not filtered_data1.empty and not filtered_data2.empty:
                        comparison_fig = plot_comparison_plotly(filtered_data1, filtered_data2, hisse1_yf, hisse2_yf)
                        st.plotly_chart(comparison_fig, use_container_width=True)
                    else:
                        st.warning("Seçilen tarih aralığı için her iki hissede de yeterli veri bulunamadı.")
                else:
                    st.error("Hisselerden biri veya her ikisi için veri çekilemedi.")
            except DataFetchError as e:
                st.error(f"Veri çekme hatası: {e}")
            except Exception as e:
                logging.error(f"Karşılaştırma hatası: {traceback.format_exc()}")
                st.error(f"Beklenmedik bir hata oluştu: {e}")
                st.code(traceback.format_exc())

def display_portfolio_summary(portfolio_tickers, interval_code):
    st.header("İzleme Listesi Özeti")
    summary_data = []
    progress_bar = st.progress(0, "İzleme listesi verileri çekiliyor...")
    
    for i, ticker in enumerate(portfolio_tickers):
        hisse_kodu_yf = f"{ticker.strip().upper()}.IS"
        try:
            data = get_stock_data(hisse_kodu_yf, interval_code)
            if data is not None and not data.empty:
                info_data = get_fundamental_data(hisse_kodu_yf)
                if info_data and info_data.get('info'):
                    info = info_data['info']
                    son_veri = data.iloc[-1]
                    summary_data.append({
                        "Hisse": hisse_kodu_yf,
                        "Son Fiyat": f"{son_veri['close']:.2f}",
                        "Piy. Değ.": f"{info.get('marketCap', 0) / 1e9:.2f} Milyar",
                        "F/K": f"{info.get('trailingPE', 0):.2f}",
                        "PD/DD": f"{info.get('priceToBook', 0):.2f}",
                        "Hacim": f"{son_veri['volume']:,.0f}"
                    })
        except DataFetchError as e:
            st.warning(f"{hisse_kodu_yf} için veri çekilemedi: {e}")
        except Exception as e:
            logging.error(f"Portföy özeti hatası ({hisse_kodu_yf}): {traceback.format_exc()}")
            st.error(f"{hisse_kodu_yf} için beklenmedik bir hata oluştu: {e}")
        progress_bar.progress((i + 1) / len(portfolio_tickers))
    progress_bar.empty()

    if summary_data:
        df_summary = pd.DataFrame(summary_data)
        st.dataframe(df_summary, use_container_width=True)
    else:
        st.warning("İzleme listesindeki hisseler için veri bulunamadı.")

def display_backtesting(veri, hisse_kodu_yf):
    st.header(f"{hisse_kodu_yf} - EMA Crossover Strateji Testi")
    with st.form(key='backtest_form'):
        st.write("Strateji: 50 günlük EMA, 200 günlük EMA'yı yukarı kestiğinde AL, aşağı kestiğinde SAT.")
        initial_cash = st.number_input("Başlangıç Nakiti", min_value=1000, value=100000, step=1000)
        commission = st.slider("Komisyon Oranı (%)", min_value=0.0, max_value=1.0, value=0.2, step=0.01) / 100
        submit_button = st.form_submit_button(label="Backtest'i Çalıştır")

    if submit_button:
        with st.spinner("Strateji geçmiş veriler üzerinde test ediliyor..."):
            try:
                stats, plot_fig = run_backtest(veri, cash=initial_cash, commission=commission)
                st.success("Backtest tamamlandı!")
                st.subheader("Performans Sonuçları")
                # Stats bir Seri ise, Timedelta içerenleri string'e çevir
                if isinstance(stats, pd.Series):
                    stats_for_display = stats.astype(str)
                else: # DataFrame ise eski mantığı kullan (daha sağlam)
                    stats_for_display = stats.copy()
                    for col in stats_for_display.select_dtypes(include=['timedelta64[ns]']).columns:
                        stats_for_display[col] = stats_for_display[col].astype(str)
                st.dataframe(stats_for_display)
                st.subheader("İşlem Grafiği")
                st.bokeh_chart(plot_fig, use_container_width=True)
            except Exception as e:
                logging.error(f"Backtest hatası: {traceback.format_exc()}")
                st.error(f"Backtest sırasında bir hata oluştu: {e}")
                st.code(traceback.format_exc())

def setup_sidebar():
    st.sidebar.header("Kontrol Paneli")
    analysis_mode = st.sidebar.radio("Analiz Modu", ["Tekil Hisse Analizi", "İzleme Listesi"], horizontal=True)

    hisse_secim = None
    portfolio_input = None
    start_date = None
    end_date = None
    analysis_type = None
    selected_indicators = []
    show_support_resistance = False

    if analysis_mode == "Tekil Hisse Analizi":
        grup_secim = st.sidebar.selectbox("Hisse Grubu:", list(HISSE_GRUPPARI.keys()), index=0)
        hisseler = sorted(HISSE_GRUPPARI.get(grup_secim, []))
        default_index = hisseler.index("GARAN") if "GARAN" in hisseler else 0
        hisse_secim = st.sidebar.selectbox("Hisse Senedi:", hisseler, index=default_index)
        
        today = datetime.today()
        start_date = st.sidebar.date_input('Başlangıç Tarihi', today - timedelta(days=365))
        end_date = st.sidebar.date_input('Bitiş Tarihi', today)
        analysis_type = st.sidebar.selectbox("Analiz Tipi:", ["Detaylı", "Basit"], index=0)

        if analysis_type == "Detaylı":
            st.sidebar.subheader("Gösterge Seçimi")
            available_indicators = [
                "EMA (8, 13, 21)", "Bollinger Bantları", "VWAP", "Ichimoku Cloud", 
                "RSI", "StochRSI", "MACD", "ADX", "OBV"
            ]
            selected_indicators = st.sidebar.multiselect(
                "Grafikte gösterilecek indikatörleri seçin:",
                available_indicators,
                default=available_indicators # Varsayılan olarak hepsi seçili
            )
            st.sidebar.subheader("Grafik Ayarları")
            show_support_resistance = st.sidebar.checkbox("Destek/Direnç Seviyelerini Göster", value=True)

    else:
        portfolio_input = st.sidebar.text_area("İzleme Listesi (Hisseleri virgülle ayırın)", "GARAN, THYAO, EREGL, BIMAS")
        hisseler = sorted(HISSE_GRUPPARI.get("Tüm Hisseler", []))

    interval_display = st.sidebar.selectbox("Zaman Aralığı:", list(ZAMAN_ARALIKLARI.keys()), index=3)
    interval_code = ZAMAN_ARALIKLARI[interval_display]
    
    analyze_button = st.sidebar.button("Analiz Et", use_container_width=True, type="primary")

    return (analysis_mode, hisse_secim, portfolio_input, hisseler, 
            interval_code, interval_display, start_date, end_date, 
            analysis_type, analyze_button, selected_indicators, show_support_resistance)

def handle_single_stock_analysis(hisse_secim, interval_code, interval_display, start_date, end_date, analysis_type, hisseler, selected_indicators, show_support_resistance):
    if start_date > end_date:
        st.error("Hata: Başlangıç tarihi, bitiş tarihinden sonra olamaz.")
        return

    hisse_kodu_yf = f"{hisse_secim}.IS"
    
    with st.spinner(f'{hisse_kodu_yf} için veriler çekiliyor ve analiz ediliyor...'):
        try:
            veri_raw = get_stock_data(hisse_kodu_yf, interval_code)
            veri_hesaplanmis = calculate_indicators(veri_raw.copy())
            veri_filtrelenmis = filter_data_by_date(veri_hesaplanmis, start_date=start_date, end_date=end_date)
            
            if veri_filtrelenmis.empty:
                st.warning("Seçilen tarih aralığı için veri bulunamadı.")
                return

            st.success(f"{hisse_kodu_yf} analizi tamamlandı.")
            ana_tab, karsilastirma_tab, temel_tab, backtest_tab, prediction_tab = st.tabs(["📈 Teknik Analiz", "🆚 Hisse Karşılaştırma", "🏢 Temel Analiz", "🧪 Strateji Testi", "🔮 Tahmin"])
            with ana_tab:
                display_technical_analysis(veri_filtrelenmis, hisse_kodu_yf, interval_display, analysis_type, selected_indicators, show_support_resistance)
            with karsilastirma_tab:
                display_comparison(hisseler, hisse_secim, interval_code, start_date, end_date)
            with temel_tab:
                display_fundamental_analysis(hisse_kodu_yf)
            with backtest_tab:
                display_backtesting(veri_filtrelenmis, hisse_kodu_yf)
            with prediction_tab:
                display_prediction(hisse_kodu_yf)

        except DataFetchError as e:
            st.error(f"Veri çekme hatası: {e}")
        except Exception as e:
            logging.error(f"Tekil hisse analizi hatası: {traceback.format_exc()}")
            st.error(f"Beklenmedik bir hata oluştu: {e}")
            st.code(traceback.format_exc())

def handle_portfolio_analysis(portfolio_input, interval_code):
    portfolio_tickers = [ticker.strip() for ticker in portfolio_input.split(",") if ticker.strip()]
    if portfolio_tickers:
        display_portfolio_summary(portfolio_tickers, interval_code)
    else:
        st.warning("Lütfen izleme listesine en az bir hisse senedi girin.")

# --- Ana Uygulama Akışı ---
def main():
    st.title("📊 BIST Hisse Senedi Analiz Platformu")

    (analysis_mode, hisse_secim, portfolio_input, hisseler, 
     interval_code, interval_display, start_date, end_date, 
     analysis_type, analyze_button, selected_indicators, show_support_resistance) = setup_sidebar()

    if 'analysis_requested' not in st.session_state:
        st.session_state.analysis_requested = False
    if analyze_button:
        st.session_state.analysis_requested = True

    if st.session_state.analysis_requested:
        if analysis_mode == "Tekil Hisse Analizi":
            handle_single_stock_analysis(hisse_secim, interval_code, interval_display, start_date, end_date, analysis_type, hisseler, selected_indicators, show_support_resistance)
        elif analysis_mode == "İzleme Listesi":
            handle_portfolio_analysis(portfolio_input, interval_code)
    else:
        st.info("Lütfen sol taraftaki menüden bir analiz modu seçip 'Analiz Et' butonuna tıklayın.")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logging.error(f"Uygulama başlatılırken beklenmedik bir hata oluştu: {traceback.format_exc()}")
        st.error("Uygulama başlatılırken beklenmedik bir hata oluştu.")
        st.error(f"Hata Detayı: {e}")
        st.code(traceback.format_exc())