"""
Bypass Engine Wrapper — Heavy/Fast 2 Aşamalı Mimari

Heavy: AyLink token alma + OUO tam bypass (browser gerekli)
Fast:  AyLink API, Redirect ve diğer HTTP tabanlı bypass'lar
"""
import httpx
from datetime import datetime, timezone
from app.models import BypassLink
from app.logger import get_logger
from app.constants import LinkStatus, FailReason, SafetyStatus, BypassSentinel, BypassType, get_bypass_type
from .aylink_bypass import AyLinkBypassUltimate
from .ouo_bypass import OuoAutoBypass
from .redirect_bypass import resolve as redirect_resolve
from .trlink_bypass import TRLinkBypass
from .shortest_bypass import ShorteStBypass
from .cutyio_bypass import CutyIoBypass
from .virustotal import scan_url_with_virustotal_sync

log = get_logger("engine")


# Bypass tipi → çalıştırma fonksiyonu eşlemesi
def _run_redirect(url: str):
    return redirect_resolve(url)

_ouo_instance = None

def _get_ouo_bypass():
    global _ouo_instance
    if _ouo_instance is None:
        _ouo_instance = OuoAutoBypass(debug_mode=False)
    return _ouo_instance

def _run_ouo(url: str):
    return _get_ouo_bypass().hedef_linki_bul(url, close_browser_after=False)

def _run_trlink(url: str):
    return TRLinkBypass().hedef_linki_bul(url)

def _run_shortest(url: str):
    return ShorteStBypass().hedef_linki_bul(url)

def _run_cutyio(url: str):
    return CutyIoBypass().hedef_linki_bul(url)


# Registry: BypassType → handler fonksiyonu
_BYPASS_HANDLERS: dict[BypassType, callable] = {
    BypassType.REDIRECT: _run_redirect,
    BypassType.TRLINK: _run_trlink,
    BypassType.SHORTEST: _run_shortest,
    BypassType.CUTYIO: _run_cutyio,
    # AYLINK fast aşaması ayrı handle edilir (token gerektirir)
}


def _vt_scan_background(link_id: int, url: str):
    """VT taramasını arka planda çalıştırır."""
    from app.database import get_db_session

    try:
        log.info(f"VT arka plan taraması başlıyor: ID={link_id} | {url}")
        vt_status = scan_url_with_virustotal_sync(url)
        
        with get_db_session() as db:
            record = db.query(BypassLink).filter(BypassLink.id == link_id).first()
            if record:
                record.safety_status = str(vt_status)
                record.last_scanned_at = datetime.now(timezone.utc)
        log.info(f"VT sonucu kaydedildi: ID={link_id} | {vt_status}")
    except Exception as e:
        log.warning(f"VT arka plan hatası: ID={link_id} | {e}")
        try:
            with get_db_session() as db:
                record = db.query(BypassLink).filter(BypassLink.id == link_id).first()
                if record:
                    record.safety_status = SafetyStatus.ERROR
        except Exception:
            pass


def _send_webhook_background(webhook_url: str, payload: dict, link_id: int):
    """Webhook gönderimini worker kritik yolundan ayırır."""
    try:
        httpx.post(webhook_url, json=payload, timeout=5)
        log.info(f"Webhook gönderildi: ID={link_id} -> {webhook_url}")
    except Exception as err:
        log.warning(f"Webhook başarısız: ID={link_id} | {err}")


