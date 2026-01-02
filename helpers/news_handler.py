import feedparser
import streamlit as st
from transformers import pipeline

@st.cache_data
def fetch_news_from_rss(feed_url):
    """
    Belirtilen RSS feed URL'sinden haberleri çeker ve bir liste olarak döndürür.
    """
    try:
        feed = feedparser.parse(feed_url)
        if feed.bozo:
            # Bozo biti, feed'in düzgün bir şekilde ayrıştırılmadığını gösterir.
            st.error(f"RSS akışı okunurken bir hata oluştu: {feed.bozo_exception}")
            return []
        return feed.entries
    except Exception as e:
        st.error(f"RSS akışı alınamadı: {e}")
        return []

@st.cache_resource
def get_sentiment_analyzer():
    """
    Duyarlılık analizi için Hugging Face modelini yükler ve önbelleğe alır.
    Bu, uygulamanın her çalıştığında modeli tekrar indirmesini engeller.
    """
    return pipeline(
        "sentiment-analysis",
        model="savasy/bert-base-turkish-sentiment-cased",
        tokenizer="savasy/bert-base-turkish-sentiment-cased"
    )

def analyze_sentiment(text):
    """
    Verilen metnin duyarlılığını analiz eder.
    'positive', 'negative', 'neutral' etiketlerini daha anlaşılır ifadelere çevirir.
    """
    try:
        analyzer = get_sentiment_analyzer()
        result = analyzer(text)
        label = result[0]['label']
        
        # Modelin etiketlerini standartlaştır
        if label.lower() == 'positive':
            return 'Pozitif'
        elif label.lower() == 'negative':
            return 'Negatif'
        else:
            return 'Nötr'
            
    except Exception as e:
        # Model yüklenemezse veya bir hata olursa, analizi atla
        print(f"Duyarlılık analizi hatası: {e}")
        return "Analiz Edilemedi"
