"""
Basit URL Kısaltıcı Bypass — HTTP Redirect Takibi

Selenium gerektirmeyen kısaltıcılar için hafif çözüm.
Sadece HTTP 301/302 redirect zincirini takip eder.
Maliyet: ~0, Süre: ~0.5-2sn
"""

import httpx
from urllib.parse import urlparse
from app.logger import get_logger
from app.constants import BypassSentinel, REDIRECT_DOMAINS, extract_domain

_log = get_logger("redirect")

# Reusable Client → TCP connection pooling (DNS + handshake tasarrufu)
_client = httpx.Client(
    follow_redirects=True,
    timeout=8,
    headers={
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                      "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
    },
)


def domain_destekleniyor_mu(url: str) -> bool:
    """URL'nin basit redirect ile çözülebilir olup olmadığını kontrol eder."""
    return extract_domain(url) in REDIRECT_DOMAINS


def resolve(url: str) -> str | None:
    """
    URL'yi HTTP redirect takibi ile çözer.
    Başarılıysa hedef URL döner, başarısızsa None.
    """
    _log.info(f"Redirect çözümleniyor: {url}")
    
    try:
        # HEAD ile dene (daha hızlı)
        response = _client.head(url)
        
        final_url = str(response.url)
        
        # Bazı siteler HEAD'e yanıt vermiyor, GET ile tekrar dene
        if final_url == url or response.status_code >= 400:
            response = _client.get(url)
            final_url = str(response.url)
        
        # 404 kontrolü
        if response.status_code == 404:
            _log.warning(f"404 döndü: {url}")
            return BypassSentinel.NOT_FOUND
        
        # Aynı domain'de kaldıysa çözülemedi
        original_domain = urlparse(url).netloc.lower()
        final_domain = urlparse(final_url).netloc.lower()
        
        if original_domain == final_domain:
            _log.warning(f"Redirect çözülemedi (aynı domain): {url} → {final_url}")
            return None
        
        _log.info(f"Çözüldü: {url} → {final_url}")
        return final_url
        
    except httpx.TimeoutException:
        _log.warning(f"Timeout: {url}")
        return BypassSentinel.TIMEOUT
    except httpx.ConnectError:
        _log.warning(f"Bağlantı hatası: {url}")
        return None
    except Exception as e:
        _log.error(f"Redirect hatası: {e}")
        return None
