

import streamlit as st

def generate_fundamental_summary(info):
    """Temel veriler için yapay zeka destekli yorumlar üretir."""
    summary_parts = []

    # Finansal Sağlık Yorumu
    debt_to_equity = info.get('debtToEquity')
    current_ratio = info.get('currentRatio')
    if debt_to_equity is not None and current_ratio is not None:
        if debt_to_equity < 0.5 and current_ratio > 1.5:
            summary_parts.append("**Finansal Sağlık:** Şirketin borçluluk oranı düşük ve cari oranı yüksek, bu da güçlü bir finansal yapıya işaret ediyor. ✅")
        elif debt_to_equity < 1.0 and current_ratio > 1.0:
            summary_parts.append("**Finansal Sağlık:** Şirketin finansal durumu dengeli görünüyor, borçları yönetilebilir seviyede. ☑️")
        else:
            summary_parts.append("**Finansal Sağlık:** Şirketin borçluluk oranı yüksek veya cari oranı düşük, bu durum finansal riskler taşıyabilir. ⚠️")
    else:
        summary_parts.append("**Finansal Sağlık:** Yeterli veri olmadığı için finansal sağlık yorumu yapılamıyor. ❓")

    # Büyüme Potansiyeli Yorumu
    revenue_growth = info.get('revenueGrowth')
    earnings_growth = info.get('earningsGrowth')
    if revenue_growth is not None and earnings_growth is not None:
        if revenue_growth > 0.10 and earnings_growth > 0.15:
            summary_parts.append("**Büyüme Potansiyeli:** Şirket hem gelir hem de kazanç açısından güçlü bir büyüme sergiliyor, bu da gelecek için olumlu bir işaret. 🚀")
        elif revenue_growth > 0.05 or earnings_growth > 0.05:
            summary_parts.append("**Büyüme Potansiyeli:** Şirket makul bir büyüme gösteriyor, ancak daha güçlü bir ivme beklenebilir. ☑️")
        else:
            summary_parts.append("**Büyüme Potansiyeli:** Şirketin büyüme oranları düşük, bu da gelecekteki performans için bir endişe kaynağı olabilir. 📉")
    else:
        summary_parts.append("**Büyüme Potansiyeli:** Yeterli veri olmadığı için büyüme potansiyeli yorumu yapılamıyor. ❓")

    # Değerleme Yorumu
    trailing_pe = info.get('trailingPE')
    forward_pe = info.get('forwardPE')
    price_to_book = info.get('priceToBook')
    if trailing_pe is not None and forward_pe is not None and price_to_book is not None:
        if trailing_pe < 15 and forward_pe < 12 and price_to_book < 2:
            summary_parts.append("**Değerleme:** Şirket mevcut F/K, tahmini F/K ve PD/DD oranlarına göre cazip bir değerlemeye sahip olabilir. 💎")
        elif trailing_pe < 25 and forward_pe < 20 and price_to_book < 3:
            summary_parts.append("**Değerleme:** Şirket makul bir değerlemeye sahip görünüyor, ancak sektör ortalamaları ile karşılaştırmak faydalı olacaktır. ☑️")
        else:
            summary_parts.append("**Değerleme:** Şirketin değerleme oranları yüksek, bu da aşırı değerli olabileceğine işaret edebilir. ⚠️")
    else:
        summary_parts.append("**Değerleme:** Yeterli veri olmadığı için değerleme yorumu yapılamıyor. ❓")

    # Karlılık Yorumu
    return_on_equity = info.get('returnOnEquity')
    profit_margins = info.get('profitMargins')
    if return_on_equity is not None and profit_margins is not None:
        if return_on_equity > 0.15 and profit_margins > 0.10:
            summary_parts.append("**Karlılık:** Şirket yüksek özkaynak karlılığı ve güçlü net kar marjı ile oldukça karlı bir yapıya sahip. 💰")
        elif return_on_equity > 0.08 or profit_margins > 0.05:
            summary_parts.append("**Karlılık:** Şirket makul bir karlılık sergiliyor, ancak iyileştirme potansiyeli olabilir. ☑️")
        else:
            summary_parts.append("**Karlılık:** Şirketin karlılık oranları düşük, bu da operasyonel verimlilik sorunlarına işaret edebilir. 📉")
    else:
        summary_parts.append("**Karlılık:** Yeterli veri olmadığı için karlılık yorumu yapılamıyor. ❓")

    # Analist Tavsiyesi
    recommendation_key = info.get('recommendationKey')
    target_mean_price = info.get('targetMeanPrice')
    current_price = info.get('regularMarketPrice') or info.get('previousClose')

    if recommendation_key and target_mean_price and current_price:
        potential = ((target_mean_price - current_price) / current_price)
        summary_parts.append(f"**Analist Tavsiyesi:** Analistler genellikle '{recommendation_key}' tavsiyesinde bulunuyor. Ortalama hedef fiyat ({target_mean_price:.2f}) mevcut fiyata ({current_price:.2f}) göre **{potential:.2%}** potansiyel sunuyor.")
    elif recommendation_key:
        summary_parts.append(f"**Analist Tavsiyesi:** Analistler genellikle hisse senedi için '{recommendation_key}' tavsiyesinde bulunuyor.")
    
    return "\n\n".join(summary_parts)

