# app/constants.py
"""
Merkezi sabitler — magic string yerine enum kullanımı.
Tüm status, fail_reason, safety_status ve domain registry burada tanımlı.
"""
import sys
from enum import Enum
from typing import Optional
from urllib.parse import urlparse

# Python 3.10 uyumluluğu — StrEnum 3.11'de eklendi
if sys.version_info >= (3, 11):
    from enum import StrEnum
else:
    class StrEnum(str, Enum):
        pass


class LinkStatus(StrEnum):
    """BypassLink.status alanı için olası değerler."""
    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"
    ERROR = "error"


class FailReason(StrEnum):
    """BypassLink.fail_reason alanı için olası değerler."""
    LINK_NOT_FOUND = "link_not_found"
    TIMEOUT = "timeout"
    UNKNOWN = "unknown"


class SafetyStatus(StrEnum):
    """BypassLink.safety_status alanı için olası değerler."""
    SCANNING = "scanning"
    CLEAN = "Clean"
    MALICIOUS = "Malicious"
    SUSPICIOUS = "Suspicious"
    UNKNOWN = "Unknown"
    ERROR = "Error"
    TIMEOUT = "Timeout"


class BypassSentinel(StrEnum):
    """Bypass servislerinin döndürdüğü özel sentinel değerleri."""
    NOT_FOUND = "__NOT_FOUND__"
    TIMEOUT = "__TIMEOUT__"


class BypassType(StrEnum):
    """Her domain'in hangi bypass servisi ile çözüleceğini belirler."""
    REDIRECT = "redirect"
    OUO = "ouo"
    AYLINK = "aylink"
    TRLINK = "trlink"
    SHORTEST = "shortest"
    CUTYIO = "cutyio"


class ApiPlan(StrEnum):
    """API kullanım planları ve günlük istek limitleri."""
    FREE = "free"           # 50 istek/gün
    STARTER = "starter"     # 500 istek/gün
    PRO = "pro"             # 5.000 istek/gün
    BUSINESS = "business"   # 50.000 istek/gün
    WEBSITE = "website"     # Sınırsız — kendi web sitemiz için


# Plan → günlük limit eşlemesi (0 = sınırsız)
PLAN_DAILY_LIMITS: dict[ApiPlan, int] = {
    ApiPlan.FREE: 50,
    ApiPlan.STARTER: 500,
    ApiPlan.PRO: 5_000,
    ApiPlan.BUSINESS: 50_000,
    ApiPlan.WEBSITE: 0,  # Sınırsız
}


# Genel rate limit (IP bazlı, dakika başına)
RATE_LIMIT_PER_MINUTE = 30


# =========================================================================
# MERKEZİ DOMAIN REGISTRY — Tek kaynak, tek güncelleme noktası
# =========================================================================
DOMAIN_REGISTRY: dict[str, BypassType] = {
    # Heavy — Browser gerektiren (AyLink: Scrapling ile token alma)
    "ay.link": BypassType.AYLINK,
    "ay.live": BypassType.AYLINK,

    # Fast — OUO (curl_cffi + reCAPTCHA)
    "ouo.io": BypassType.OUO,
    "ouo.press": BypassType.OUO,

    # Fast — Basit HTTP redirect
    "bit.ly": BypassType.REDIRECT,
    "bit.do": BypassType.REDIRECT,
    "tinyurl.com": BypassType.REDIRECT,
    "t.co": BypassType.REDIRECT,
    "is.gd": BypassType.REDIRECT,
    "v.gd": BypassType.REDIRECT,
    "rb.gy": BypassType.REDIRECT,
    "shorturl.at": BypassType.REDIRECT,
    "shorturl.asia": BypassType.REDIRECT,
    "cutt.ly": BypassType.REDIRECT,
    "tl.tc": BypassType.REDIRECT,
    "s.id": BypassType.REDIRECT,
    "t.ly": BypassType.REDIRECT,
    "tiny.cc": BypassType.REDIRECT,
    "ow.ly": BypassType.REDIRECT,
    "buff.ly": BypassType.REDIRECT,
    "adf.ly": BypassType.REDIRECT,
    "bc.vc": BypassType.REDIRECT,
    "soo.gd": BypassType.REDIRECT,
    "goo.gl": BypassType.REDIRECT,
    "rebrand.ly": BypassType.REDIRECT,
    "short.io": BypassType.REDIRECT,
    "kutt.it": BypassType.REDIRECT,

    # Fast — TR Shortener'lar (curl_cffi)
    "tr.link": BypassType.TRLINK,
    "shorte.st": BypassType.SHORTEST,
    "sh.st": BypassType.SHORTEST,
    "gestyy.com": BypassType.SHORTEST,
    "destyy.com": BypassType.SHORTEST,
    "cuty.io": BypassType.CUTYIO,
    "cutyion.com": BypassType.CUTYIO,
    "cutyio.com": BypassType.CUTYIO,
}

# =========================================================================
# TÜRETİLMİŞ SET'LER — Registry'den otomatik hesaplanır
# =========================================================================
ALLOWED_DOMAINS: set[str] = set(DOMAIN_REGISTRY.keys())
HEAVY_DOMAINS: set[str] = {d for d, t in DOMAIN_REGISTRY.items() if t in (BypassType.AYLINK, BypassType.OUO)}


def _domains_by_type(bypass_type: BypassType) -> set[str]:
    """Belirli bir bypass tipine ait domain'leri döndürür."""
    return {d for d, t in DOMAIN_REGISTRY.items() if t == bypass_type}


# Servisler bu set'leri _is_X() kontrollerinde kullanabilir
REDIRECT_DOMAINS = _domains_by_type(BypassType.REDIRECT)
OUO_DOMAINS = _domains_by_type(BypassType.OUO)
TRLINK_DOMAINS = _domains_by_type(BypassType.TRLINK)
SHORTEST_DOMAINS = _domains_by_type(BypassType.SHORTEST)
CUTYIO_DOMAINS = _domains_by_type(BypassType.CUTYIO)


def extract_domain(url: str) -> str:
    """URL'den domain çıkarır (www. prefix'ini kaldırır). Güvenli parsing."""
    try:
        host = urlparse(url).netloc.lower()
        return host[4:] if host.startswith("www.") else host
    except Exception:
        return ""


def get_bypass_type(url: str) -> Optional[BypassType]:
    """URL'nin hangi bypass servisi ile çözüleceğini döndürür. None = desteklenmiyor."""
    domain = extract_domain(url)
    return DOMAIN_REGISTRY.get(domain)


def is_heavy(url: str) -> bool:
    """URL'nin browser gerektiren bir domain olup olmadığını kontrol eder."""
    return extract_domain(url) in HEAVY_DOMAINS
