import streamlit as st
import pandas as pd
import numpy as np
import traceback
from datetime import datetime, timedelta
from tenacity import retry, stop_after_attempt, wait_fixed

# Helper modüllerini import et
from helpers.data_handler import get_stock_data as get_stock_data_native
from helpers.data_handler import calculate_indicators, get_fundamental_data as get_fundamental_data_native, filter_data_by_date, get_sector_peers as get_sector_peers_native
from helpers.plotter import plot_analysis_plotly, plot_comparison_plotly
from helpers.ui_components import generate_technical_summary, generate_fundamental_summary
from helpers.backtester import run_backtest

# --- Sabitler ve Ayarlar ---
HISSE_GRUPPARI = {
    "BIST 100 Hisseleri": [
        "AKBNK", "GARAN", "ISCTR", "YKBNK", "VAKBN", "THYAO", "ASELS", "TUPRS", "KCHOL", "BIMAS",
        "FROTO", "SISE", "ENKAI", "PETKM", "KOZAL", "TOASO", "KRDMD", "SAHOL", "SASA", "EREGL",
        "ARCLK", "PGSUS", "ALARK", "HEKTS", "TAVHL", "TCELL", "ODAS", "KORDS", "DOHOL", "ZOREN",
        "GWIND", "AGHOL", "AKSA", "OYAKC", "CCOLA", "TRKCM", "ADEL", "ULKER", "LOGO", "ISGYO",
        "MGROS", "GENIL", "ISDMR", "BRISA", "ALKIM", "AKGRT", "BANVT", "CIMSA", "ENJSA", "KARSN",
        "TTRAK", "GOZDE", "SOKM", "ALFAS", "BIOEN", "QUAGR", "BURCE", "DGNMO", "EKGYO", "GUBRF",
        "IZMDC", "MPARK", "NETAS", "PENTA", "TMSN", "TUCLK", "ULAS", "VERUS", "YUNSA"
    ],
    "BIST 30 Hisseleri": [
        "AKBNK", "GARAN", "ISCTR", "YKBNK", "VAKBN", "THYAO", "ASELS", "TUPRS", "KCHOL", "BIMAS",
        "FROTO", "SISE", "ENKAI", "PETKM", "KOZAL", "TOASO", "KRDMD", "SAHOL", "SASA", "EREGL",
        "ARCLK", "PGSUS", "TCELL", "ULKER", "ISDMR", "TAVHL", "KRDMA", "LOGO", "ODAS", "TRKCM"
    ],
    "Tüm Hisseler": [
        "QNBTR","ASELS","GARAN","KCHOL","THYAO","ISBTR","ISCTR","ISKUR","ENKAI","AKBNK","FROTO","BIMAS","TUPRS","VAKBN","YKBNK","TCELL","TTKOM","SAHOL","EREGL","HALKB","PKENT","KENT","CCOLA","SASA","PGSUS","DSTKF","OYAKC","KLRHO","SISE","ZRGYO","TOASO","ISDMR","TAVHL","AEFES","DOCO","ASTOR","MGROS","TURSG","GUBRF","KOZAL","ARCLK","ENJSA","AHGSLR","YBTAS","SRVGY","BINHO","HATSN","VAKKO","GSRAY","ARMGD","GLCVY","REEDR","ISFIN","SONME","HRKET","GARFA","IZFAS","AGROT","KARSN","AKENR","INGRM","KLGYO","BEGYO","TSPOR","GOKNR","NATEN","TRCAS","VAKFN","TNZTP","TARKM","CEMAS","VKGYO","BOSSA","BOBET","IZMDC","SURGY","INVEO","ATATP","IEYHO","SNPAM","ADEL","BULGS","EBEBK","ENDAE","KBORU","SUWEN","AKMGY","GENTS","ODAS","ASGYO","KMPUR","BASCM","DOKTA","MEGMT","EMKEL","KAREL","BMSTL","YIGIT","GOZDE","MOBTL","AYEN","PAGYO","DOBUR","PARSN","KOPOL","OFSYM","BIGEN","KARTN","ISKPL","NTGAZ","EKOS","PLTUR","GOLTS","USAK","PAPIL","A1CAP","PRKAB","TCKRC","MNDTR","ORGE","ERCB","ATAKP","KOCMT","MAALT","ALGYO","AFYON","ULUUN","ALKA","DMRGD","PENTA","CEMZY","MERIT","INDES","ALKIM","CEMTS","IHAAS","FORTE","BFREN","CATES","DESA","BORSK","ARDYZ","ALKLC","PEKGY","EGEGY","MHRGY","GOODY","TKNSA","HOROZ","BARMA","KZGYO","BIGCH","DCTTR","DYOBY","ANELE","ELITE","CGCAM","ORMA","ALVES","KRVGD","DERHL","TSGYO","SOKE","KAPLM","FMIZP","ALCTL","KONKA","MERCN","DAGHL","METUR","SEGMN","YATAS","ARSAN","AHSGY","BAGFS","GSDHO","EGEPO","SERNT","LRSHO","YAPRK","ONRYT","AZTEK","SAFKR","MACKO","MEDTR","HUNER","EKSUN","CMBTN","HURGZ","TURGG","GEREL","TEKTU","INTEM","BRKVY","KNFRT","SAYAS","KGYO","INTEK","OSMEN","OTTO","FENER","BVSAN","BRLSM","TRILC","SEGYO","IHLAS","ERBOS","ARENA","LKMNH","KUTPO","NETAS","MARBL","ISSEN","MNDRS","SANKO","K","ORCAY","OZRDN","ULAS","ERSU","ATAGY","OYAYO","VKFYO","EKIZ","ATSYH","AVTUR","RODRG","HUBVC","SANEL","CASA","MMCAS","IDGYO","GRNYO","ATLAS","MTRYO","ETYAT","DIRIT","BRMEN","EUKYO","EUYO"
    ]
}
ZAMAN_ARALIKLARI = {
    "1 Saatlik": "1h", "4 Saatlik": "4h", "1 Günlük": "1d",
    "1 Haftalık": "1wk", "1 Aylık": "1mo"
}

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
        st.error(f"{hisse_kodu} için teknik veriler çekilirken hata oluştu: {e}")
        raise e # Tenacity'nin tekrar denemesi için hatayı yeniden fırlat

