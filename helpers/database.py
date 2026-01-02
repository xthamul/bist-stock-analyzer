import sqlite3
import pandas as pd
import json
from datetime import datetime

DB_FILE = "portfolio.db"


def get_db_connection():
    """Veritabanı bağlantısı oluşturur."""
    conn = sqlite3.connect(DB_FILE, detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Veritabanı tablolarını (eğer yoksa) oluşturur."""
    conn = get_db_connection()
    cursor = conn.cursor()
    # İşlemler tablosu
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            hisse TEXT NOT NULL,
            miktar REAL NOT NULL,
            alis_fiyati REAL NOT NULL,
            tarih DATE NOT NULL
        )
    """
    )
    # Kullanıcı tercihleri tablosu
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS user_preferences (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        )
    """
    )
    # Alarmlar tablosu
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS alarms (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            hisse TEXT NOT NULL,
            condition_type TEXT NOT NULL,
            value REAL NOT NULL,
            status TEXT NOT NULL DEFAULT 'active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    conn.commit()
    conn.close()


def add_transaction(hisse, miktar, alis_fiyati, tarih):
    """Veritabanına yeni bir işlem ekler."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO transactions (hisse, miktar, alis_fiyati, tarih) VALUES (?, ?, ?, ?)",
        (hisse, miktar, alis_fiyati, tarih),
    )
    conn.commit()
    conn.close()


def get_all_transactions():
    """Tüm işlemleri bir DataFrame olarak döndürür."""
    conn = get_db_connection()
    df = pd.read_sql_query("SELECT * FROM transactions ORDER BY tarih DESC", conn)
    conn.close()
    return df


def remove_transactions(transaction_ids):
    """Verilen ID'lere sahip işlemleri siler."""
    conn = get_db_connection()
    cursor = conn.cursor()
    placeholders = ", ".join("?" for _ in transaction_ids)
    query = f"DELETE FROM transactions WHERE id IN ({placeholders})"
    cursor.execute(query, tuple(transaction_ids))
    conn.commit()
    conn.close()

# --- Kullanıcı Tercihleri Fonksiyonları ---

def set_preference(key, value):
    """Veritabanına bir kullanıcı tercihini (anahtar-değer) kaydeder."""
    conn = get_db_connection()
    cursor = conn.cursor()
    json_value = json.dumps(value)
    cursor.execute("REPLACE INTO user_preferences (key, value) VALUES (?, ?)", (key, json_value))
    conn.commit()
    conn.close()

def get_preference(key, default=None):
    """Veritabanından bir kullanıcı tercihini okur."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT value FROM user_preferences WHERE key = ?", (key,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return json.loads(row['value'])
    return default

# --- Alarm Fonksiyonları ---

def add_alarm(hisse, condition_type, value):
    """Veritabanına yeni bir alarm ekler."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO alarms (hisse, condition_type, value, status, created_at) VALUES (?, ?, ?, 'active', ?)",
        (hisse, condition_type, value, datetime.now())
    )
    conn.commit()
    conn.close()

def get_active_alarms():
    """Durumu 'active' olan tüm alarmları döndürür."""
    conn = get_db_connection()
    df = pd.read_sql_query("SELECT * FROM alarms WHERE status = 'active'", conn)
    conn.close()
    return df

def get_all_alarms():
    """Tüm alarmları en yeniden eskiye doğru sıralanmış bir DataFrame olarak döndürür."""
    conn = get_db_connection()
    df = pd.read_sql_query("SELECT * FROM alarms ORDER BY created_at DESC", conn)
    conn.close()
    return df
    
def update_alarm_status(alarm_id, status):
    """Belirli bir alarmın durumunu günceller."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE alarms SET status = ? WHERE id = ?", (status, alarm_id))
    conn.commit()
    conn.close()

def delete_alarm(alarm_id):
    """Belirli bir alarmı ID'sine göre siler."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM alarms WHERE id = ?", (alarm_id,))
    conn.commit()
    conn.close()
