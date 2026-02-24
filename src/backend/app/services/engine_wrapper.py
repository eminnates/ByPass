"""
Bypass Engine Wrapper — Heavy/Fast 2 Aşamalı Mimari

Heavy: AyLink token alma (browser gerekli, 3 worker limit)
Fast:  AyLink API, OUO, Redirect (HTTP only, sınırsız)
"""
import requests
import threading
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.models import BypassLink
from app.database import SessionLocal
from app.logger import get_logger
from .aylink_bypass import AyLinkBypassUltimate
from .ouo_bypass import OuoAutoBypass
from .redirect_bypass import resolve as redirect_resolve, domain_destekleniyor_mu
from .virustotal import scan_url_with_virustotal_sync

log = get_logger("engine")


def _vt_scan_background(link_id: int, url: str):
    """VT taramasını arka planda çalıştırır."""
    db: Session = SessionLocal()
    try:
        log.info(f"VT arka plan taraması başlıyor: ID={link_id} | {url}")
        vt_status = scan_url_with_virustotal_sync(url)
        
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


def _save_result(link_id: int, cozum, url: str):
    """Bypass sonucunu DB'ye kaydeder ve VT taramasını başlatır."""
    db: Session = SessionLocal()
    try:
        record = db.query(BypassLink).filter(BypassLink.id == link_id).first()
        if not record:
            return

        if cozum and cozum.startswith("__"):
            record.status = "failed"
            if cozum == "__NOT_FOUND__":
                record.fail_reason = "link_not_found"
                log.warning(f"Link bulunamadı (404): ID={link_id}")
            elif cozum == "__TIMEOUT__":
                record.fail_reason = "timeout"
            else:
                record.fail_reason = "unknown"
        elif cozum:
            record.resolved_url = cozum
            record.status = "success"
            record.safety_status = "scanning"
        else:
            record.status = "failed"
            record.fail_reason = "unknown"
            log.warning(f"Bypass başarısız: ID={link_id}")

        db.commit()

        # VT taraması arka planda
        if record.status == "success" and cozum:
            vt_thread = threading.Thread(
                target=_vt_scan_background,
                args=(link_id, cozum),  # Çözülmüş URL'yi tara
                daemon=True,
            )
            vt_thread.start()

        # Webhook
        if record.webhook_url:
            try:
                payload = {
                    "id": record.id,
                    "original_url": record.original_url,
                    "resolved_url": record.resolved_url,
                    "status": record.status,
                    "safety_status": record.safety_status,
                }
                requests.post(record.webhook_url, json=payload, timeout=5)
                log.info(f"Webhook gönderildi -> {record.webhook_url}")
            except Exception as w_err:
                log.warning(f"Webhook başarısız: {w_err}")

    except Exception as e:
        log.error(f"Sonuç kaydetme hatası: {e}", exc_info=True)
        try:
            record = db.query(BypassLink).filter(BypassLink.id == link_id).first()
            if record:
                record.status = "error"
                db.commit()
        except:
            pass
    finally:
        db.close()


# =========================================================================
# FAST İŞLEMLER — Browser gerektirmez
# =========================================================================
def run_fast_bypass(link_id: int, url: str, aylink_tokens: dict = None):
    """
    Fast lane: HTTP tabanlı bypass.
    
    - Redirect: HTTP HEAD/GET
    - OUO: curl_cffi + reCAPTCHA  
    - AyLink API: token'larla /get/tk + /links/go2 (token'lar heavy'den gelir)
    """
    try:
        cozum = None

        if aylink_tokens:
            # AyLink 2. aşama — token'lar heavy'den geldi, sadece API çağır
            log.info(f"[FAST] AyLink API bypass: ID={link_id}")
            cozum = AyLinkBypassUltimate.api_bypass(aylink_tokens)

        elif domain_destekleniyor_mu(url):
            # Redirect bypass
            log.info(f"[FAST] Redirect bypass: ID={link_id}")
            cozum = redirect_resolve(url)

        elif "ouo" in url:
            # OUO bypass
            log.info(f"[FAST] OUO bypass: ID={link_id}")
            bot = OuoAutoBypass()
            cozum = bot.hedef_linki_bul(url)

        _save_result(link_id, cozum, url)

    except Exception as e:
        log.error(f"[FAST] Hata: ID={link_id} | {e}", exc_info=True)
        _save_result(link_id, None, url)


# =========================================================================
# HEAVY İŞLEMLER — Browser gerektirir
# =========================================================================
def run_heavy_token_fetch(link_id: int, url: str, fast_callback):
    """
    Heavy lane: AyLink token alma (browser açılır).
    Token'lar alındıktan sonra fast_callback ile API bypass tetiklenir.
    
    Args:
        fast_callback: Fonksiyon(link_id, url, tokens) — fast lane'e gönderir
    """
    try:
        bot = AyLinkBypassUltimate(debug_mode=False)
        tokens = bot.token_al(url)

        if tokens == "__NOT_FOUND__":
            _save_result(link_id, "__NOT_FOUND__", url)
            return

        if not tokens:
            _save_result(link_id, None, url)
            return

        # Token'lar alındı → Fast lane'e API bypass'ı gönder
        log.info(f"[HEAVY→FAST] Token'lar alındı, API bypass fast lane'e yönlendiriliyor: ID={link_id}")
        fast_callback(link_id, url, tokens)

    except Exception as e:
        log.error(f"[HEAVY] Token alma hatası: ID={link_id} | {e}", exc_info=True)
        _save_result(link_id, None, url)


# Geriye uyumluluk — eski run_bypass_process (tek çağrı ile tam bypass)
def run_bypass_process(link_id: int, url: str):
    """Eski interface — engine_wrapper dışında kullanılmamalı."""
    if "ay.link" in url or "ay.live" in url:
        bot = AyLinkBypassUltimate(debug_mode=False)
        cozum = bot.baslat(url)
    elif domain_destekleniyor_mu(url):
        cozum = redirect_resolve(url)
    elif "ouo" in url:
        bot = OuoAutoBypass()
        cozum = bot.hedef_linki_bul(url)
    else:
        cozum = None

    _save_result(link_id, cozum, url)