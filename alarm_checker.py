import time
import logging
from plyer import notification
import pandas as pd

# Proje kök dizinindeki diğer modülleri import edebilmek için
import sys
sys.path.append('.')

import helpers.database as db
from helpers.data_handler import get_stock_data

# Loglama ayarları
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(message)s",
    filename="alarms.log",
    filemode="a",
)

CHECK_INTERVAL_SECONDS = 60  # Alarmları kontrol etme aralığı (saniye)  

def check_alarms():
    """Veritabanındaki aktif alarmları kontrol eder ve koşullar sağlanırsa bildirim gönderir."""
    logging.info("Aktif alarmlar kontrol ediliyor...")
    active_alarms = db.get_active_alarms()

    if active_alarms.empty:
        logging.info("Kontrol edilecek aktif alarm bulunamadı.")
        return

    # Her hisse için en son fiyatı bir kez çekmek üzere hisseleri grupla
    unique_stocks = active_alarms['hisse'].unique()
    
    for stock_code in unique_stocks:
        try:
            hisse_yf = f"{stock_code}.IS"
            # Sadece son 2 günlük veriyi çekmek yeterli
            latest_data = get_stock_data(hisse_yf, interval="1d", period="2d")
            if latest_data is None or latest_data.empty:
                logging.warning(f"{stock_code} için güncel fiyat alınamadı.")
                continue
            
            current_price = latest_data['close'].iloc[-1]
            
            # Bu hisseye ait alarmları filtrele
            stock_alarms = active_alarms[active_alarms['hisse'] == stock_code]

            for _, alarm in stock_alarms.iterrows():
                condition_met = False
                target_value = alarm['value']
                condition_type = alarm['condition_type']
                
                if condition_type == 'Fiyat >=' and current_price >= target_value:
                    condition_met = True
                elif condition_type == 'Fiyat <=' and current_price <= target_value:
                    condition_met = True
                
                if condition_met:
                    logging.info(f"ALARM TETİKLENDİ: {alarm['hisse']} fiyatı ({current_price:.2f}) {condition_type} {target_value:.2f} koşulunu sağladı.")
                    
                    # Masaüstü bildirimi gönder
                    try:
                        notification.notify(
                            title=f"Borsa Alarmı: {alarm['hisse']}",
                            message=f"{alarm['hisse']} fiyatı {current_price:.2f} TL oldu. Alarm koşulu: {condition_type} {target_value:.2f}",
                            app_name="BIST Analiz Platformu",
                            timeout=30  # Bildirimin ekranda kalma süresi (saniye)
                        )
                        logging.info("Masaüstü bildirimi başarıyla gönderildi.")
                    except Exception as e:
                        logging.error(f"Masaüstü bildirimi gönderilemedi: {e}")

                    # Alarmın durumunu 'triggered' olarak güncelle
                    db.update_alarm_status(alarm['id'], 'triggered')
                    logging.info(f"{alarm['id']} ID'li alarm 'triggered' olarak güncellendi.")

        except Exception as e:
            logging.error(f"{stock_code} için alarmlar kontrol edilirken bir hata oluştu: {e}")


if __name__ == "__main__":
    print("Alarm kontrolcüsü başlatıldı.")
    print(f"Alarmlar her {CHECK_INTERVAL_SECONDS} saniyede bir kontrol edilecek.")
    print("Bu pencereyi açık bıraktığınız sürece alarmlarınız çalışacaktır.")
    print("Kapatmak için CTRL+C tuşlarına basın.")
    
    # Başlamadan önce veritabanının var olduğundan emin ol
    db.init_db()

    while True:
        try:
            check_alarms()
            time.sleep(CHECK_INTERVAL_SECONDS)
        except KeyboardInterrupt:
            print("\nAlarm kontrolcüsü kapatılıyor.")
            break
        except Exception as e:
            logging.critical(f"Ana döngüde beklenmedik bir hata oluştu: {e}")
            # Beklenmedik hatalarda bir süre bekleyip tekrar dene
            time.sleep(CHECK_INTERVAL_SECONDS * 2)
