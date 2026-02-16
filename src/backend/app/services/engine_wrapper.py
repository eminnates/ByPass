import requests
import asyncio
import threading
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.models import BypassLink
from app.database import SessionLocal
from app.logger import get_logger
from .aylink_bypass import AyLinkBypassUltimate
from .ouo_bypass import OuoAutoBypass
from .redirect_bypass import resolve as redirect_resolve, domain_destekleniyor_mu
from .virustotal import scan_url_with_virustotal

log = get_logger("engine")

def _vt_scan_background(link_id: int, url: str):
    """VT taramasını arka planda çalıştırır. Bypass'tan bağımsız."""
    db: Session = SessionLocal()
    try:
        log.info(f"VT arka plan taraması başlıyor: ID={link_id} | {url}")
        vt_status = asyncio.run(scan_url_with_virustotal(url))
        
        record = db.query(BypassLink).filter(BypassLink.id == link_id).first()
        if record:
            record.safety_status = vt_status
            record.last_scanned_at = datetime.now(timezone.utc)
            db.commit()
            log.info(f"VT sonucu kaydedildi: ID={link_id} | {vt_status}")
    except Exception as e:
        log.warning(f"VT arka plan hatası: ID={link_id} | {e}")
        try:
            record = db.query(BypassLink).filter(BypassLink.id == link_id).first()
            if record:
                record.safety_status = "Error"
                db.commit()
        except:
            pass
    finally:
        db.close()

def run_bypass_process(link_id: int, url: str):
    db: Session = SessionLocal()
    record = db.query(BypassLink).filter(BypassLink.id == link_id).first()
    
    try:
        # --- 1. BYPASS İŞLEMİ ---
        cozum = None
        
        # Katman 1: Basit HTTP redirect (Selenium yok, ~0.5sn)
        if domain_destekleniyor_mu(url):
            log.info(f"Basit redirect ile deneniyor: {url}")
            cozum = redirect_resolve(url)
        # Katman 2: Selenium bypass (ağır, ~30sn)
        elif "ay.link" in url or "ay.live" in url:
            bot = AyLinkBypassUltimate(debug_mode=False)
            cozum = bot.baslat(url)
        elif "ouo" in url:
            bot = OuoAutoBypass()
            cozum = bot.hedef_linki_bul(url)
            
        # --- 2. SONUÇ ---
        if cozum and cozum.startswith("__"):
            record.status = "failed"
            if cozum == "__NOT_FOUND__":
                record.fail_reason = "link_not_found"
                log.warning(f"Link bulunamadı (404): ID={link_id} | URL={url}")
            elif cozum == "__TIMEOUT__":
                record.fail_reason = "timeout"
                log.warning(f"Zaman aşımı: ID={link_id} | URL={url}")
            else:
                record.fail_reason = "unknown"
                log.warning(f"Bilinmeyen sinyal ({cozum}): ID={link_id} | URL={url}")
        elif cozum:
            record.resolved_url = cozum
            record.status = "success"
            record.safety_status = "scanning"  # Taranıyor olarak işaretle
        else:
            record.status = "failed"
            record.fail_reason = "unknown"
            log.warning(f"Bypass başarısız: ID={link_id} | URL={url}")
        
        db.commit()  # Sonucu HEMEN kaydet — kullanıcı beklemez
        
        # --- 3. VT TARAMASI (ARKA PLANDA) ---
        if record.status == "success" and cozum:
            vt_thread = threading.Thread(
                target=_vt_scan_background,
                args=(link_id, url),
                daemon=True
            )
            vt_thread.start()
            log.info(f"VT taraması arka plana alındı: ID={link_id}")
        
        # --- 4. WEBHOOK ---
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
                log.info(f"Webhook gönderildi -> {record.webhook_url}")
            except Exception as w_err:
                log.warning(f"Webhook başarısız: {w_err}")

    except Exception as e:
        log.error(f"Genel Motor Hatası: {e}", exc_info=True)
        record.status = "error"
        db.commit()
    finally:
        db.close()