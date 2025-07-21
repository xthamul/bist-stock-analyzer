import sys
import traceback
import yfinance as yf
import pandas as pd
import numpy as np
import pandas_ta as ta
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from scipy.signal import find_peaks
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

# pandas_ta kaynaklı numpy hatasını düzeltmek için yama
if not hasattr(np, 'NaN'):
    setattr(np, 'NaN', np.nan)

class StockAnalyzerApp:
    def __init__(self, master):
        self.master = master
        master.title("BIST Hisse Senedi Analiz Uygulaması")
        master.geometry("850x650") # Pencere boyutunu ayarla

        self.hisse_gruplari = {
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

        self.zaman_araliklari = {
            "1 Saatlik": "1h", "4 Saatlik": "4h", "1 Günlük": "1d",
            "1 Haftalık": "1wk", "1 Aylık": "1mo"
        }

        self.display_ranges = {
            "Tüm Veri": None, "Son 1 Ay": pd.DateOffset(months=1),
            "Son 3 Ay": pd.DateOffset(months=3), "Son 6 Ay": pd.DateOffset(months=6),
            "Son 1 Yıl": pd.DateOffset(years=1), "Son 2 Yıl": pd.DateOffset(years=2)
        }
        
        self.current_chart_figure = None

        # --- Arayüz Elementleri ---
        self.notebook = ttk.Notebook(master)
        self.notebook.pack(pady=10, padx=10, expand=True, fill='both')

        self.tech_analysis_frame = ttk.Frame(self.notebook, padding="10")
        self.fundamental_analysis_frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(self.tech_analysis_frame, text='Teknik Analiz')
        self.notebook.add(self.fundamental_analysis_frame, text='Temel Analiz')

        self.setup_technical_analysis_tab()
        self.setup_fundamental_analysis_tab()

    def setup_technical_analysis_tab(self):
        controls_frame = ttk.LabelFrame(self.tech_analysis_frame, text="Kontroller", padding="10")
        controls_frame.pack(fill='x', expand=False)

        ttk.Label(controls_frame, text="Hisse Grubu:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.grup_secim = ttk.Combobox(controls_frame, values=list(self.hisse_gruplari.keys()), state="readonly")
        self.grup_secim.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        self.grup_secim.set("BIST 100 Hisseleri")
        self.grup_secim.bind("<<ComboboxSelected>>", self.update_hisse_listesi)

        ttk.Label(controls_frame, text="Hisse Senedi:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.hisse_secim = ttk.Combobox(controls_frame, state="readonly")
        self.hisse_secim.grid(row=1, column=1, padx=5, pady=5, sticky="ew")
        self.update_hisse_listesi()

        ttk.Label(controls_frame, text="Zaman Aralığı:").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        self.interval_secim = ttk.Combobox(controls_frame, values=list(self.zaman_araliklari.keys()), state="readonly")
        self.interval_secim.grid(row=2, column=1, padx=5, pady=5, sticky="ew")
        self.interval_secim.set("1 Günlük")

        ttk.Label(controls_frame, text="Görüntüleme Aralığı:").grid(row=3, column=0, padx=5, pady=5, sticky="w")
        self.display_range_secim = ttk.Combobox(controls_frame, values=list(self.display_ranges.keys()), state="readonly")
        self.display_range_secim.grid(row=3, column=1, padx=5, pady=5, sticky="ew")
        self.display_range_secim.set("Son 1 Yıl")

        self.analyze_button = ttk.Button(controls_frame, text="Analiz Et", command=self.run_analysis)
        self.analyze_button.grid(row=4, column=0, columnspan=2, padx=5, pady=10, sticky="ew")

        self.save_chart_button = ttk.Button(controls_frame, text="Grafiği Kaydet", command=self.save_chart)
        self.save_chart_button.grid(row=5, column=0, columnspan=2, padx=5, pady=5, sticky="ew")
        self.save_chart_button.state(['disabled'])

        log_frame = ttk.LabelFrame(self.tech_analysis_frame, text="Analiz Sonuçları", padding="10")
        log_frame.pack(fill='both', expand=True, pady=(10,0))
        
        self.message_text = tk.Text(log_frame, height=15, wrap="word", font=("Courier", 9))
        self.message_text.pack(side="left", fill="both", expand=True)
        
        scrollbar = ttk.Scrollbar(log_frame, command=self.message_text.yview)
        scrollbar.pack(side="right", fill="y")
        self.message_text.config(yscrollcommand=scrollbar.set)

    def setup_fundamental_analysis_tab(self):
        self.fundamental_text = tk.Text(self.fundamental_analysis_frame, wrap="word", font=("Courier", 10), state="disabled")
        self.fundamental_text.pack(padx=5, pady=5, fill="both", expand=True)

    def update_hisse_listesi(self, event=None):
        secilen_grup = self.grup_secim.get()
        hisseler = sorted(self.hisse_gruplari.get(secilen_grup, []))
        self.hisse_secim['values'] = hisseler
        if hisseler:
            self.hisse_secim.set(hisseler[0])
        else:
            self.hisse_secim.set("")

    def _flatten_columns(self, df):
        """
        Flattens MultiIndex columns to a single level of strings.
        """
        new_columns = []
        for col in df.columns:
            if isinstance(col, tuple):
                # Join tuple elements with '_' and remove any trailing underscores
                new_columns.append('_'.join(filter(None, col)).strip('_'))
            else:
                new_columns.append(str(col))
        df.columns = new_columns
        return df

    def log_message(self, message):
        self.message_text.config(state="normal")
        self.message_text.insert(tk.END, message + "\n")
        self.message_text.see(tk.END)
        self.message_text.config(state="disabled")
        self.master.update_idletasks()

    def run_analysis(self, event=None):
        hisse_kodu = self.hisse_secim.get()
        interval_display = self.interval_secim.get()
        display_range_key = self.display_range_secim.get()

        if not all([hisse_kodu, interval_display, display_range_key]):
            messagebox.showwarning("Uyarı", "Lütfen tüm alanları doldurun.")
            return

        hisse_kodu_yf = f"{hisse_kodu}.IS"
        interval_code = self.zaman_araliklari.get(interval_display)

        self.log_message(f"Analiz başlatılıyor: {hisse_kodu_yf} ({interval_display}, {display_range_key})")
        self.save_chart_button.state(['disabled'])
        self.current_chart_figure = None
        self.message_text.config(state="normal")
        self.message_text.delete('1.0', tk.END)
        self.message_text.config(state="disabled")

        try:
            self._analiz_et_ve_gorsellestir(hisse_kodu_yf, interval_code, display_range_key, interval_display)
            self.fetch_and_display_fundamental_data(hisse_kodu_yf)
            if self.current_chart_figure:
                self.save_chart_button.state(['!disabled'])
        except Exception as e:
            self.log_message(f"Bir hata oluştu: {e}")
            messagebox.showerror("Hata", f"Analiz sırasında bir hata oluştu: {e}")
            traceback.print_exc()

    def _analiz_et_ve_gorsellestir(self, hisse_kodu, interval, display_range_key, interval_display):
        self.log_message(f"Veriler çekiliyor...")
        
        # Veri çekme periyodunu dinamikleştir
        if interval in ["1h", "4h"]:
            veri = yf.download(hisse_kodu, period="2y", interval=interval, progress=False, auto_adjust=False)
        else:
            veri = yf.download(hisse_kodu, period="max", interval=interval, progress=False, auto_adjust=False)

        if veri.empty:
            self.log_message(f"Hata: {hisse_kodu} için veri bulunamadı.")
            return

        # yfinance'in tek bir hisse için bile MultiIndex döndürme durumunu ele al
        if isinstance(veri.columns, pd.MultiIndex):
            veri.columns = veri.columns.droplevel(1)

        # Sütun adlarını küçük harfe çevirerek tutarlılık sağla
        veri.columns = [col.lower() for col in veri.columns]

        veri = self.calculate_indicators(veri)
        veri = self.filter_data_by_display_range(veri, display_range_key)

        if veri.empty:
            self.log_message(f"Hata: Seçilen görüntüleme aralığı için yeterli veri yok.")
            return

        self.plot_analysis(veri, hisse_kodu, interval, display_range_key, interval_display)
        self.log_analysis_summary(veri)

    def calculate_indicators(self, veri):
        self.log_message("Teknik göstergeler hesaplanıyor...")
        veri.ta.ema(length=8, append=True)
        veri.ta.ema(length=13, append=True)
        veri.ta.ema(length=21, append=True)
        veri.ta.ema(length=50, append=True)
        veri.ta.ema(length=200, append=True)
        veri.ta.bbands(length=20, append=True)
        veri.ta.stochrsi(append=True)
        veri.ta.macd(append=True)
        veri.ta.rsi(append=True)
        veri.ta.adx(append=True)
        veri.ta.atr(append=True)
        veri.ta.obv(append=True) # OBV ekledik

        

        # Hareketli Ortalama Kesişimleri
        veri['golden_cross'] = np.nan
        veri['death_cross'] = np.nan
        if 'ema_50' in veri.columns and 'ema_200' in veri.columns:
            for i in range(1, len(veri)):
                if veri['ema_50'].iloc[i-1] < veri['ema_200'].iloc[i-1] and veri['ema_50'].iloc[i] > veri['ema_200'].iloc[i]:
                    veri['golden_cross'].iloc[i] = veri['low'].iloc[i] * 0.99 # Golden Cross
                elif veri['ema_50'].iloc[i-1] > veri['ema_200'].iloc[i-1] and veri['ema_50'].iloc[i] < veri['ema_200'].iloc[i]:
                    veri['death_cross'].iloc[i] = veri['high'].iloc[i] * 1.01 # Death Cross

        veri.ta.cdl_pattern(name="all", append=True)
        veri = find_trendline_breakouts(veri, lookback=30)

        # Ensure columns are flattened and are simple strings after all pandas_ta operations
        veri = self._flatten_columns(veri)

        print("Sütunlar (lower() öncesi):", veri.columns)
        # Sütun adlarını küçük harfe çevirerek tutarlılık sağla
        veri.columns = [col.lower() for col in veri.columns]

        return veri

    def filter_data_by_display_range(self, veri, display_range_key):
        if display_range_key != "Tüm Veri":
            time_delta = self.display_ranges[display_range_key]
            if time_delta:
                start_date = veri.index.max() - time_delta
                return veri[veri.index >= start_date].copy()
        return veri

    def plot_analysis(self, veri, hisse_kodu, interval, display_range_key, interval_display):
        self.log_message("Grafik oluşturuluyor...")
        
        # Plotly ile alt grafikler oluştur
        fig = make_subplots(rows=9, cols=1, shared_xaxes=True,
                            vertical_spacing=0.02,
                            row_heights=[0.4, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1])

        # Mum Grafiği
        fig.add_trace(go.Candlestick(x=veri.index,
                                     open=veri['open'],
                                     high=veri['high'],
                                     low=veri['low'],
                                     close=veri['close'],
                                     name='Fiyat'),
                      row=1, col=1)

        # EMA'lar
        fig.add_trace(go.Scatter(x=veri.index, y=veri['ema_8'], mode='lines', name='EMA 8', line=dict(color='#007bff', width=1)), row=1, col=1)
        fig.add_trace(go.Scatter(x=veri.index, y=veri['ema_13'], mode='lines', name='EMA 13', line=dict(color='#6f42c1', width=1)), row=1, col=1)
        fig.add_trace(go.Scatter(x=veri.index, y=veri['ema_21'], mode='lines', name='EMA 21', line=dict(color='#fd7e14', width=1)), row=1, col=1)

        # Bollinger Bantları
        fig.add_trace(go.Scatter(x=veri.index, y=veri['bbu_20_2.0'], mode='lines', name='BB Üst', line=dict(color='#28a745', width=1, dash='dash')), row=1, col=1)
        fig.add_trace(go.Scatter(x=veri.index, y=veri['bbl_20_2.0'], mode='lines', name='BB Alt', line=dict(color='#dc3545', width=1, dash='dash')), row=1, col=1)

        # Kırılım Sinyalleri
        breakout_up = veri[veri['breakout'] == 1]
        breakout_down = veri[veri['breakout'] == -1]
        fig.add_trace(go.Scatter(x=breakout_up.index, y=breakout_up['low'] * 0.98, mode='markers', name='Yükseliş Kırılımı', marker=dict(symbol='triangle-up', size=10, color='green')), row=1, col=1)
        fig.add_trace(go.Scatter(x=breakout_down.index, y=breakout_down['high'] * 1.02, mode='markers', name='Düşüş Kırılımı', marker=dict(symbol='triangle-down', size=10, color='red')), row=1, col=1)

        # Hareketli Ortalama Kesişim Sinyalleri
        golden_cross_points = veri[veri['golden_cross'].notna()]
        death_cross_points = veri[veri['death_cross'].notna()]
        fig.add_trace(go.Scatter(x=golden_cross_points.index, y=golden_cross_points['golden_cross'], mode='markers', name='Golden Cross', marker=dict(symbol='star', size=12, color='gold')), row=1, col=1)
        fig.add_trace(go.Scatter(x=death_cross_points.index, y=death_cross_points['death_cross'], mode='markers', name='Death Cross', marker=dict(symbol='star', size=12, color='purple')), row=1, col=1)

        # Hacim
        fig.add_trace(go.Bar(x=veri.index, y=veri['volume'], name='Hacim', marker_color='#6c757d'), row=2, col=1)

        # RSI
        fig.add_trace(go.Scatter(x=veri.index, y=veri['rsi_14'], mode='lines', name='RSI', line=dict(color='#007bff', width=1)), row=3, col=1)
        fig.add_trace(go.Scatter(x=veri.index, y=[70]*len(veri), mode='lines', name='RSI 70', line=dict(color='#dc3545', width=0.7, dash='dot')), row=3, col=1)
        fig.add_trace(go.Scatter(x=veri.index, y=[30]*len(veri), mode='lines', name='RSI 30', line=dict(color='#28a745', width=0.7, dash='dot')), row=3, col=1)

        # Stokastik RSI
        fig.add_trace(go.Scatter(x=veri.index, y=veri['stochrsik_14_14_3_3'], mode='lines', name='StochRSI %K', line=dict(color='#007bff', width=1)), row=4, col=1)
        fig.add_trace(go.Scatter(x=veri.index, y=veri['stochrsid_14_14_3_3'], mode='lines', name='StochRSI %D', line=dict(color='#fd7e14', width=1)), row=4, col=1)

        # MACD
        fig.add_trace(go.Scatter(x=veri.index, y=veri['macd_12_26_9'], mode='lines', name='MACD', line=dict(color='#007bff', width=1)), row=5, col=1)
        fig.add_trace(go.Scatter(x=veri.index, y=veri['macds_12_26_9'], mode='lines', name='MACD Sinyal', line=dict(color='#fd7e14', width=1)), row=5, col=1)
        fig.add_trace(go.Scatter(x=veri.index, y=veri['macdh_12_26_9'], name='MACD Histogram', marker_color='#6c757d'), row=5, col=1)

        # ADX
        fig.add_trace(go.Scatter(x=veri.index, y=veri['adx_14'], mode='lines', name='ADX', line=dict(color='#ffc107', width=1)), row=6, col=1)
        fig.add_trace(go.Scatter(x=veri.index, y=veri['dmp_14'], mode='lines', name='+DI', line=dict(color='#28a745', width=1)), row=6, col=1)
        fig.add_trace(go.Scatter(x=veri.index, y=veri['dmn_14'], mode='lines', name='-DI', line=dict(color='#dc3545', width=1)), row=6, col=1)

        # ATR
        fig.add_trace(go.Scatter(x=veri.index, y=veri['atrr_14'], mode='lines', name='ATR', line=dict(color='#17a2b8', width=1)), row=7, col=1)

        # OBV
        fig.add_trace(go.Scatter(x=veri.index, y=veri['obv'], mode='lines', name='OBV', line=dict(color='#ffc107', width=1)), row=8, col=1)

        # Bollinger Band Genişliği
        fig.add_trace(go.Scatter(x=veri.index, y=veri['bbb_20_2.0'], mode='lines', name='BBW', line=dict(color='#6c757d', width=1)), row=9, col=1)

        # Düzen ve Başlık
        fig.update_layout(title_text=f'{hisse_kodu} Teknik Analiz ({interval_display}, {display_range_key})',
                          title_x=0.5, # Başlığı ortala
                          height=1400, # Grafiğin yüksekliğini artır
                          xaxis_rangeslider_visible=False, # Range slider'ı kapat
                          hovermode='x unified', # Hover modunu ayarla
                          template='plotly_dark') # Daha modern bir tema kullan

        # X ekseni ayarları (tüm alt grafikler için)
        fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='#333', rangeslider_visible=False)
        # Y ekseni ayarları
        fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='#333')

        # Her bir alt grafik için y ekseni başlıkları
        fig.update_yaxes(title_text='Fiyat', row=1, col=1)
        fig.update_yaxes(title_text='Hacim', row=2, col=1)
        fig.update_yaxes(title_text='RSI', row=3, col=1)
        fig.update_yaxes(title_text='StochRSI', row=4, col=1)
        fig.update_yaxes(title_text='MACD', row=5, col=1)
        fig.update_yaxes(title_text='ADX', row=6, col=1)
        fig.update_yaxes(title_text='ATR', row=7, col=1)
        fig.update_yaxes(title_text='OBV', row=8, col=1)
        fig.update_yaxes(title_text='BBW', row=9, col=1)

        self.current_chart_figure = fig
        fig.show()

    def log_analysis_summary(self, veri):
        son_veri = veri.iloc[-1]
        summary = [
            "--- Teknik Analiz Özeti ---",
            f"Tarih: {son_veri.name.strftime('%Y-%m-%d %H:%M')}",
            f"Kapanış Fiyatı: {son_veri['close']:.2f}",
            f"EMA (8, 13, 21): {son_veri['ema_8']:.2f}, {son_veri['ema_13']:.2f}, {son_veri['ema_21']:.2f}",
            f"Bollinger (Üst/Alt): {son_veri['bbu_20_2.0']:.2f} / {son_veri['bbl_20_2.0']:.2f}",
            f"RSI (14): {son_veri['rsi_14']:.2f}",
            f"Stokastik RSI (k, d): {son_veri['stochrsik_14_14_3_3']:.2f}, {son_veri['stochrsid_14_14_3_3']:.2f}",
            f"MACD (Değer, Sinyal): {son_veri['macd_12_26_9']:.2f}, {son_veri['macds_12_26_9']:.2f}",
            f"ADX (14): {son_veri['adx_14']:.2f}",
            f"ATR (14): {son_veri['atrr_14']:.2f}",
            f"OBV: {son_veri['obv']:.2f}",
            f"Bollinger Band Genişliği (BBW): {son_veri['bbb_20_2.0']:.2f}"
        ]

        # Yapay Zeka Destekli Teknik Yorumlar (Simülasyon)
        summary.append("\n--- Yapay Zeka Destekli Teknik Yorumlar ---")
        
        # Genel Teknik Görünüm
        if son_veri['ema_50'] > son_veri['ema_200'] and son_veri['close'] > son_veri['ema_50']:
            summary.append("Genel Teknik Görünüm: Güçlü Yükseliş Eğilimi (Fiyatlar EMA50 ve EMA200 üzerinde, EMA50 > EMA200).")
        elif son_veri['ema_50'] < son_veri['ema_200'] and son_veri['close'] < son_veri['ema_50']:
            summary.append("Genel Teknik Görünüm: Güçlü Düşüş Eğilimi (Fiyatlar EMA50 ve EMA200 altında, EMA50 < EMA200).")
        elif son_veri['ema_50'] > son_veri['ema_200'] and son_veri['close'] < son_veri['ema_50']:
            summary.append("Genel Teknik Görünüm: Yükseliş eğilimi zayıflıyor veya düzeltme yaşanıyor.")
        elif son_veri['ema_50'] < son_veri['ema_200'] and son_veri['close'] > son_veri['ema_50']:
            summary.append("Genel Teknik Görünüm: Düşüş eğilimi zayıflıyor veya toparlanma yaşanıyor.")
        else:
            summary.append("Genel Teknik Görünüm: Yatay veya belirsiz eğilim.")

        if son_veri['rsi_14'] > 70:
            summary.append("RSI aşırı alım bölgesinde, düzeltme veya düşüş riski olabilir.")
        elif son_veri['rsi_14'] < 30:
            summary.append("RSI aşırı satım bölgesinde, toparlanma veya yükseliş potansiyeli olabilir.")

        if son_veri['macd_12_26_9'] > son_veri['macds_12_26_9'] and son_veri['macdh_12_26_9'] > 0:
            summary.append("MACD pozitif bölgede ve sinyal çizgisinin üzerinde, yükseliş eğilimi devam ediyor.")
        elif son_veri['macd_12_26_9'] < son_veri['macds_12_26_9'] and son_veri['macdh_12_26_9'] < 0:
            summary.append("MACD negatif bölgede ve sinyal çizgisinin altında, düşüş eğilimi devam ediyor.")

        if son_veri['adx_14'] > 25:
            if son_veri['dmp_14'] > son_veri['dmn_14']:
                summary.append("ADX güçlü bir trendin varlığını gösteriyor ve pozitif yönlü hareket baskın.")
            else:
                summary.append("ADX güçlü bir trendin varlığını gösteriyor ancak negatif yönlü hareket baskın.")
        else:
            summary.append("ADX zayıf veya yatay bir trendin varlığını gösteriyor.")

        # OBV Yorumu
        if son_veri['obv'] > veri['obv'].iloc[-2]:
            summary.append("OBV yükseliyor, bu da alıcı baskısının arttığını ve mevcut trendi desteklediğini gösteriyor.")
        elif son_veri['obv'] < veri['obv'].iloc[-2]:
            summary.append("OBV düşüyor, bu da satıcı baskısının arttığını ve mevcut trendi zayıflattığını gösteriyor.")
        else:
            summary.append("OBV yatay seyrediyor, bu da belirsizliği gösteriyor.")

        # BBW Yorumu
        if son_veri['bbb_20_2.0'] > veri['bbb_20_2.0'].mean() * 1.5: # Ortalama genişliğin 1.5 katından fazlaysa
            summary.append("Bollinger Band Genişliği yüksek, bu da yüksek volatiliteye işaret ediyor. Büyük fiyat hareketleri beklenebilir.")
        elif son_veri['bbb_20_2.0'] < veri['bbb_20_2.0'].mean() * 0.5: # Ortalama genişliğin yarısından azsa
            summary.append("Bollinger Band Genişliği düşük, bu da düşük volatiliteye işaret ediyor. Sıkışma sonrası büyük fiyat hareketleri beklenebilir.")
        else:
            summary.append("Bollinger Band Genişliği normal seviyelerde, volatilite dengeli.")

        summary.append("-------------------------------------")
        
        candle_cols = [col for col in veri.columns if col.startswith('cdl_')]
        last_pattern = veri[candle_cols].iloc[-1]
        detected = last_pattern[last_pattern != 0]
        if not detected.empty:
            p_name = detected.index[0].replace("cdl_", "")
            p_signal = " (Yükseliş)" if detected.iloc[0] > 0 else " (Düşüş)"
            summary.append(f"Son Mum Formasyonu: {p_name}{p_signal}")
        
        # Hareketli Ortalama Kesişim Yorumları
        if 'golden_cross' in son_veri and not pd.isna(son_veri['golden_cross']):
            summary.append("Golden Cross sinyali oluştu (Kısa vadeli ortalama uzun vadeli ortalamayı yukarı kesti), bu yükseliş trendinin başlangıcı olabilir.")
        if 'death_cross' in son_veri and not pd.isna(son_veri['death_cross']):
            summary.append("Death Cross sinyali oluştu (Kısa vadeli ortalama uzun vadeli ortalamayı aşağı kesti), bu düşüş trendinin başlangıcı olabilir.")

        breakout_signal = 'Yok'
        if son_veri['breakout'] == 1: breakout_signal = 'Yükseliş'
        elif son_veri['breakout'] == -1: breakout_signal = 'Düşüş'
        summary.append(f"Son Kırılım Sinyali: {breakout_signal}")
        summary.append("-------------------------------------")
        
        self.log_message("\n".join(summary))

    def fetch_and_display_fundamental_data(self, hisse_kodu):
        self.log_message(f"Temel veriler çekiliyor...")
        try:
            stock = yf.Ticker(hisse_kodu)
            info = stock.info
            
            self.fundamental_text.config(state="normal")
            self.fundamental_text.delete('1.0', tk.END)

            key_info_map = {
                'longName': 'Şirket Adı', 'symbol': 'Sembol', 'sector': 'Sektör',
                'marketCap': 'Piyasa Değeri', 'trailingPE': 'F/K Oranı', 'forwardPE': 'Tahmini F/K',
                'trailingEps': 'EPS', 'priceToBook': 'PD/DD', 'dividendYield': 'Temettü Verimi',
                'payoutRatio': 'Temettü Dağıtma Oranı', 'beta': 'Beta', '52WeekChange': '52H Değişim',
                'fiftyTwoWeekHigh': '52H En Yüksek', 'fiftyTwoWeekLow': '52H En Düşük',
                'regularMarketVolume': 'Hacim', 'averageVolume': 'Ortalama Hacim',
                'enterpriseValue': 'Şirket Değeri', 'revenueGrowth': 'Gelir Büyümesi',
                'earningsGrowth': 'Kazanç Büyümesi', 'debtToEquity': 'Borç/Özkaynak Oranı',
                'currentRatio': 'Cari Oran', 'returnOnEquity': 'Özkaynak Karlılığı',
                'grossMargins': 'Brüt Kar Marjı', 'operatingMargins': 'Faaliyet Kar Marjı',
                'profitMargins': 'Net Kar Marjı',
                'recommendationKey': 'Analist Tavsiyesi', 'targetMeanPrice': 'Ort. Hedef Fiyat'
            }

            display_text = f"--- {info.get('longName', hisse_kodu)} Temel Verileri ---\n\n"
            for key, label in key_info_map.items():
                value = info.get(key, "N/A")
                if isinstance(value, (int, float)):
                    if 'Değişim' in label or 'Verim' in label:
                        display_text += f"{label:<25}: {value:.2%}\n"
                    else:
                        display_text += f"{label:<25}: {value:,.2f}\n"
                else:
                    display_text += f"{label:<25}: {value}\n"
            
            self.fundamental_text.insert(tk.END, display_text)
            
            # Yapay Zeka Destekli Temel Yorumları Ekle
            fundamental_summary = self._generate_fundamental_summary(info)
            self.fundamental_text.insert(tk.END, "\n--- Yapay Zeka Destekli Temel Yorumlar ---\n")
            self.fundamental_text.insert(tk.END, fundamental_summary)

            self.log_message("Temel veriler başarıyla çekildi.")
        except Exception as e:
            self.log_message(f"Temel veriler çekilemedi: {e}")
        finally:
            self.fundamental_text.config(state="disabled")

    def save_chart(self):
        if not self.current_chart_figure:
            messagebox.showwarning("Uyarı", "Kaydedilecek bir grafik yok.")
            return
        try:
            file_path = filedialog.asksaveasfilename(
                defaultextension=".html",
                filetypes=[("HTML files", "*.html"), ("PNG files", "*.png"), ("JPEG files", "*.jpg")],
                title="Grafiği Kaydet"
            )
            if file_path:
                if file_path.endswith(".html"):
                    self.current_chart_figure.write_html(file_path)
                elif file_path.endswith(".png") or file_path.endswith(".jpg"):
                    # Plotly'nin statik resim kaydetme özelliği için kaleido'ya ihtiyaç duyulabilir.
                    # pip install kaleido
                    self.current_chart_figure.write_image(file_path)
                self.log_message(f"Grafik kaydedildi: {file_path}")
                messagebox.showinfo("Başarılı", f"Grafik kaydedildi: {file_path}")
        except Exception as e:
            self.log_message(f"Grafik kaydedilemedi: {e}")
            messagebox.showerror("Hata", f"Grafik kaydedilemedi: {e}")

    def _generate_fundamental_summary(self, info):
        summary_parts = []

        # Finansal Sağlık Yorumu
        debt_to_equity = info.get('debtToEquity')
        current_ratio = info.get('currentRatio')
        if debt_to_equity is not None and current_ratio is not None:
            if debt_to_equity < 0.5 and current_ratio > 1.5:
                summary_parts.append("Finansal Sağlık: Şirketin borçluluk oranı düşük ve cari oranı yüksek, bu da güçlü bir finansal yapıya işaret ediyor.")
            elif debt_to_equity < 1.0 and current_ratio > 1.0:
                summary_parts.append("Finansal Sağlık: Şirketin finansal durumu dengeli görünüyor, borçları yönetilebilir seviyede.")
            else:
                summary_parts.append("Finansal Sağlık: Şirketin borçluluk oranı yüksek veya cari oranı düşük, bu durum finansal riskler taşıyabilir.")
        else:
            summary_parts.append("Finansal Sağlık: Yeterli veri olmadığı için finansal sağlık yorumu yapılamıyor.")

        # Büyüme Potansiyeli Yorumu
        revenue_growth = info.get('revenueGrowth')
        earnings_growth = info.get('earningsGrowth')
        if revenue_growth is not None and earnings_growth is not None:
            if revenue_growth > 0.10 and earnings_growth > 0.15: # %10 gelir, %15 kazanç büyümesi
                summary_parts.append("Büyüme Potansiyeli: Şirket hem gelir hem de kazanç açısından güçlü bir büyüme sergiliyor, bu da gelecek için olumlu bir işaret.")
            elif revenue_growth > 0.05 or earnings_growth > 0.05:
                summary_parts.append("Büyüme Potansiyeli: Şirket makul bir büyüme gösteriyor, ancak daha güçlü bir ivme beklenebilir.")
            else:
                summary_parts.append("Büyüme Potansiyeli: Şirketin büyüme oranları düşük, bu da gelecekteki performans için bir endişe kaynağı olabilir.")
        else:
            summary_parts.append("Büyüme Potansiyeli: Yeterli veri olmadığı için büyüme potansiyeli yorumu yapılamıyor.")

        # Değerleme Yorumu
        trailing_pe = info.get('trailingPE')
        forward_pe = info.get('forwardPE')
        price_to_book = info.get('priceToBook')
        if trailing_pe is not None and forward_pe is not None and price_to_book is not None:
            if trailing_pe < 15 and forward_pe < 12 and price_to_book < 2:
                summary_parts.append("Değerleme: Şirket mevcut F/K, tahmini F/K ve PD/DD oranlarına göre cazip bir değerlemeye sahip olabilir.")
            elif trailing_pe < 25 and forward_pe < 20 and price_to_book < 3:
                summary_parts.append("Değerleme: Şirket makul bir değerlemeye sahip görünüyor, ancak sektör ortalamaları ile karşılaştırmak faydalı olacaktır.")
            else:
                summary_parts.append("Değerleme: Şirketin değerleme oranları yüksek, bu da aşırı değerli olabileceğine işaret edebilir.")
        else:
            summary_parts.append("Değerleme: Yeterli veri olmadığı için değerleme yorumu yapılamıyor.")

        # Karlılık Yorumu
        return_on_equity = info.get('returnOnEquity')
        gross_margins = info.get('grossMargins')
        profit_margins = info.get('profitMargins')
        if return_on_equity is not None and gross_margins is not None and profit_margins is not None:
            if return_on_equity > 0.15 and gross_margins > 0.30 and profit_margins > 0.10: # %15 ROE, %30 Brüt, %10 Net Kar Marjı
                summary_parts.append("Karlılık: Şirket yüksek özkaynak karlılığı ve güçlü kar marjları ile oldukça karlı bir yapıya sahip.")
            elif return_on_equity > 0.08 or gross_margins > 0.20 or profit_margins > 0.05:
                summary_parts.append("Karlılık: Şirket makul bir karlılık sergiliyor, ancak iyileştirme potansiyeli olabilir.")
            else:
                summary_parts.append("Karlılık: Şirketin karlılık oranları düşük, bu da operasyonel verimlilik sorunlarına işaret edebilir.")
        else:
            summary_parts.append("Karlılık: Yeterli veri olmadığı için karlılık yorumu yapılamıyor.")

        # Analist Tavsiyesi
        recommendation_key = info.get('recommendationKey')
        target_mean_price = info.get('targetMeanPrice')
        current_price = info.get('currentPrice')

        if recommendation_key and target_mean_price and current_price:
            summary_parts.append(f"Analist Tavsiyesi: Analistler genellikle hisse senedi için '{recommendation_key}' tavsiyesinde bulunuyor. Ortalama hedef fiyat {target_mean_price:.2f} iken, mevcut fiyat {current_price:.2f}. Bu, potansiyel bir {((target_mean_price - current_price) / current_price):.2%} getiri anlamına gelebilir.")
        elif recommendation_key:
            summary_parts.append(f"Analist Tavsiyesi: Analistler genellikle hisse senedi için '{recommendation_key}' tavsiyesinde bulunuyor.")
        else:
            summary_parts.append("Analist Tavsiyesi: Analist tavsiyesi veya hedef fiyat verisi bulunamadı.")

        return "\n".join(summary_parts)

def find_trendline_breakouts(data: pd.DataFrame, lookback: int, peak_prominence: float = 0.02):
    data['breakout'] = 0
    for i in range(lookback, len(data)):
        window = data.iloc[i - lookback:i]
        price_range = window['close'].max() - window['close'].min()
        if price_range == 0: continue

        prominence_value = price_range * peak_prominence
        peaks, _ = find_peaks(window['close'], prominence=prominence_value)
        troughs, _ = find_peaks(-window['close'], prominence=prominence_value)

        if len(peaks) >= 2:
            x_peaks = peaks[-2:]
            y_peaks = window['close'].iloc[x_peaks].values
            slope = (y_peaks[1] - y_peaks[0]) / (x_peaks[1] - x_peaks[0]) if (x_peaks[1] - x_peaks[0]) != 0 else 0
            intercept = y_peaks[0] - slope * x_peaks[0]
            resistance_price = slope * (lookback - 1) + intercept
            if data['close'].iloc[i] > resistance_price:
                data.loc[data.index[i], 'breakout'] = 1

        if len(troughs) >= 2:
            x_troughs = troughs[-2:]
            y_troughs = window['close'].iloc[x_troughs].values
            slope = (y_troughs[1] - y_troughs[0]) / (x_troughs[1] - x_troughs[0]) if (x_troughs[1] - x_troughs[0]) != 0 else 0
            intercept = y_troughs[0] - slope * x_troughs[0]
            support_price = slope * (lookback - 1) + intercept
            if data['close'].iloc[i] < support_price:
                data.loc[data.index[i], 'breakout'] = -1
    return data

if __name__ == "__main__":
    root = tk.Tk()
    app = StockAnalyzerApp(root)
    root.mainloop()