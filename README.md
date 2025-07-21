# BIST Hisse Senedi Analiz Platformu

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Bu proje, Borsa İstanbul'da (BIST) işlem gören hisse senetleri için kapsamlı teknik ve temel analiz sunan, Streamlit ile geliştirilmiş interaktif bir web uygulamasıdır. Kullanıcıların hisse senedi verilerini görselleştirmesine, finansal oranları karşılaştırmasına ve basit ticaret stratejilerini test etmesine olanak tanır.

---

### 🖼️ Ekran Görüntüsü

İlerde eklenecektir.

---

### ✨ Özellikler

-   **📈 Kapsamlı Teknik Analiz:**
    -   Hareketli Ortalamalar (EMA 8, 13, 21, 50, 200)
    -   Bollinger Bantları
    -   Göreceli Güç Endeksi (RSI)
    -   MACD (Hareketli Ortalama Yakınsama/Iraksama)
    -   Ortalama Gerçek Aralık (ATR)
    -   ve daha birçok popüler teknik gösterge.
-   **🏢 Detaylı Temel Analiz:**
    -   Şirket profili, özet bilgiler ve temel oranlar (F/K, PD/DD vb.).
    -   Ayrıntılı finansal tablolar (Gelir Tablosu, Bilanço, Nakit Akışı).
-   **🆚 Sektör ve Hisse Karşılaştırma:**
    -   Bir hisseyi, kendi sektöründeki diğer şirketlerle temel metrikler bazında karşılaştırma.
    -   İki farklı hissenin fiyat performansını aynı grafikte görselleştirme.
-   **🧪 Strateji Testi (Backtesting):**
    -   Basit bir EMA Crossover (50/200 gün) stratejisinin geçmiş performansını test etme.
    -   Başlangıç sermayesi ve komisyon oranları gibi parametreleri ayarlama imkanı.
-   **📊 İnteraktif ve Özelleştirilebilir Grafikler:**
    -   Plotly ile oluşturulmuş, yakınlaştırma ve kaydırma yapılabilen dinamik grafikler.
    -   Farklı zaman aralıkları (saatlik, günlük, haftalık) ve tarih aralıkları seçme.
-   **🧾 Veri İndirme:**
    -   Analiz edilen hissenin tüm teknik verilerini CSV formatında indirme.

---

### 🛠️ Kullanılan Teknolojiler

-   **Python:** Ana programlama dili.
-   **Streamlit:** İnteraktif web arayüzünü oluşturmak için kullanılan ana kütüphane.
-   **Pandas:** Veri işleme ve analizi.
-   **yfinance:** Yahoo Finance API'sinden borsa verilerini çekmek için.
-   **Plotly:** İnteraktif ve zengin veri görselleştirmeleri oluşturmak için.
-   **backtesting.py:** Ticaret stratejilerinin geçmişe dönük test edilmesi için.

---

### 🚀 Kurulum ve Çalıştırma

Bu projeyi yerel makinenizde çalıştırmak için aşağıdaki adımları izleyin:

**1. Projeyi Klonlayın:**

```bash
git clone https://github.com/xthamul/bist-stock-analyzer.git
cd bist-stock-analyzer
```

**2. Sanal Ortam Oluşturun ve Aktif Edin:**

-   Python'da projeler için sanal bir ortam oluşturmak, bağımlılıkları yönetmek adına en iyi pratiktir.

```bash
# Sanal ortamı oluştur
python -m venv venv

# Sanal ortamı aktif et
# Windows için:
venv\Scripts\activate
# macOS / Linux için:
source venv/bin/activate
```

**3. Gerekli Kütüphaneleri Yükleyin:**

```bash
pip install -r requirements.txt
```

**4. Streamlit Uygulamasını Başlatın:**

```bash
streamlit run app.py
```

Bu komutu çalıştırdıktan sonra, varsayılan web tarayıcınızda uygulamanın açıldığı yeni bir sekme göreceksiniz.

---

### 📂 Dosya Yapısı

```
.
├── app.py                  # Ana Streamlit uygulama dosyası
├── requirements.txt        # Proje bağımlılıkları
├── helpers/                # Yardımcı modüllerin bulunduğu klasör
│   ├── data_handler.py     # Veri çekme ve indikatör hesaplama
│   ├── plotter.py          # Grafikleri çizdirme
│   ├── backtester.py       # Backtesting mantığı
│   └── ui_components.py    # Arayüz bileşenleri (özetler vb.)
├── .gitignore              # Git tarafından takip edilmeyecek dosyalar
└── README.md               # Bu dosya
```

---

### 🤝 Katkıda Bulunma

Katkıda bulunmak isterseniz, lütfen bir *pull request* açın veya bir *issue* oluşturun. Tüm katkılara açığız!

---

### 📄 Lisans

Bu proje [MIT Lisansı](https://opensource.org/licenses/MIT) altında lisanslanmıştır.
