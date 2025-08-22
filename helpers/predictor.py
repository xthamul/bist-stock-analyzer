import pandas as pd
import pandas_ta as ta
import yfinance as yf
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.metrics import accuracy_score, classification_report
import numpy as np

def get_stock_data_for_prediction(ticker, interval="1d", period="5y"):
    """
    Belirli bir hisse senedi için yfinance kullanarak veri çeker.
    """
    data = yf.download(ticker, interval=interval, period=period, progress=False, auto_adjust=False)
    if data.empty:
        return None
    
    if isinstance(data.columns, pd.MultiIndex):
        data.columns = data.columns.droplevel(1)
    
    data.columns = [col.lower() for col in data.columns]
    return data

def calculate_prediction_features(df):
    """
    Tahmin modeli için teknik göstergeleri ve ek özellikleri hesaplar.
    """
    df_copy = df.copy()

    # Temel göstergeler
    df_copy.ta.ema(length=8, append=True)
    df_copy.ta.ema(length=13, append=True)
    df_copy.ta.ema(length=21, append=True)
    df_copy.ta.ema(length=50, append=True)
    df_copy.ta.ema(length=200, append=True)
    df_copy.ta.bbands(length=20, append=True)
    df_copy.ta.stochrsi(append=True)
    df_copy.ta.macd(append=True)
    df_copy.ta.rsi(append=True)
    df_copy.ta.adx(append=True)
    df_copy.ta.atr(append=True)
    df_copy.ta.obv(append=True)

    # Volatilite ve Momentum Özellikleri
    df_copy['volatility_30d'] = df_copy['close'].rolling(window=30).std() * (252**0.5)
    df_copy['momentum_5d'] = df_copy['close'] / df_copy['close'].shift(5) - 1
    df_copy['rsi_x_macd'] = df_copy['RSI_14'] * df_copy['MACD_12_26_9']
    
    # Sütun adlarını düzeltme
    if isinstance(df_copy.columns, pd.MultiIndex):
        df_copy.columns = ['_'.join(col).strip() for col in df_copy.columns.values]
    
    df_copy.columns = [col.lower() for col in df_copy.columns]

    # Eksik değerleri doldur
    df_copy = df_copy.fillna(method='ffill').fillna(method='bfill')
    
    return df_copy

def create_target_variable(df, forecast_horizon=1):
    """
    Hedef değişkeni oluşturur: Sonraki günün kapanış fiyatı bugünkünden yüksekse 1, değilse 0.
    """
    df['target'] = (df['close'].shift(-forecast_horizon) > df['close']).astype(int)
    df = df.dropna() # Son satırda NaN oluşur, onu düşür
    return df

def train_prediction_model(df):
    """
    Random Forest modelini GridSearchCV ile en iyi parametreleri bularak eğitir ve değerlendirir.
    """
    features = [col for col in df.columns if col not in ['open', 'high', 'low', 'close', 'volume', 'target', 'dividends', 'stock splits']]
    
    X = df[features]
    y = df['target']

    train_size = int(len(df) * 0.8)
    X_train, X_test = X.iloc[:train_size], X.iloc[train_size:]
    y_train, y_test = y.iloc[:train_size], y.iloc[train_size:]

    # GridSearchCV için parametre grid'i
    param_grid = {
        'n_estimators': [50, 100, 200],
        'max_depth': [None, 10, 20, 30],
        'min_samples_split': [2, 5, 10]
    }

    # Modeli ve GridSearchCV'ü oluştur
    rf = RandomForestClassifier(random_state=42, class_weight='balanced')
    grid_search = GridSearchCV(estimator=rf, param_grid=param_grid, cv=3, n_jobs=1, verbose=1)
    
    grid_search.fit(X_train, y_train)

    best_model = grid_search.best_estimator_
    best_params = grid_search.best_params_

    y_pred = best_model.predict(X_test)

    accuracy = accuracy_score(y_test, y_pred)
    report = classification_report(y_test, y_pred, output_dict=True)
    report_df = pd.DataFrame(report).transpose()

    test_results = X_test.copy()
    test_results['actual'] = y_test
    test_results['predicted'] = y_pred
    
    return best_model, features, accuracy, report_df, test_results, best_params

def get_latest_prediction(model, latest_data, features):
    """
    En son veri noktasını kullanarak tahmin yapar.
    """
    if latest_data.empty:
        return "Yeterli veri yok."
    
    # Modelin beklediği özelliklerin son veri noktasında olduğundan emin ol
    latest_features = latest_data[features].iloc[-1].values.reshape(1, -1)
    prediction = model.predict(latest_features)[0]
    
    if prediction == 1:
        return "Yarınki kapanış fiyatının bugünkünden yüksek olması bekleniyor (Yükseliş)."
    else:
        return "Yarınki kapanış fiyatının bugünkünden düşük olması bekleniyor (Düşüş)."

if __name__ == "__main__":
    # Örnek kullanım
    ticker = "GARAN.IS"
    
    print(f"{ticker} için veri çekiliyor...")
    data = get_stock_data_for_prediction(ticker)

    if data is not None:
        print("Özellikler hesaplanıyor...")
        data_with_features = calculate_prediction_features(data)
        
        print("Hedef değişken oluşturuluyor...")
        data_final = create_target_variable(data_with_features)

        if not data_final.empty:
            print("Model eğitiliyor...")
            model, features = train_prediction_model(data_final)
            
            print("\nEn son tahmin yapılıyor...")
            latest_prediction = get_latest_prediction(model, data_final, features)
            print(latest_prediction)
        else:
            print("Hedef değişken oluşturulduktan sonra veri boş kaldı.")
    else:
        print(f"{ticker} için veri çekilemedi.")