@st.cache_data(ttl=3600)
@retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
def get_fundamental_data(hisse_kodu):
    """Native temel veri çekme fonksiyonunu retry ve cache ile sarmalar."""
    try:
        return get_fundamental_data_native(hisse_kodu)
    except Exception as e:
        st.error(f"{hisse_kodu} için temel veriler çekilirken hata oluştu: {e}")
        raise e

@st.cache_data(ttl=86400)
def get_sector_peers(hisse_kodu):
    try:
        return get_sector_peers_native(hisse_kodu)
    except Exception as e:
        st.error(f"{hisse_kodu} için sektör verileri çekilirken hata oluştu: {e}")
        return None, None

# --- Ana Arayüz Fonksiyonları ---
@st.cache_data
def convert_df_to_csv(df):
    return df.to_csv().encode('utf-8')

def display_technical_analysis(veri, hisse_kodu_yf, interval_display, analysis_type):
    st.header(f"{hisse_kodu_yf} - Teknik Grafik")
    plotly_fig = plot_analysis_plotly(veri, hisse_kodu_yf, interval_display, analysis_type)
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
    data = get_fundamental_data(hisse_kodu_yf)
    if data and data.get('info'):
        info = data['info']
        
        st.subheader("Şirket Künyesi")
        _, key_info_text = generate_fundamental_summary(info, as_markdown=False)
        st.text(key_info_text)

        st.subheader("Yapay Zeka Destekli Temel Yorumlar")
        fundamental_summary = generate_fundamental_summary(info, as_markdown=True)
        st.markdown(fundamental_summary)

        display_sector_analysis(hisse_kodu_yf, info)

        st.subheader("Finansal Tablolar")
        tablo_gelir, tablo_bilanco, tablo_nakit = st.tabs(["Gelir Tablosu", "Bilanço", "Nakit Akış Tablosu"])
        with tablo_gelir:
            st.dataframe(data.get('financials'), use_container_width=True)
        with tablo_bilanco:
            st.dataframe(data.get('balance_sheet'), use_container_width=True)
        with tablo_nakit:
            st.dataframe(data.get('cashflow'), use_container_width=True)
    else:
        st.warning("Temel veriler alınamadı.")

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

def display_portfolio_summary(portfolio_tickers, interval_code):
    st.header("İzleme Listesi Özeti")
    summary_data = []
    progress_bar = st.progress(0, "İzleme listesi verileri çekiliyor...")
    
    for i, ticker in enumerate(portfolio_tickers):
        hisse_kodu_yf = f"{ticker.strip().upper()}.IS"
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
                st.error(f"Backtest sırasında bir hata oluştu: {e}")
                st.code(traceback.format_exc())

