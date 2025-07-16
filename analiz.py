import sys
import traceback
import yfinance as yf
import pandas as pd
import numpy as np
import pandas_ta as ta
import matplotlib.pyplot as plt
import mplfinance as mpf
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk

from scipy.signal import find_peaks
from sklearn.linear_model import LinearRegression
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
        master.protocol("WM_DELETE_WINDOW", self.on_closing)

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
        
        self.canvas = None
        self.toolbar = None
        self.current_chart_figure = None
        self.chart_window = None

        # --- Arayüz Elementleri ---
        self.notebook = ttk.Notebook(master)
        self.notebook.pack(pady=10, padx=10, expand=True, fill='both')

        self.tech_analysis_frame = ttk.Frame(self.notebook, padding="10")
        self.fundamental_analysis_frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(self.tech_analysis_frame, text='Teknik Analiz')
        self.notebook.add(self.fundamental_analysis_frame, text='Temel Analiz')

        self.setup_technical_analysis_tab()
        self.setup_fundamental_analysis_tab()

    def on_closing(self):
        plt.close('all')
        if self.chart_window:
            try:
                self.chart_window.destroy()
            except tk.TclError:
                pass
        self.master.destroy()
        sys.exit(0)

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

        ttk.Label(controls_frame, text="Analiz Tipi:").grid(row=4, column=0, padx=5, pady=5, sticky="w")
        self.analiz_tipi_secim = ttk.Combobox(controls_frame, values=["Detaylı", "Basit"], state="readonly")
        self.analiz_tipi_secim.grid(row=4, column=1, padx=5, pady=5, sticky="ew")
        self.analiz_tipi_secim.set("Detaylı")

        button_frame = ttk.Frame(controls_frame)
        button_frame.grid(row=5, column=0, columnspan=2, pady=10)
        
        self.analyze_button = ttk.Button(button_frame, text="Analiz Et", command=self.run_analysis)
        self.analyze_button.pack(side="left", padx=5)

        self.save_button = ttk.Button(button_frame, text="Grafiği Kaydet", command=self.save_chart)
        self.save_button.pack(side="left", padx=5)

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
        analysis_type = self.analiz_tipi_secim.get()

        if not all([hisse_kodu, interval_display, display_range_key, analysis_type]):
            messagebox.showwarning("Uyarı", "Lütfen tüm alanları doldurun.")
            return

        hisse_kodu_yf = f"{hisse_kodu}.IS"
        interval_code = self.zaman_araliklari.get(interval_display)

        self.log_message(f"Analiz başlatılıyor: {hisse_kodu_yf} ({interval_display}, {display_range_key}, Tip: {analysis_type})")
        self.message_text.config(state="normal")
        self.message_text.delete('1.0', tk.END)
        self.message_text.config(state="disabled")

        try:
            self._analiz_et_ve_gorsellestir(hisse_kodu_yf, interval_code, display_range_key, interval_display, analysis_type)
            self.fetch_and_display_fundamental_data(hisse_kodu_yf)
        except Exception as e:
            self.log_message(f"Bir hata oluştu: {e}")
            messagebox.showerror("Hata", f"Analiz sırasında bir hata oluştu: {e}")
            traceback.print_exc()

    def _analiz_et_ve_gorsellestir(self, hisse_kodu, interval, display_range_key, interval_display, analysis_type):
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
        veri_filtrelenmis = self.filter_data_by_display_range(veri.copy(), display_range_key)

        if veri_filtrelenmis.empty:
            self.log_message(f"Hata: Seçilen görüntüleme aralığı için yeterli veri yok.")
            return

        self.plot_analysis(veri_filtrelenmis, hisse_kodu, interval, display_range_key, interval_display, analysis_type)
        self.log_analysis_summary(veri_filtrelenmis)

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

    def plot_analysis(self, veri, hisse_kodu, interval, display_range_key, interval_display, analysis_type):
        self.log_message(f"Grafik oluşturuluyor ({analysis_type})...")

        # Mevcut grafik penceresini kapat
        if self.chart_window:
            try:
                self.chart_window.destroy()
            except tk.TclError:
                pass # Pencere zaten kapalı olabilir

        # Yeni bir Toplevel penceresi oluştur
        self.chart_window = tk.Toplevel(self.master)
        self.chart_window.title(f"Grafik: {hisse_kodu}")
        self.chart_window.geometry("1000x700")

        # mplfinance için sütun adlarını düzenle
        veri.index.name = 'Date'

        apds = [] # addplot listesi

        # Basit Analiz
        if analysis_type == "Basit":
            # EMA 50 ve EMA 200
            apds.append(mpf.make_addplot(veri['ema_50'], color='orange', panel=0, ylabel='EMA 50'))
            apds.append(mpf.make_addplot(veri['ema_200'], color='purple', panel=0, ylabel='EMA 200'))

            # Volume
            apds.append(mpf.make_addplot(veri['volume'], panel=1, type='bar', color='gray', ylabel='Hacim'))

            # RSI
            apds.append(mpf.make_addplot(veri['rsi_14'], panel=2, color='blue', ylabel='RSI'))
            apds.append(mpf.make_addplot(pd.Series(70, index=veri.index), panel=2, color='gray', linestyle='--', width=0.7))
            apds.append(mpf.make_addplot(pd.Series(30, index=veri.index), panel=2, color='gray', linestyle='--', width=0.7))

            panels = 3 # 0: Fiyat, 1: Hacim, 2: RSI
            panel_ratios = (3, 1, 1) # Fiyat, Hacim, RSI oranları

        # Detaylı Analiz
        else: # analysis_type == "Detaylı"
            # EMA 8, 13, 21
            apds.append(mpf.make_addplot(veri['ema_8'], color='#007bff', panel=0, ylabel='EMA 8'))
            apds.append(mpf.make_addplot(veri['ema_13'], color='#6f42c1', panel=0, ylabel='EMA 13'))
            apds.append(mpf.make_addplot(veri['ema_21'], color='#fd7e14', panel=0, ylabel='EMA 21'))

            # Bollinger Bantları
            apds.append(mpf.make_addplot(veri['bbu_20_2.0'], color='#28a745', linestyle='--', panel=0, ylabel='BB Upper'))
            apds.append(mpf.make_addplot(veri['bbl_20_2.0'], color='#dc3545', linestyle='--', panel=0, ylabel='BB Lower'))

            # Volume
            apds.append(mpf.make_addplot(veri['volume'], panel=1, type='bar', color='gray', ylabel='Hacim'))

            # RSI
            apds.append(mpf.make_addplot(veri['rsi_14'], panel=2, color='blue', ylabel='RSI'))
            apds.append(mpf.make_addplot(pd.Series(70, index=veri.index), panel=2, color='gray', linestyle='--', width=0.7))
            apds.append(mpf.make_addplot(pd.Series(30, index=veri.index), panel=2, color='gray', linestyle='--', width=0.7))

            # StochRSI
            apds.append(mpf.make_addplot(veri['stochrsik_14_14_3_3'], panel=3, color='#007bff', ylabel='StochRSI K'))
            apds.append(mpf.make_addplot(veri['stochrsid_14_14_3_3'], panel=3, color='#fd7e14', ylabel='StochRSI D'))

            # MACD
            apds.append(mpf.make_addplot(veri['macd_12_26_9'], panel=4, color='#007bff', ylabel='MACD'))
            apds.append(mpf.make_addplot(veri['macds_12_26_9'], panel=4, color='#fd7e14', ylabel='MACD Signal'))
            apds.append(mpf.make_addplot(veri['macdh_12_26_9'], type='bar', panel=4, color='#6c757d', ylabel='MACD Hist'))

            # ADX
            apds.append(mpf.make_addplot(veri['adx_14'], panel=5, color='#ffc107', ylabel='ADX'))
            apds.append(mpf.make_addplot(veri['dmp_14'], panel=5, color='#28a745', ylabel='+DI'))
            apds.append(mpf.make_addplot(veri['dmn_14'], panel=5, color='#dc3545', ylabel='-DI'))

            # ATR
            apds.append(mpf.make_addplot(veri['atrr_14'], panel=6, color='#17a2b8', ylabel='ATR'))

            # OBV
            apds.append(mpf.make_addplot(veri['obv'], panel=7, color='#ffc107', ylabel='OBV'))

            # BBW
            apds.append(mpf.make_addplot(veri['bbb_20_2.0'], panel=8, color='#6c757d', ylabel='BBW'))

            panels = 9 # 0: Fiyat, 1: Hacim, 2: RSI, 3: StochRSI, 4: MACD, 5: ADX, 6: ATR, 7: OBV, 8: BBW
            panel_ratios = (3, 1, 1, 1, 1, 1, 1, 1, 1) # Fiyat, Hacim, RSI, StochRSI, MACD, ADX, ATR, OBV, BBW oranları

        # Trend çizgileri için alines formatına dönüştür
        alines = self.find_and_draw_trendlines(veri, interval)

        # mplfinance stilini ayarla
        s = mpf.make_mpf_style(base_mpf_style='yahoo', rc={'figure.facecolor': 'white'})

        fig, axes = mpf.plot(veri,
                             type='candle',
                             style=s,
                             title=f'{hisse_kodu} Teknik Analiz ({interval_display}, {display_range_key})',
                             ylabel='Fiyat',
                             #ylabel_lower='Hacim', # Removed, now explicit in addplot
                             volume=False, # Set to False as volume is explicitly added
                             addplot=apds,
                             panel_ratios=panel_ratios,
                             figscale=1.5, # Figür boyutunu ayarla
                             returnfig=True,
                             alines=alines,
                             columns=['open', 'high', 'low', 'close', 'volume']
                            )

        # Grafiği Tkinter Canvas'ına göm
        self.current_chart_figure = fig
        canvas = FigureCanvasTkAgg(fig, master=self.chart_window)
        canvas.draw()
        canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        # Toolbar ekle
        toolbar = NavigationToolbar2Tk(canvas, self.chart_window)
        toolbar.update()
        toolbar.pack(side=tk.BOTTOM, fill=tk.X)

        self.log_message("Grafik başarıyla oluşturuldu.")

    def find_and_draw_trendlines(self, data, interval):
        self.log_message("Trend çizgileri için tepe ve dip noktaları aranıyor...")
        
        alines = []
        
        # Adjust distance and prominence based on interval
        if interval == "1h":
            distance = 3  # For hourly, look for peaks/troughs every 3 bars
            prominence_percentage = 0.001 # 0.1% of the price range
        elif interval == "4h":
            distance = 5 # For 4-hourly, look for peaks/troughs every 5 bars
            prominence_percentage = 0.002 # 0.2% of the price range
        elif interval == "1d":
            distance = 10 # For daily, look for peaks/troughs every 10 bars
            prominence_percentage = 0.005 # 0.5% of the price range
        elif interval == "1wk":
            distance = 15 # For weekly, look for peaks/troughs every 15 bars
            prominence_percentage = 0.01 # 1% of the price range
        elif interval == "1mo":
            distance = 20 # For monthly, look for peaks/troughs every 20 bars
            prominence_percentage = 0.015 # 1.5% of the price range
        else:
            distance = 10 # Default for any other interval
            prominence_percentage = 0.005 # Default prominence

        # Calculate prominence dynamically based on the current data's price range
        price_range = data['high'].max() - data['low'].min()
        if price_range == 0:
            self.log_message("Fiyat aralığı sıfır, trend çizgisi hesaplanamıyor.")
            return alines # Cannot calculate prominence if price range is zero

        prominence = price_range * prominence_percentage

        peaks, _ = find_peaks(data['high'], prominence=prominence, distance=distance)
        troughs, _ = find_peaks(-data['low'], prominence=prominence, distance=distance)
        self.log_message(f"{len(peaks)} tepe ve {len(troughs)} dip bulundu (distance={distance}, prominence={prominence:.2f}).")

        x_numeric = np.arange(len(data.index)).reshape(-1, 1)

        if len(peaks) >= 2:
            self.log_message("Direnç çizgisi hesaplanıyor...")
            x_peaks = x_numeric[peaks].reshape(-1, 1)
            y_peaks = data['high'].iloc[peaks].values

            model = LinearRegression()
            model.fit(x_peaks, y_peaks)

            # Draw line only between the first and last detected peak
            alines.append([
                (data.index[peaks[0]], model.predict(x_numeric[peaks[0]].reshape(1, -1))[0]),
                (data.index[peaks[-1]], model.predict(x_numeric[peaks[-1]].reshape(1, -1))[0])
            ])

        if len(troughs) >= 2:
            self.log_message("Destek çizgisi hesaplanıyor...")
            x_troughs = x_numeric[troughs].reshape(-1, 1)
            y_troughs = data['low'].iloc[troughs].values

            model = LinearRegression()
            model.fit(x_troughs, y_troughs)

            alines.append([
                (data.index[troughs[0]], model.predict(x_numeric[troughs[0]].reshape(1, -1))[0]),
                (data.index[troughs[-1]], model.predict(x_numeric[troughs[-1]].reshape(1, -1))[0])
            ])
        return alines

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

        summary.append("-------------------------------------\n")
        
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
        summary.append("-------------------------------------\n")
        
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
        if not hasattr(self, 'current_chart_figure') or not self.current_chart_figure:
            messagebox.showwarning("Uyarı", "Kaydedilecek bir grafik yok.")
            return
        try:
            file_path = filedialog.asksaveasfilename(
                defaultextension=".png",
                filetypes=[("PNG files", "*.png"), ("All files", "*.*")],
                title="Grafiği Kaydet"
            )
            if file_path:
                self.current_chart_figure.savefig(file_path, bbox_inches='tight')
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
        current_price = info.get('regularMarketPrice') or info.get('previousClose')

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
        price_range = window['high'].max() - window['low'].min()
        if price_range == 0: continue

        prominence_value = price_range * peak_prominence
        peaks, _ = find_peaks(window['high'], prominence=prominence_value)
        troughs, _ = find_peaks(-window['low'], prominence=prominence_value)

        if len(peaks) >= 2:
            x_peaks = peaks[-2:]
            y_peaks = window['high'].iloc[x_peaks.flatten()].values
            x_peaks_1d = x_peaks.flatten()
            if (x_peaks_1d[1] - x_peaks_1d[0]) != 0:
                slope = (y_peaks[1] - y_peaks[0]) / (x_peaks_1d[1] - x_peaks_1d[0])
                intercept = y_peaks[0] - slope * x_peaks_1d[0]
                resistance_price = slope * (lookback - 1) + intercept
                if data['close'].iloc[i] > resistance_price:
                    data.loc[data.index[i], 'breakout'] = 1

        if len(troughs) >= 2:
            x_troughs = troughs[-2:]
            y_troughs = window['low'].iloc[x_troughs.flatten()].values
            x_troughs_1d = x_troughs.flatten()
            if (x_troughs_1d[1] - x_troughs_1d[0]) != 0:
                slope = (y_troughs[1] - y_troughs[0]) / (x_troughs_1d[1] - x_troughs_1d[0])
                intercept = y_troughs[0] - slope * x_troughs_1d[0]
                support_price = slope * (lookback - 1) + intercept
                if data['close'].iloc[i] < support_price:
                    data.loc[data.index[i], 'breakout'] = -1
    return data

if __name__ == "__main__":
    root = tk.Tk()
    app = StockAnalyzerApp(root)
    root.mainloop()