"""
In-Memory Rate Limiter — Redis Gerektirmez

2GB RAM kısıtlı VPS için optimize edilmiş sliding window rate limiter.
Bellek kullanımı: ~5MB (10.000 benzersiz IP için).
5 dakika inaktif IP'ler otomatik temizlenir.

Thread-safe: tüm state bir Lock ile korunur.
"""

import time
import threading
from collections import defaultdict, deque
from app.logger import get_logger

log = get_logger("ratelimit")

# =========================================================================
# SLIDING WINDOW RATE LIMITER
# =========================================================================

_lock = threading.Lock()

# IP → deque of timestamps (son 60 saniyenin istekleri)
_ip_windows: dict[str, deque] = defaultdict(deque)

# Son temizlik zamanı
_last_cleanup = time.monotonic()

# Temizlik aralığı (saniye)
_CLEANUP_INTERVAL = 300  # 5 dakika
_WINDOW_SECONDS = 60     # 1 dakikalık pencere


def _cleanup_stale():
    """5 dakikadır istek yapmayan IP'lerin entry'lerini siler."""
    global _last_cleanup
    now = time.monotonic()

    if now - _last_cleanup < _CLEANUP_INTERVAL:
        return

    _last_cleanup = now
    cutoff = now - _CLEANUP_INTERVAL
    stale_keys = [ip for ip, dq in _ip_windows.items() if not dq or dq[-1] < cutoff]

    for key in stale_keys:
        del _ip_windows[key]

    if stale_keys:
        log.info(f"Rate limiter temizlik: {len(stale_keys)} inaktif IP silindi, "
                 f"aktif: {len(_ip_windows)}")


def check_rate_limit(identifier: str, max_requests: int) -> tuple[bool, int]:
    """
    Sliding window ile rate limit kontrolü.
    
    Args:
        identifier: IP adresi veya API key hash
        max_requests: Dakika başına izin verilen max istek
    
    Returns:
        (is_allowed, remaining_requests)
    """
    now = time.monotonic()

    with _lock:
        _cleanup_stale()

        window = _ip_windows[identifier]

        # Pencere dışındaki eski timestamp'leri temizle
        while window and window[0] <= now - _WINDOW_SECONDS:
            window.popleft()

        current_count = len(window)

        if current_count >= max_requests:
            remaining = 0
            return False, remaining

        # İstek izin verildi — timestamp ekle
        window.append(now)
        remaining = max_requests - current_count - 1
        return True, remaining


def get_limiter_stats() -> dict:
    """Monitoring için limiter istatistikleri."""
    with _lock:
        return {
            "tracked_ips": len(_ip_windows),
            "total_entries": sum(len(dq) for dq in _ip_windows.values()),
        }
