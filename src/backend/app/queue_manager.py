"""
Kuyruk Yöneticisi — Heavy / Fast Dual Lane

Heavy lane: Browser gerektiren işlemler (AyLink token alma, max 3 worker)  
Fast lane: HTTP-only bypass (OUO, redirect, AyLink API, sınırsız)

Tüm kuyruk durumu ve dispatch mantığı burada merkezileştirilmiştir.
"""

import threading
from typing import Optional
from concurrent.futures import ThreadPoolExecutor

from .constants import is_heavy
from .logger import get_logger
from .services.engine_wrapper import run_fast_bypass, run_heavy_token_fetch

log = get_logger("queue")

# =========================================================================
# EXECUTOR'LAR — 2GB RAM / 2 Core VPS için optimize edildi
# =========================================================================
heavy_executor = ThreadPoolExecutor(max_workers=3)    # Browser: RAM yoğun
fast_executor = ThreadPoolExecutor(max_workers=15)    # HTTP: I/O-bound, 15 yeterli
vt_executor = ThreadPoolExecutor(max_workers=3)       # VT API: rate limit var

# =========================================================================
# THREAD-SAFE KUYRUK TAKİBİ
# =========================================================================
_queue_lock = threading.Lock()
_heavy_queue: list[int] = []       # Browser kuyruğunda bekleyenler
_heavy_active: set[int] = set()    # Browser aktif işlemler
_fast_active: set[int] = set()     # HTTP aktif işlemler


def _dispatch_to_fast(link_id: int, url: str, tokens: dict = None):
    """
    Fast lane'e iş gönderir.
    Heavy tamamlandığında AyLink token'larını buraya yönlendirir.
    """
    with _queue_lock:
        _fast_active.add(link_id)

    log.info(f"[FAST] İşlem başladı: ID={link_id}")

    try:
        run_fast_bypass(link_id, url, aylink_tokens=tokens)
    finally:
        with _queue_lock:
            _fast_active.discard(link_id)
        log.info(f"[FAST] İşlem bitti: ID={link_id}")


def _tracked_heavy_process(link_id: int, url: str):
    """Heavy lane: Browser ile token al, sonra fast lane'e API bypass gönder."""
    with _queue_lock:
        if link_id in _heavy_queue:
            _heavy_queue.remove(link_id)
        _heavy_active.add(link_id)

    log.info(f"[HEAVY] İşlem başladı: ID={link_id} | Aktif: {len(_heavy_active)} | Kuyrukta: {len(_heavy_queue)}")

    try:
        run_heavy_token_fetch(
            link_id, url,
            fast_callback=lambda lid, u, tokens: fast_executor.submit(_dispatch_to_fast, lid, u, tokens)
        )
    finally:
        with _queue_lock:
            _heavy_active.discard(link_id)
        log.info(f"[HEAVY] İşlem bitti: ID={link_id} | Aktif: {len(_heavy_active)} | Kuyrukta: {len(_heavy_queue)}")


def _tracked_fast_process(link_id: int, url: str):
    """Fast lane: HTTP-only bypass. Yüksek öncelik, kuyruk yok, anında işlenir."""
    with _queue_lock:
        _fast_active.add(link_id)

    log.info(f"[FAST] İşlem başladı: ID={link_id}")

    try:
        run_fast_bypass(link_id, url)
    finally:
        with _queue_lock:
            _fast_active.discard(link_id)
        log.info(f"[FAST] İşlem bitti: ID={link_id}")


# =========================================================================
# PUBLIC API
# =========================================================================
def submit_to_queue(link_id: int, url: str):
    """Domain'e göre heavy veya fast lane'e yönlendirir."""
    if is_heavy(url):
        with _queue_lock:
            _heavy_queue.append(link_id)
        log.info(f"[HEAVY] Kuyruğa eklendi: ID={link_id} | Sıra: {len(_heavy_queue)}")
        heavy_executor.submit(_tracked_heavy_process, link_id, url)
    else:
        log.info(f"[FAST] Anında işleme alındı: ID={link_id}")
        fast_executor.submit(_tracked_fast_process, link_id, url)


def get_queue_position(link_id: int) -> Optional[int]:
    """Verilen ID'nin kuyruktaki sırasını döner. Fast = her zaman 0."""
    with _queue_lock:
        if link_id in _fast_active:
            return 0
        if link_id in _heavy_active:
            return 0
        if link_id in _heavy_queue:
            return _heavy_queue.index(link_id) + 1
    return None


def get_queue_info() -> dict:
    """Kuyruk durumunu döner."""
    with _queue_lock:
        return {
            "fast": {
                "active_count": len(_fast_active),
                "max_workers": 50,
                "active_ids": list(_fast_active),
            },
            "heavy": {
                "active_count": len(_heavy_active),
                "max_workers": 3,
                "active_ids": list(_heavy_active),
                "waiting_count": len(_heavy_queue),
                "waiting_ids": list(_heavy_queue),
            },
        }


def get_heavy_queue_length() -> int:
    """Heavy kuyruğundaki bekleyen sayısını döner."""
    with _queue_lock:
        return len(_heavy_queue)


def shutdown():
    """Graceful shutdown — tüm executor'ları bekleyerek kapatır."""
    log.info("Executor'lar kapatılıyor...")
    heavy_executor.shutdown(wait=True, cancel_futures=True)
    fast_executor.shutdown(wait=True, cancel_futures=True)
    vt_executor.shutdown(wait=True, cancel_futures=True)
    log.info("Tüm executor'lar kapatıldı.")