def generate_technical_summary(veri):
    """Teknik veriler için yapay zeka destekli yorumlar üretir."""
    son_veri = veri.iloc[-1]
    summary = []

    # Genel Teknik Görünüm
    if son_veri['ema_50'] > son_veri['ema_200'] and son_veri['close'] > son_veri['ema_50']:
        summary.append("**Genel Teknik Görünüm:** Güçlü Yükseliş Eğilimi (Fiyatlar EMA50 ve EMA200 üzerinde, EMA50 > EMA200). 🟢")
    elif son_veri['ema_50'] < son_veri['ema_200'] and son_veri['close'] < son_veri['ema_50']:
        summary.append("**Genel Teknik Görünüm:** Güçlü Düşüş Eğilimi (Fiyatlar EMA50 ve EMA200 altında, EMA50 < EMA200). 🔴")
    else:
        summary.append("**Genel Teknik Görünüm:** Yön arayışı veya düzeltme mevcut. 🟡")

    # RSI
    if son_veri['rsi_14'] > 70:
        summary.append(f"**RSI ({son_veri['rsi_14']:.2f}):** Aşırı alım bölgesinde, düzeltme riski olabilir. ⚠️")
    elif son_veri['rsi_14'] < 30:
        summary.append(f"**RSI ({son_veri['rsi_14']:.2f}):** Aşırı satım bölgesinde, toparlanma potansiyeli olabilir. ✅")
    else:
        summary.append(f"**RSI ({son_veri['rsi_14']:.2f}):** Nötr bölgede.")

    # MACD
    if son_veri['macd_12_26_9'] > son_veri['macds_12_26_9']:
        summary.append(f"**MACD:** Pozitif kesişim mevcut, yükseliş momentumunu destekliyor. 🟢")
    else:
        summary.append(f"**MACD:** Negatif kesişim mevcut, düşüş momentumunu destekliyor. 🔴")

    # ADX
    if son_veri['adx_14'] > 25:
        trend_yonu = "yükseliş" if son_veri['dmp_14'] > son_veri['dmn_14'] else "düşüş"
        summary.append(f"**ADX ({son_veri['adx_14']:.2f}):** Güçlü bir {trend_yonu} trendi mevcut. 💪")
    else:
        summary.append(f"**ADX ({son_veri['adx_14']:.2f}):** Zayıf veya trendsiz bir piyasa yapısı. 횡")

    # Son Mum Formasyonu
    # Manuel hesaplamada mum formasyonu yok, bu kısmı kaldırıyoruz veya farklı bir yaklaşımla ekliyoruz.
    # candle_cols = [col for col in veri.columns if col.startswith('cdl_')]
    # last_pattern = veri[candle_cols].iloc[-1]
    # detected = last_pattern[last_pattern != 0]
    # if not detected.empty:
    #     p_name = detected.index[0].replace("cdl_", "").replace("_", " ").title()
    #     p_signal = "(Yükseliş ⬆️)" if detected.iloc[0] > 0 else "(Düşüş ⬇️)"
    #     summary.append(f"**Son Mum Formasyonu:** {p_name} {p_signal}")

    return "\n\n".join(summary)