def _save_result(link_id: int, cozum, url: str):
    """Bypass sonucunu DB'ye kaydeder ve VT taramasını başlatır."""
    from app.database import get_db_session

    try:
        with get_db_session() as db:
            record = db.query(BypassLink).filter(BypassLink.id == link_id).first()
            if not record:
                return

            if cozum and cozum.startswith("__"):
                record.status = LinkStatus.FAILED
                if cozum == BypassSentinel.NOT_FOUND:
                    record.fail_reason = FailReason.LINK_NOT_FOUND
                    log.warning(f"Link bulunamadı (404): ID={link_id}")
                elif cozum == BypassSentinel.TIMEOUT:
                    record.fail_reason = FailReason.TIMEOUT
                else:
                    record.fail_reason = FailReason.UNKNOWN
            elif cozum:
                record.resolved_url = cozum
                record.status = LinkStatus.SUCCESS
                record.safety_status = SafetyStatus.SCANNING
            else:
                record.status = LinkStatus.FAILED
                record.fail_reason = FailReason.UNKNOWN
                log.warning(f"Bypass başarısız: ID={link_id}")

            # Webhook (commit öncesi data hazır)
            webhook_url = record.webhook_url
            webhook_payload = None
            if webhook_url:
                webhook_payload = {
                    "id": record.id,
                    "original_url": record.original_url,
                    "resolved_url": record.resolved_url,
                    "status": record.status,
                    "safety_status": record.safety_status,
                }

            # Status bilgilerini VT thread için sakla
            should_scan_vt = record.status == LinkStatus.SUCCESS and cozum

        # Session kapandıktan sonra (commit oldu) → ağ işlemleri
        if should_scan_vt:
            from app.queue_manager import vt_executor
            vt_executor.submit(_vt_scan_background, link_id, cozum)

        if webhook_payload and webhook_url:
            from app.queue_manager import webhook_executor
            webhook_executor.submit(_send_webhook_background, webhook_url, webhook_payload, link_id)

    except Exception as e:
        log.error(f"Sonuç kaydetme hatası: {e}", exc_info=True)
        try:
            with get_db_session() as db:
                record = db.query(BypassLink).filter(BypassLink.id == link_id).first()
                if record:
                    record.status = LinkStatus.ERROR
        except Exception:
            pass


# =========================================================================
# FAST İŞLEMLER — Browser gerektirmez
# =========================================================================
def run_fast_bypass(link_id: int, url: str, aylink_tokens: dict = None):
    """
    Fast lane: HTTP tabanlı bypass.
    Registry'den domain → handler eşlemesi ile çalışır.
    """
    try:
        cozum = None

        if aylink_tokens:
            # AyLink 2. aşama — token'lar heavy'den geldi, sadece API çağır
            log.info(f"[FAST] AyLink API bypass: ID={link_id}")
            cozum = AyLinkBypassUltimate.api_bypass(aylink_tokens)
        else:
            bypass_type = get_bypass_type(url)
            if bypass_type and bypass_type in _BYPASS_HANDLERS:
                log.info(f"[FAST] {bypass_type.value} bypass: ID={link_id}")
                cozum = _BYPASS_HANDLERS[bypass_type](url)

        _save_result(link_id, cozum, url)

    except Exception as e:
        log.error(f"[FAST] Hata: ID={link_id} | {e}", exc_info=True)
        _save_result(link_id, None, url)


# =========================================================================
# HEAVY İŞLEMLER — Browser gerektirir
# =========================================================================
def run_heavy_bypass(link_id: int, url: str, fast_callback):
    """
    Heavy lane: Browser işlemlerini yürütür.
    AyLink: Token alır ve fast_callback ile HTTP API'sine gönderir.
    OUO: Tüm işlemi browser içinde tamamlar.
    """
    try:
        bypass_type = get_bypass_type(url)
        
        # OUO doğrudan heavy lane üzerinde tamamen çözülür, token devri (fast lane) yapmaz.
        if bypass_type == BypassType.OUO:
            log.info(f"[HEAVY] OUO tam tarayıcı bypass başlıyor: ID={link_id}")
            cozum = _get_ouo_bypass().hedef_linki_bul(url)
            _save_result(link_id, cozum, url)
            return

        # AYLINK Token Alma Süreci
        bot = AyLinkBypassUltimate(debug_mode=False)
        tokens = bot.token_al(url)

        if tokens == BypassSentinel.NOT_FOUND:
            _save_result(link_id, BypassSentinel.NOT_FOUND, url)
            return

        if not tokens:
            _save_result(link_id, None, url)
            return

        # Token'lar alındı → Fast lane'e API bypass'ı gönder
        log.info(f"[HEAVY→FAST] Token'lar alındı, API bypass fast lane'e yönlendiriliyor: ID={link_id}")
        fast_callback(link_id, url, tokens)

    except Exception as e:
        log.error(f"[HEAVY] İşlem hatası: ID={link_id} | {e}", exc_info=True)
        _save_result(link_id, None, url)
def shutdown_ouo():
    """Uygulama kapanırken çağır."""
    global _ouo_instance
    if _ouo_instance is not None:
        _ouo_instance._stop_browser()
        _ouo_instance = None