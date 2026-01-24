import requests  # En üste ekle
from sqlalchemy.orm import Session
from app.models import BypassLink
from app.database import SessionLocal
from .aylink_bypass import AyLinkBypassUltimate
from .ouo_bypass import OuoAutoBypass

def run_bypass_process(link_id: int, url: str):
    db: Session = SessionLocal()
    record = db.query(BypassLink).filter(BypassLink.id == link_id).first()
    
    try:
        # --- BYPASS İŞLEMİ (AYNI) ---
        cozum = None
        if "ay.link" in url or "ay.live" in url:
            bot = AyLinkBypassUltimate(debug_mode=False)
            cozum = bot.baslat(url)
        elif "ouo" in url:
            bot = OuoAutoBypass()
            cozum = bot.hedef_linki_bul(url)
            
        # --- VERİTABANI GÜNCELLEME ---
        if cozum:
            record.resolved_url = cozum
            record.status = "success"
        else:
            record.status = "failed"
            
        db.commit() # Önce veritabanına kaydet
        
        # --- YENİ: WEBHOOK TETİKLEME ---
        # Eğer kayıtta bir webhook URL'i varsa oraya haber ver
        if record.webhook_url:
            print(f"📡 Webhook tetikleniyor: {record.webhook_url}")
            try:
                payload = {
                    "id": record.id,
                    "original_url": record.original_url,
                    "resolved_url": record.resolved_url,
                    "status": record.status
                }
                # Karşı sunucuya POST isteği atıyoruz
                requests.post(record.webhook_url, json=payload, timeout=5)
                print("✅ Webhook başarıyla gönderildi.")
            except Exception as w_err:
                print(f"⚠️ Webhook gönderilemedi: {w_err}")

    except Exception as e:
        print(f"Hata: {e}")
        record.status = "error"
        db.commit()
    finally:
        db.close()