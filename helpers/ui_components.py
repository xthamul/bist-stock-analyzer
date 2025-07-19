
# Bu dosya, hem Streamlit hem de Tkinter uygulamaları için metin tabanlı özetler üretir.

def generate_fundamental_summary(info, as_markdown=True):
    """Temel veriler için yorumlar ve anahtar bilgiler üretir."""
    summary_parts = []

    # Finansal Sağlık
    debt_to_equity = info.get('debtToEquity')
    current_ratio = info.get('currentRatio')
    if debt_to_equity is not None and current_ratio is not None:
        if debt_to_equity < 0.5 and current_ratio > 1.5:
            summary_parts.append("Finansal Sağlık: Güçlü bir finansal yapıya işaret ediyor (Düşük borç, yüksek likidite).")
        elif debt_to_equity < 1.0 and current_ratio > 1.0:
            summary_parts.append("Finansal Sağlık: Finansal durum dengeli görünüyor.")
        else:
            summary_parts.append("Finansal Sağlık: Finansal riskler taşıyabilir (Yüksek borç veya düşük likidite).")
    
    # Büyüme
    revenue_growth = info.get('revenueGrowth')
    earnings_growth = info.get('earningsGrowth')
    if revenue_growth is not None and earnings_growth is not None:
        if revenue_growth > 0.10 and earnings_growth > 0.15:
            summary_parts.append("Büyüme: Güçlü gelir ve kazanç büyümesi sergiliyor.")
        else:
            summary_parts.append("Büyüme: Büyüme oranları yavaş veya negatif.")

    # Değerleme
    trailing_pe = info.get('trailingPE')
    price_to_book = info.get('priceToBook')
    if trailing_pe is not None and price_to_book is not None:
        if trailing_pe < 15 and price_to_book < 2:
            summary_parts.append("Değerleme: Göstergeler cazip bir değerlemeye işaret edebilir.")
        else:
            summary_parts.append("Değerleme: Göstergeler şirketin pahalı olabileceğini gösteriyor.")

    # Karlılık
    return_on_equity = info.get('returnOnEquity')
    profit_margins = info.get('profitMargins')
    if return_on_equity is not None and profit_margins is not None:
        if return_on_equity > 0.15 and profit_margins > 0.10:
            summary_parts.append("Karlılık: Yüksek özkaynak karlılığı ve güçlü net kar marjı.")
        else:
            summary_parts.append("Karlılık: Karlılık oranları düşük.")

    # Anahtar Bilgiler Metni
    key_info_map = {
        'longName': 'Şirket Adı', 'symbol': 'Sembol', 'sector': 'Sektör',
        'marketCap': 'Piyasa Değeri', 'trailingPE': 'F/K Oranı', 'forwardPE': 'Tahmini F/K',
        'priceToBook': 'PD/DD', 'dividendYield': 'Temettü Verimi',
        'returnOnEquity': 'Özkaynak Karlılığı', 'profitMargins': 'Net Kar Marjı',
    }
    key_info_text = ""
    for key, label in key_info_map.items():
        value = info.get(key, "N/A")
        if isinstance(value, (int, float)):
            if 'Verim' in label or 'Karlılık' in label or 'Marjı' in label:
                key_info_text += f"{label:<25}: {value:.2%}\n"
            else:
                key_info_text += f"{label:<25}: {value:,.2f}\n"
        else:
            key_info_text += f"{label:<25}: {value}\n"

    if as_markdown:
        # Streamlit için Markdown formatı
        md_summary = [s.replace("Finansal Sağlık:", "**Finansal Sağlık:**").replace("Büyüme:", "**Büyüme:**").replace("Değerleme:", "**Değerleme:**").replace("Karlılık:", "**Karlılık:**") for s in summary_parts]
        return "\n\n".join(md_summary)
    else:
        # Tkinter için düz metin formatı
        return "\n".join(summary_parts), key_info_text

def generate_technical_summary(veri, as_markdown=True):
    """Teknik veriler için yorumlar üretir."""
    son_veri = veri.iloc[-1]
    summary = []

    # Genel Teknik Görünüm
    if son_veri['ema_50'] > son_veri['ema_200'] and son_veri['close'] > son_veri['ema_50']:
        summary.append("Genel Görünüm: Güçlü Yükseliş Eğilimi.")
    elif son_veri['ema_50'] < son_veri['ema_200'] and son_veri['close'] < son_veri['ema_50']:
        summary.append("Genel Görünüm: Güçlü Düşüş Eğilimi.")
    else:
        summary.append("Genel Görünüm: Yön arayışı veya düzeltme mevcut.")

    # RSI
    if son_veri['rsi_14'] > 70:
        summary.append(f"RSI ({son_veri['rsi_14']:.2f}): Aşırı alım bölgesinde.")
    elif son_veri['rsi_14'] < 30:
        summary.append(f"RSI ({son_veri['rsi_14']:.2f}): Aşırı satım bölgesinde.")
    else:
        summary.append(f"RSI ({son_veri['rsi_14']:.2f}): Nötr bölgede.")

    # MACD
    if son_veri['macd_12_26_9'] > son_veri['macds_12_26_9']:
        summary.append("MACD: Pozitif kesişim mevcut.")
    else:
        summary.append("MACD: Negatif kesişim mevcut.")

    # ADX
    if son_veri['adx_14'] > 25:
        trend_yonu = "yükseliş" if son_veri['dmp_14'] > son_veri['dmn_14'] else "düşüş"
        summary.append(f"ADX ({son_veri['adx_14']:.2f}): Güçlü bir {trend_yonu} trendi mevcut.")
    else:
        summary.append(f"ADX ({son_veri['adx_14']:.2f}): Zayıf veya trendsiz piyasa.")

    if as_markdown:
        # Streamlit için Markdown formatı
        return "\n\n".join([f"- {s}" for s in summary])
    else:
        # Tkinter için düz metin formatı
        return "\n".join(summary)
