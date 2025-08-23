import pandas as pd
import yfinance as yf
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC
from sklearn.neighbors import KNeighborsClassifier
from sklearn.model_selection import GridSearchCV
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    roc_auc_score,
    precision_score,
    recall_score,
    f1_score,
)
import numpy as np


def get_stock_data_for_prediction(ticker, interval="1d", period="5y"):
    """
    Belirli bir hisse senedi için yfinance kullanarak veri çeker.
    """
    data = yf.download(
        ticker, interval=interval, period=period, progress=False, auto_adjust=False
    )
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

    # --- Mevcut Göstergeler ---
    df_copy.ta.ema(length=8, append=True)
    df_copy.ta.ema(length=21, append=True)
    df_copy.ta.ema(length=50, append=True)
    df_copy.ta.ema(length=200, append=True)
    df_copy.ta.bbands(length=20, append=True)
    df_copy.ta.rsi(length=14, append=True)
    df_copy.ta.macd(append=True)
    df_copy.ta.atr(append=True)

    # --- Yeni Eklenen Özellikler ---

    # 1. Gecikmeli Fiyat Değişimleri (Lagged Returns)
    for lag in [1, 3, 5, 10, 21]:
        df_copy[f'return_{lag}d'] = df_copy["close"].pct_change(periods=lag)

    # 2. Hareketli Ortalama Farkları ve Oranları
    df_copy['ema_50_200_diff'] = df_copy['EMA_50'] - df_copy['EMA_200']
    df_copy['ema_8_21_diff'] = df_copy['EMA_8'] - df_copy['EMA_21']

    # 3. Gelişmiş Volatilite Ölçümleri
    # Bollinger Bant Genişliği (Mevcut bbands() zaten ekliyor olabilir, kontrol edelim)
    if 'BBB_20_2.0' in df_copy.columns:
        df_copy['bollinger_width'] = df_copy['BBB_20_2.0']
    
    # Fiyatın Bollinger Bantlarına göre konumu
    if 'BBL_20_2.0' in df_copy.columns and 'BBU_20_2.0' in df_copy.columns:
        df_copy['price_to_bb_upper'] = df_copy['close'] / df_copy['BBU_20_2.0']
        df_copy['price_to_bb_lower'] = df_copy['close'] / df_copy['BBL_20_2.0']

    # 4. Diğer Göstergeler
    df_copy.ta.obv(append=True)
    df_copy.ta.adx(append=True)
    df_copy.ta.stochrsi(append=True)

    # Sütun adlarını düzeltme ve temizleme
    if isinstance(df_copy.columns, pd.MultiIndex):
        df_copy.columns = ["_".join(col).strip() for col in df_copy.columns.values]

    df_copy.columns = [col.lower() for col in df_copy.columns]
    
    # Sonsuz değerleri NaN ile değiştir
    df_copy.replace([np.inf, -np.inf], np.nan, inplace=True)

    # Eksik değerleri doldur (önce ileri, sonra geri)
    df_copy = df_copy.fillna(method="ffill").fillna(method="bfill")

    return df_copy


def create_target_variable(df, forecast_horizon=1):
    """
    Hedef değişkeni oluşturur: Sonraki günün kapanış fiyatı bugünkünden yüksekse 1, değilse 0.
    """
    df["target"] = (df["close"].shift(-forecast_horizon) > df["close"]).astype(int)
    df = df.dropna()  # Son satırda NaN oluşur, onu düşür
    return df


