import unittest
import os
import pandas as pd
from datetime import datetime

# Testleri çalıştırmadan önce DB_FILE'ı geçici bir dosya olarak ayarla
from helpers import database as db
db.DB_FILE = "test_portfolio.db"


class TestDatabase(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """Testler başlamadan önce veritabanını başlat."""
        if os.path.exists(db.DB_FILE):
            os.remove(db.DB_FILE)
        db.init_db()

    @classmethod
    def tearDownClass(cls):
        """Tüm testler bittikten sonra test veritabanı dosyasını sil."""
        if os.path.exists(db.DB_FILE):
            os.remove(db.DB_FILE)

    def setUp(self):
        """Her testten önce veritabanı tablolarını temizle."""
        conn = db.get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM transactions")
        cursor.execute("DELETE FROM user_preferences")
        cursor.execute("DELETE FROM alarms")
        conn.commit()
        conn.close()

    def test_transactions(self):
        """İşlem ekleme, alma ve silme fonksiyonlarını test et."""
        # 1. Başlangıçta hiç işlem olmamalı
        self.assertTrue(db.get_all_transactions().empty)

        # 2. İşlem ekle
        db.add_transaction("GARAN", 100, 10.5, "2023-01-15")
        db.add_transaction("THYAO", 50, 150.2, "2023-01-20")
        
        transactions = db.get_all_transactions()
        self.assertEqual(len(transactions), 2)
        self.assertEqual(transactions.iloc[0]['hisse'], "THYAO") # En son eklenen ilk gelir

        # 3. İşlem sil
        transaction_id_to_delete = transactions.iloc[0]['id']
        db.remove_transactions([transaction_id_to_delete])
        
        remaining_transactions = db.get_all_transactions()
        self.assertEqual(len(remaining_transactions), 1)
        self.assertEqual(remaining_transactions.iloc[0]['hisse'], "GARAN")

    def test_preferences(self):
        """Tercih kaydetme ve okuma fonksiyonlarını test et."""
        # 1. Başlangıçta değer olmamalı, varsayılan dönmeli
        self.assertIsNone(db.get_preference("non_existent_key"))
        self.assertEqual(db.get_preference("non_existent_key", default="default"), "default")

        # 2. String bir değer kaydet ve oku
        db.set_preference("string_key", "test_value")
        self.assertEqual(db.get_preference("string_key"), "test_value")

        # 3. Liste (array) bir değer kaydet ve oku
        my_list = ["GARAN", "THYAO", "EREGL"]
        db.set_preference("favorites", my_list)
        self.assertEqual(db.get_preference("favorites"), my_list)

        # 4. Üzerine yazma
        db.set_preference("string_key", "new_value")
        self.assertEqual(db.get_preference("string_key"), "new_value")

    def test_alarms(self):
        """Alarm ekleme, alma, güncelleme ve silme fonksiyonlarını test et."""
        # 1. Başlangıçta alarm olmamalı
        self.assertTrue(db.get_all_alarms().empty)
        self.assertTrue(db.get_active_alarms().empty)

        # 2. Alarm ekle
        db.add_alarm("GARAN", "Fiyat >=", 12.0)
        db.add_alarm("THYAO", "Fiyat <=", 140.0)

        all_alarms = db.get_all_alarms()
        active_alarms = db.get_active_alarms()
        self.assertEqual(len(all_alarms), 2)
        self.assertEqual(len(active_alarms), 2)

        # 3. Alarm durumunu güncelle
        alarm_to_update_id = active_alarms.iloc[0]['id']
        db.update_alarm_status(alarm_to_update_id, "triggered")
        
        self.assertEqual(len(db.get_active_alarms()), 1)
        
        # 4. Alarm sil
        db.delete_alarm(alarm_to_update_id)
        self.assertEqual(len(db.get_all_alarms()), 1)

if __name__ == '__main__':
    unittest.main()
