import requests
import asyncio
from datetime import datetime # datetime düzeltildi
from sqlalchemy.orm import Session
from app.models import BypassLink
from app.database import SessionLocal
# Botlarını import et
from .aylink_bypass import AyLinkBypassUltimate
from .ouo_bypass import OuoAutoBypass
# Yeni VT servisini import et
from .virustotal import scan_url_with_virustotal

def run_bypass_process(link_id: int, url: str):
    db: Session = SessionLocal()
    record = db.query(BypassLink).filter(BypassLink.id == link_id).first()
    
    try:
        # --- 1. BYPASS İŞLEMİ ---
        cozum = None
        if "ay.link" in url or "ay.live" in url:
            bot = AyLinkBypassUltimate(debug_mode=False)
            cozum = bot.baslat(url)
        elif "ouo" in url:
            bot = OuoAutoBypass()
            cozum = bot.hedef_linki_bul(url)
            
        # --- 2. SONUÇ VE GÜVENLİK ---
        if cozum:
            record.resolved_url = cozum
            record.status = "success"
            
            # --- VIRUSTOTAL CHECK ---
            try:
                # Async fonksiyonu senkron içinde çalıştır
                print(f"🛡️ VT Taraması başlıyor: {cozum}")
                vt_status = asyncio.run(scan_url_with_virustotal(cozum))
                
                record.safety_status = vt_status
                record.last_scanned_at = datetime.utcnow()
                print(f"🛡️ Güvenlik Sonucu: {vt_status}")
                
            except Exception as vt_err:
                print(f"⚠️ VirusTotal hatası: {vt_err}")
                record.safety_status = "Error"
        else:
            record.status = "failed"
        
        db.commit()
        
        # --- 3. WEBHOOK ---
        if record.webhook_url:
            try:
                payload = {
                    "id": record.id,
                    "original_url": record.original_url,
                    "resolved_url": record.resolved_url,
                    "status": record.status,
                    "safety_status": record.safety_status
                }
                requests.post(record.webhook_url, json=payload, timeout=5)
                print(f"✅ Webhook gönderildi -> {record.webhook_url}")
            except Exception as w_err:
                print(f"⚠️ Webhook başarısız: {w_err}")

    except Exception as e:
        print(f"❌ Genel Motor Hatası: {e}")
        record.status = "error"
        db.commit()
    finally:
        db.close()