def train_prediction_model(df, model_type="RandomForest"):
    """
    Seçilen modeli GridSearchCV ile en iyi parametreleri bularak eğitir ve değerlendirir.
    """
    features = [
        col
        for col in df.columns
        if col
        not in [
            "open",
            "high",
            "low",
            "close",
            "volume",
            "target",
            "dividends",
            "stock splits",
        ]
    ]

    X = df[features]
    y = df["target"]

    train_size = int(len(df) * 0.8)
    X_train, X_test = X.iloc[:train_size], X.iloc[train_size:]
    y_train, y_test = y.iloc[:train_size], y.iloc[train_size:]

    if model_type == "RandomForest":
        model = RandomForestClassifier(random_state=42, class_weight="balanced")
        param_grid = {
            "n_estimators": [50, 100, 200],
            "max_depth": [None, 10, 20, 30],
            "min_samples_split": [2, 5, 10],
        }
    elif model_type == "LogisticRegression":
        model = LogisticRegression(
            random_state=42, solver="liblinear", class_weight="balanced"
        )
        param_grid = {"C": [0.1, 1.0, 10.0], "penalty": ["l1", "l2"]}
    elif model_type == "SVC":
        model = SVC(random_state=42, probability=True, class_weight="balanced")
        param_grid = {"C": [0.1, 1.0, 10.0], "kernel": ["linear", "rbf"]}
    elif model_type == "GradientBoosting":
        model = GradientBoostingClassifier(random_state=42)
        param_grid = {
            "n_estimators": [50, 100, 200],
            "learning_rate": [0.01, 0.1, 0.2],
            "max_depth": [3, 5, 7],
        }
    elif model_type == "KNeighbors":
        model = KNeighborsClassifier()
        param_grid = {"n_neighbors": [3, 5, 7, 9], "weights": ["uniform", "distance"]}
    else:
        raise ValueError("Geçersiz model tipi.")

    # Modeli ve GridSearchCV'ü oluştur
    grid_search = GridSearchCV(
        estimator=model, param_grid=param_grid, cv=3, n_jobs=1, verbose=0
    )  # verbose=0 to reduce output

    grid_search.fit(X_train, y_train)

    best_model = grid_search.best_estimator_
    best_params = grid_search.best_params_

    y_pred = best_model.predict(X_test)

    accuracy = accuracy_score(y_test, y_pred)
    report = classification_report(y_test, y_pred, output_dict=True)
    report_df = pd.DataFrame(report).transpose()

    y_prob = None
    if hasattr(best_model, "predict_proba"):
        y_prob = best_model.predict_proba(X_test)[:, 1]  # Probability for ROC AUC

    roc_auc = roc_auc_score(y_test, y_prob) if y_prob is not None else np.nan
    precision = precision_score(y_test, y_pred)
    recall = recall_score(y_test, y_pred)
    f1 = f1_score(y_test, y_pred)

    test_results = X_test.copy()
    test_results["actual"] = y_test
    test_results["predicted"] = y_pred

    feature_importances = None
    if hasattr(best_model, "feature_importances_"):
        feature_importances = pd.Series(
            best_model.feature_importances_, index=features
        ).sort_values(ascending=False)
    elif hasattr(best_model, "coef_"):
        # For linear models, coefficients can be used as importance (absolute value)
        feature_importances = pd.Series(
            np.abs(best_model.coef_[0]), index=features
        ).sort_values(ascending=False)

    return (
        best_model,
        features,
        accuracy,
        report_df,
        test_results,
        best_params,
        roc_auc,
        precision,
        recall,
        f1,
        feature_importances,
    )


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
        return (
            "Yarınki kapanış fiyatının bugünkünden yüksek olması bekleniyor (Yükseliş)."
        )
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
            (
                model,
                features,
                accuracy,
                report_df,
                test_results,
                best_params,
                roc_auc,
                precision,
                recall,
                f1,
                feature_importances,
            ) = train_prediction_model(data_final)

            print("\nEn son tahmin yapılıyor...")
            latest_prediction = get_latest_prediction(model, data_final, features)
            print(latest_prediction)

            print(f"Accuracy: {accuracy:.2f}")
            print(f"ROC AUC: {roc_auc:.2f}")
            print(f"Precision: {precision:.2f}")
            print(f"Recall: {recall:.2f}")
            print(f"F1-Score: {f1:.2f}")
            if feature_importances is not None:
                print("Feature Importances:")
                print(feature_importances)

        else:
            print("Hedef değişken oluşturulduktan sonra veri boş kaldı.")
    else:
        print(f"{ticker} için veri çekilemedi.")
