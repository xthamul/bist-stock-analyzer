import sys
import traceback
import pandas as pd
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import time

# Proje yardımcı modüllerini içe aktar
from helpers.data_handler import (
    get_stock_data,
    get_fundamental_data,
    filter_data_by_date,
    calculate_indicators,
)
from helpers.plotter import plot_analysis_mpl
from helpers.ui_components import (
    generate_technical_summary,
    generate_fundamental_summary,
)


class StockAnalyzerApp:
    def __init__(self, master):
        self.master = master
        master.title("BIST Hisse Senedi Analiz Uygulaması")
        master.geometry("850x650")
        master.protocol("WM_DELETE_WINDOW", self.on_closing)

        # ... (sabitler ve yapılandırmalar aynı) ...
        self.hisse_gruplari = {
            "BIST 100 Hisseleri": [
                "AKBNK",
                "GARAN",
                "ISCTR",
                "YKBNK",
                "VAKBN",
                "THYAO",
                "ASELS",
                "TUPRS",
                "KCHOL",
                "BIMAS",
                "FROTO",
                "SISE",
                "ENKAI",
                "PETKM",
                "KOZAL",
                "TOASO",
                "KRDMD",
                "SAHOL",
                "SASA",
                "EREGL",
                "ARCLK",
                "PGSUS",
                "ALARK",
                "HEKTS",
                "TAVHL",
                "TCELL",
                "ODAS",
                "KORDS",
                "DOHOL",
                "ZOREN",
                "GWIND",
                "AGHOL",
                "AKSA",
                "OYAKC",
                "CCOLA",
                "TRKCM",
                "ADEL",
                "ULKER",
                "LOGO",
                "ISGYO",
                "MGROS",
                "GENIL",
                "ISDMR",
                "BRISA",
                "ALKIM",
                "AKGRT",
                "BANVT",
                "CIMSA",
                "ENJSA",
                "KARSN",
                "TTRAK",
                "GOZDE",
                "SOKM",
                "ALFAS",
                "BIOEN",
                "QUAGR",
                "BURCE",
                "DGNMO",
                "EKGYO",
                "GUBRF",
                "IZMDC",
                "MPARK",
                "NETAS",
                "PENTA",
                "TMSN",
                "TUCLK",
                "ULAS",
                "VERUS",
                "YUNSA",
            ],
            "BIST 30 Hisseleri": [
                "AKBNK",
                "GARAN",
                "ISCTR",
                "YKBNK",
                "VAKBN",
                "THYAO",
                "ASELS",
                "TUPRS",
                "KCHOL",
                "BIMAS",
                "FROTO",
                "SISE",
                "ENKAI",
                "PETKM",
                "KOZAL",
                "TOASO",
                "KRDMD",
                "SAHOL",
                "SASA",
                "EREGL",
                "ARCLK",
                "PGSUS",
                "TCELL",
                "ULKER",
                "ISDMR",
                "TAVHL",
                "KRDMA",
                "LOGO",
                "ODAS",
                "TRKCM",
            ],
            "Tüm Hisseler": [
                "QNBTR",
                "ASELS",
                "GARAN",
                "KCHOL",
                "THYAO",
                "ISBTR",
                "ISCTR",
                "ISKUR",
                "ENKAI",
                "AKBNK",
                "FROTO",
                "BIMAS",
                "TUPRS",
                "VAKBN",
                "YKBNK",
                "TCELL",
                "TTKOM",
                "SAHOL",
                "EREGL",
                "HALKB",
                "PKENT",
                "KENT",
                "CCOLA",
                "SASA",
                "PGSUS",
                "DSTKF",
                "OYAKC",
                "KLRHO",
                "SISE",
                "ZRGYO",
                "TOASO",
                "ISDMR",
                "TAVHL",
                "AEFES",
                "DOCO",
                "ASTOR",
                "MGROS",
                "TURSG",
                "GUBRF",
                "KOZAL",
                "ARCLK",
                "ENJSA",
                "AHGSLR",
                "YBTAS",
                "SRVGY",
                "BINHO",
                "HATSN",
                "VAKKO",
                "GSRAY",
                "ARMGD",
                "GLCVY",
                "REEDR",
                "ISFIN",
                "SONME",
                "HRKET",
                "GARFA",
                "IZFAS",
                "AGROT",
                "KARSN",
                "AKENR",
                "INGRM",
                "KLGYO",
                "BEGYO",
                "TSPOR",
                "GOKNR",
                "NATEN",
                "TRCAS",
                "VAKFN",
                "TNZTP",
                "TARKM",
                "CEMAS",
                "VKGYO",
                "BOSSA",
                "BOBET",
                "IZMDC",
                "SURGY",
                "INVEO",
                "ATATP",
                "IEYHO",
                "SNPAM",
                "ADEL",
                "BULGS",
                "EBEBK",
                "ENDAE",
                "KBORU",
                "SUWEN",
                "AKMGY",
                "GENTS",
                "ODAS",
                "ASGYO",
                "KMPUR",
                "BASCM",
                "DOKTA",
                "MEGMT",
                "EMKEL",
                "KAREL",
                "BMSTL",
                "YIGIT",
                "GOZDE",
                "MOBTL",
                "AYEN",
                "PAGYO",
                "DOBUR",
                "PARSN",
                "KOPOL",
                "OFSYM",
                "BIGEN",
                "KARTN",
                "ISKPL",
                "NTGAZ",
                "EKOS",
                "PLTUR",
                "GOLTS",
                "USAK",
                "PAPIL",
                "A1CAP",
                "PRKAB",
                "TCKRC",
                "MNDTR",
                "ORGE",
                "ERCB",
                "ATAKP",
                "KOCMT",
                "MAALT",
                "ALGYO",
                "AFYON",
                "ULUUN",
                "ALKA",
                "DMRGD",
                "PENTA",
                "CEMZY",
                "MERIT",
                "INDES",
                "ALKIM",
                "CEMTS",
                "IHAAS",
                "FORTE",
                "BFREN",
                "CATES",
                "DESA",
                "BORSK",
                "ARDYZ",
                "ALKLC",
                "PEKGY",
                "EGEGY",
                "MHRGY",
                "GOODY",
                "TKNSA",
                "HOROZ",
                "BARMA",
                "KZGYO",
                "BIGCH",
                "DCTTR",
                "DYOBY",
                "ANELE",
                "ELITE",
                "CGCAM",
                "ORMA",
                "ALVES",
                "KRVGD",
                "DERHL",
                "TSGYO",
                "SOKE",
                "KAPLM",
                "FMIZP",
                "ALCTL",
                "KONKA",
                "MERCN",
                "DAGHL",
                "METUR",
                "SEGMN",
                "YATAS",
                "ARSAN",
                "AHSGY",
                "BAGFS",
                "GSDHO",
                "EGEPO",
                "SERNT",
                "LRSHO",
                "YAPRK",
                "ONRYT",
                "AZTEK",
                "SAFKR",
                "MACKO",
                "MEDTR",
                "HUNER",
                "EKSUN",
                "CMBTN",
                "HURGZ",
                "TURGG",
                "GEREL",
                "TEKTU",
                "INTEM",
                "BRKVY",
                "KNFRT",
                "SAYAS",
                "KGYO",
                "INTEK",
                "OSMEN",
                "OTTO",
                "FENER",
                "BVSAN",
                "BRLSM",
                "TRILC",
                "SEGYO",
                "IHLAS",
                "ERBOS",
                "ARENA",
                "LKMNH",
                "KUTPO",
                "NETAS",
                "MARBL",
                "ISSEN",
                "MNDRS",
                "SANKO",
                "K",
                "ORCAY",
                "OZRDN",
                "ULAS",
                "ERSU",
                "ATAGY",
                "OYAYO",
                "VKFYO",
                "EKIZ",
                "ATSYH",
                "AVTUR",
                "RODRG",
                "HUBVC",
                "SANEL",
                "CASA",
                "MMCAS",
                "IDGYO",
                "GRNYO",
                "ATLAS",
                "MTRYO",
                "ETYAT",
                "DIRIT",
                "BRMEN",
                "EUKYO",
                "EUYO",
            ],
        }
        self.zaman_araliklari = {
            "1 Saatlik": "1h",
            "4 Saatlik": "4h",
            "1 Günlük": "1d",
            "1 Haftalık": "1wk",
            "1 Aylık": "1mo",
        }
        self.display_ranges = {
            "Tüm Veri": None,
            "Son 1 Ay": pd.DateOffset(months=1),
            "Son 3 Ay": pd.DateOffset(months=3),
            "Son 6 Ay": pd.DateOffset(months=6),
            "Son 1 Yıl": pd.DateOffset(years=1),
            "Son 2 Yıl": pd.DateOffset(years=2),
        }

        self.current_chart_figure = None
        self.chart_window = None

        self.notebook = ttk.Notebook(master)
        self.notebook.pack(pady=10, padx=10, expand=True, fill="both")
        self.tech_analysis_frame = ttk.Frame(self.notebook, padding="10")
        self.fundamental_analysis_frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(self.tech_analysis_frame, text="Teknik Analiz")
        self.notebook.add(self.fundamental_analysis_frame, text="Temel Analiz")
        self.setup_technical_analysis_tab()
        self.setup_fundamental_analysis_tab()

    def on_closing(self):
        plt.close("all")
        if self.chart_window:
            try:
                self.chart_window.destroy()
            except tk.TclError:
                pass
        self.master.destroy()
        sys.exit(0)

    def setup_technical_analysis_tab(self):
        controls_frame = ttk.LabelFrame(
            self.tech_analysis_frame, text="Kontroller", padding="10"
        )
        controls_frame.pack(fill="x", expand=False)

        ttk.Label(controls_frame, text="Hisse Grubu:").grid(
            row=0, column=0, padx=5, pady=5, sticky="w"
        )
        self.grup_secim = ttk.Combobox(
            controls_frame, values=list(self.hisse_gruplari.keys()), state="readonly"
        )
        self.grup_secim.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        self.grup_secim.set("BIST 100 Hisseleri")
        self.grup_secim.bind("<<ComboboxSelected>>", self.update_hisse_listesi)

        ttk.Label(controls_frame, text="Hisse Senedi:").grid(
            row=1, column=0, padx=5, pady=5, sticky="w"
        )
        self.hisse_secim = ttk.Combobox(controls_frame, state="readonly")
        self.hisse_secim.grid(row=1, column=1, padx=5, pady=5, sticky="ew")
        self.update_hisse_listesi()

        ttk.Label(controls_frame, text="Zaman Aralığı:").grid(
            row=2, column=0, padx=5, pady=5, sticky="w"
        )
        self.interval_secim = ttk.Combobox(
            controls_frame, values=list(self.zaman_araliklari.keys()), state="readonly"
        )
        self.interval_secim.grid(row=2, column=1, padx=5, pady=5, sticky="ew")
        self.interval_secim.set("1 Günlük")

        ttk.Label(controls_frame, text="Görüntüleme Aralığı:").grid(
            row=3, column=0, padx=5, pady=5, sticky="w"
        )
        self.display_range_secim = ttk.Combobox(
            controls_frame, values=list(self.display_ranges.keys()), state="readonly"
        )
        self.display_range_secim.grid(row=3, column=1, padx=5, pady=5, sticky="ew")
        self.display_range_secim.set("Son 1 Yıl")

        ttk.Label(controls_frame, text="Analiz Tipi:").grid(
            row=4, column=0, padx=5, pady=5, sticky="w"
        )
        self.analiz_tipi_secim = ttk.Combobox(
            controls_frame, values=["Detaylı", "Basit"], state="readonly"
        )
        self.analiz_tipi_secim.grid(row=4, column=1, padx=5, pady=5, sticky="ew")
        self.analiz_tipi_secim.set("Detaylı")

        button_frame = ttk.Frame(controls_frame)
        button_frame.grid(row=5, column=0, columnspan=2, pady=10)

        self.analyze_button = ttk.Button(
            button_frame, text="Analiz Et", command=self.run_analysis
        )
        self.analyze_button.pack(side="left", padx=5)

        self.save_button = ttk.Button(
            button_frame, text="Grafiği Kaydet", command=self.save_chart
        )
        self.save_button.pack(side="left", padx=5)

        log_frame = ttk.LabelFrame(
            self.tech_analysis_frame, text="Analiz Sonuçları", padding="10"
        )
        log_frame.pack(fill="both", expand=True, pady=(10, 0))

        self.message_text = tk.Text(
            log_frame, height=15, wrap="word", font=("Courier", 9)
        )
        self.message_text.pack(side="left", fill="both", expand=True)

        scrollbar = ttk.Scrollbar(log_frame, command=self.message_text.yview)
        scrollbar.pack(side="right", fill="y")
        self.message_text.config(yscrollcommand=scrollbar.set)

    def setup_fundamental_analysis_tab(self):
        self.fundamental_text = tk.Text(
            self.fundamental_analysis_frame,
            wrap="word",
            font=("Courier", 10),
            state="disabled",
        )
        self.fundamental_text.pack(padx=5, pady=5, fill="both", expand=True)

    def update_hisse_listesi(self, event=None):
        secilen_grup = self.grup_secim.get()
        hisseler = sorted(self.hisse_gruplari.get(secilen_grup, []))
        self.hisse_secim["values"] = hisseler
        if hisseler:
            self.hisse_secim.set(hisseler[0])
        else:
            self.hisse_secim.set("")

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

        self.log_message(f"Analiz başlatılıyor: {hisse_kodu_yf}...")
        self.message_text.config(state="normal")
        self.message_text.delete("1.0", tk.END)
        self.message_text.config(state="disabled")

        try:
            # Veri çekme işlemi için tekrar deneme mantığı
            veri_raw = None
            for attempt in range(3):
                try:
                    self.log_message(f"Veriler çekiliyor... (Deneme {attempt + 1})")
                    veri_raw = get_stock_data(hisse_kodu_yf, interval_code)
                    break  # Başarılı olursa döngüden çık
                except Exception as e:
                    self.log_message(f"Veri çekme hatası: {e}")
                    if attempt < 2:
                        time.sleep(2)  # Tekrar denemeden önce bekle

            if veri_raw is None or veri_raw.empty:
                self.log_message(f"Hata: {hisse_kodu_yf} için veri bulunamadı.")
                messagebox.showerror("Hata", f"{hisse_kodu_yf} için veri bulunamadı.")
                return

            self.log_message("Teknik göstergeler hesaplanıyor...")
            veri_hesaplanmis = calculate_indicators(veri_raw.copy())

            time_delta = self.display_ranges.get(display_range_key)
            veri_filtrelenmis = filter_data_by_date(
                veri_hesaplanmis, time_delta=time_delta
            )

            if veri_filtrelenmis.empty:
                self.log_message(
                    "Hata: Seçilen görüntüleme aralığı için yeterli veri yok."
                )
                return

            self.log_message("Grafik oluşturuluyor...")
            self.display_chart(
                veri_filtrelenmis, hisse_kodu_yf, interval_display, analysis_type
            )

            self.log_message("Teknik analiz özeti oluşturuluyor...")
            technical_summary = generate_technical_summary(
                veri_filtrelenmis, as_markdown=False
            )
            self.log_message("\n--- Teknik Analiz Özeti ---\n" + technical_summary)

            self.log_message("Temel veriler çekiliyor...")
            self.display_fundamental_data(hisse_kodu_yf)

        except Exception as e:
            error_message = f"Analiz sırasında bir hata oluştu: {e}"
            self.log_message(error_message)
            messagebox.showerror("Hata", error_message)
            traceback.print_exc()

    def display_chart(self, veri, hisse_kodu, interval_display, analysis_type):
        if self.chart_window:
            try:
                self.chart_window.destroy()
            except tk.TclError:
                pass

        self.chart_window = tk.Toplevel(self.master)
        self.chart_window.title(f"Grafik: {hisse_kodu}")
        self.chart_window.geometry("1100x800")

        fig, _ = plot_analysis_mpl(veri, hisse_kodu, interval_display, analysis_type)
        self.current_chart_figure = fig

        canvas = FigureCanvasTkAgg(fig, master=self.chart_window)
        canvas.draw()
        canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        toolbar = NavigationToolbar2Tk(canvas, self.chart_window)
        toolbar.update()
        toolbar.pack(side=tk.BOTTOM, fill=tk.X)
        self.log_message("Grafik başarıyla oluşturuldu.")

    def display_fundamental_data(self, hisse_kodu_yf):
        try:
            data = get_fundamental_data(hisse_kodu_yf)
            if not data or not data.get("info"):
                self.log_message("Temel veriler alınamadı.")
                return

            info = data["info"]
            self.fundamental_text.config(state="normal")
            self.fundamental_text.delete("1.0", tk.END)

            summary_text, key_info_text = generate_fundamental_summary(
                info, as_markdown=False
            )

            display_text = (
                f"--- {info.get('longName', hisse_kodu_yf)} Temel Verileri ---\n\n"
            )
            display_text += key_info_text
            display_text += "\n\n--- Yapay Zeka Destekli Temel Yorumlar ---\n"
            display_text += summary_text

            self.fundamental_text.insert(tk.END, display_text)
            self.log_message("Temel veriler başarıyla gösterildi.")

        except Exception as e:
            self.log_message(f"Temel veriler işlenirken hata oluştu: {e}")
        finally:
            self.fundamental_text.config(state="disabled")

    def save_chart(self):
        if not self.current_chart_figure:
            messagebox.showwarning("Uyarı", "Kaydedilecek bir grafik yok.")
            return
        try:
            file_path = filedialog.asksaveasfilename(
                defaultextension=".png",
                filetypes=[("PNG files", "*.png"), ("All files", "*.*")],
                title="Grafiği Kaydet",
            )
            if file_path:
                self.current_chart_figure.savefig(file_path, bbox_inches="tight")
                self.log_message(f"Grafik kaydedildi: {file_path}")
                messagebox.showinfo("Başarılı", f"Grafik kaydedildi: {file_path}")
        except Exception as e:
            self.log_message(f"Grafik kaydedilemedi: {e}")
            messagebox.showerror("Hata", f"Grafik kaydedilemedi: {e}")


if __name__ == "__main__":
    root = tk.Tk()
    app = StockAnalyzerApp(root)
    root.mainloop()