# --- Ana Uygulama Akışı ---
def main():
    st.title("📊 BIST Hisse Senedi Analiz Platformu")

    with st.sidebar:
        st.header("Kontrol Paneli")
        analysis_mode = st.radio("Analiz Modu", ["Tekil Hisse Analizi", "İzleme Listesi"], horizontal=True)

        if analysis_mode == "Tekil Hisse Analizi":
            grup_secim = st.selectbox("Hisse Grubu:", list(HISSE_GRUPPARI.keys()), index=0)
            hisseler = sorted(HISSE_GRUPPARI.get(grup_secim, []))
            default_index = hisseler.index("GARAN") if "GARAN" in hisseler else 0
            hisse_secim = st.selectbox("Hisse Senedi:", hisseler, index=default_index)
        else:
            portfolio_input = st.text_area("İzleme Listesi (Hisseleri virgülle ayırın)", "GARAN, THYAO, EREGL, BIMAS")
            hisseler = sorted(HISSE_GRUPPARI.get("Tüm Hisseler", []))
            hisse_secim = None

        interval_display = st.selectbox("Zaman Aralığı:", list(ZAMAN_ARALIKLARI.keys()), index=2)
        interval_code = ZAMAN_ARALIKLARI[interval_display]
        
        if analysis_mode == "Tekil Hisse Analizi":
            today = datetime.today()
            start_date = st.date_input('Başlangıç Tarihi', today - timedelta(days=365))
            end_date = st.date_input('Bitiş Tarihi', today)
            analysis_type = st.selectbox("Analiz Tipi:", ["Detaylı", "Basit"], index=0)
        
        analyze_button = st.button("Analiz Et", use_container_width=True, type="primary")

    if 'analysis_requested' not in st.session_state:
        st.session_state.analysis_requested = False
    if analyze_button:
        st.session_state.analysis_requested = True

    if st.session_state.analysis_requested:
        if analysis_mode == "Tekil Hisse Analizi":
            if start_date > end_date:
                st.error("Hata: Başlangıç tarihi, bitiş tarihinden sonra olamaz.")
                return

            hisse_kodu_yf = f"{hisse_secim}.IS"
            
            with st.spinner(f'{hisse_kodu_yf} için veriler çekiliyor ve analiz ediliyor...'):
                try:
                    veri_raw = get_stock_data(hisse_kodu_yf, interval_code)
                except ValueError as e:
                    st.error(f"{hisse_kodu_yf} için veri çekilemedi: {e}. Lütfen farklı bir zaman aralığı deneyin veya daha sonra tekrar deneyin.")
                    veri_raw = None
                except Exception as e:
                    st.error(f"{hisse_kodu_yf} için beklenmedik bir hata oluştu: {e}. Lütfen daha sonra tekrar deneyin.")
                    st.error(f"Detay: {e}")
                    veri_raw = None

                if veri_raw is not None:
                    veri_hesaplanmis = calculate_indicators(veri_raw.copy())
                    veri_filtrelenmis = filter_data_by_date(veri_hesaplanmis, start_date=start_date, end_date=end_date)
                    if not veri_filtrelenmis.empty:
                        st.success(f"{hisse_kodu_yf} analizi tamamlandı.")
                        ana_tab, karsilastirma_tab, temel_tab, backtest_tab = st.tabs(["📈 Teknik Analiz", "🆚 Hisse Karşılaştırma", "🏢 Temel Analiz", "🧪 Strateji Testi"])
                        with ana_tab:
                            display_technical_analysis(veri_filtrelenmis, hisse_kodu_yf, interval_display, analysis_type)
                        with karsilastirma_tab:
                            display_comparison(hisseler, hisse_secim, interval_code, start_date, end_date)
                        with temel_tab:
                            display_fundamental_analysis(hisse_kodu_yf)
                        with backtest_tab:
                            display_backtesting(veri_filtrelenmis, hisse_kodu_yf)
                    else:
                        st.warning("Seçilen tarih aralığı için veri bulunamadı.")
        
        elif analysis_mode == "İzleme Listesi":
            portfolio_tickers = [ticker.strip() for ticker in portfolio_input.split(",") if ticker.strip()]
            if portfolio_tickers:
                display_portfolio_summary(portfolio_tickers, interval_code)
            else:
                st.warning("Lütfen izleme listesine en az bir hisse senedi girin.")
    else:
        st.info("Lütfen sol taraftaki menüden bir analiz modu seçip 'Analiz Et' butonuna tıklayın.")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        st.error("Uygulama başlatılırken beklenmedik bir hata oluştu.")
        st.error(f"Hata Detayı: {e}")
        st.code(traceback.format_exc())