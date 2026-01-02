import sqlite3
import pandas as pd

DB_FILE = "portfolio.db"


def get_db_connection():
    """Veritabanı bağlantısı oluşturur."""
    conn = sqlite3.connect(DB_FILE)
    return conn


def init_db():
    """Veritabanı tablosunu (eğer yoksa) oluşturur."""
    conn = get_db_connection()
    cursor = conn.cursor()
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
    df = pd.read_sql_query("SELECT * FROM transactions", conn)
    conn.close()
    return df


def remove_transactions(transaction_ids):
    """Verilen ID'lere sahip işlemleri siler."""
    conn = get_db_connection()
    cursor = conn.cursor()
    # ID'leri bir demet (tuple) haline getirerek sorguya güvenli bir şekilde ekle
    placeholders = ", ".join("?" for _ in transaction_ids)
    query = f"DELETE FROM transactions WHERE id IN ({placeholders})"
    cursor.execute(query, tuple(transaction_ids))
    conn.commit()
    conn.close()
