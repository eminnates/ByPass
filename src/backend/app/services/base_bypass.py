"""
Base Bypass — Tüm curl_cffi tabanlı bypass servisleri için ortak altyapı.

Alt sınıflar sadece _bypass_single() metodunu override eder.
Zincirleme bypass, session yönetimi ve domain kontrolü burada tanımlı.
"""

import time
from abc import ABC, abstractmethod
from curl_cffi import requests
from app.logger import get_logger
from app.constants import BypassSentinel, extract_domain


class BaseBypass(ABC):
    """
    Tüm curl_cffi tabanlı bypass servisleri için base class.
    
    Alt sınıf sorumluluğu:
        - DOMAINS: set[str] → kendi domain'leri
        - SERVICE_NAME: str → log'larda görünecek isim
        - _bypass_single(url) → tek link bypass mantığı
    
    Base class sağlar:
        - __init__: curl_cffi session oluşturma
        - is_own_domain: domain kontrolü
        - hedef_linki_bul: zincirleme bypass döngüsü
    """

    # Alt sınıflar bunları override etmeli
    DOMAINS: set = set()
    SERVICE_NAME: str = "base"
    MAX_DEPTH: int = 5

    def __init__(self, debug_mode=False, extra_headers=None, skip_session=False):
        self.debug_mode = debug_mode
        self._log = get_logger(self.SERVICE_NAME)
        if not skip_session:  # ← yeni
            self.client = requests.Session()
            headers = {
                'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
                'accept-language': 'en-US,en;q=0.9',
                'cache-control': 'max-age=0',
                'upgrade-insecure-requests': '1',
            }
            if extra_headers:
                headers.update(extra_headers)
            self.client.headers.update(headers)
    
        self._log.info(f"{self.SERVICE_NAME} Bypass hazır. Debug: {debug_mode}")

    def is_own_domain(self, url: str) -> bool:
        """URL'nin bu servisin domain'lerinden birine ait olup olmadığını kontrol eder."""
        return extract_domain(url) in self.DOMAINS

    @abstractmethod
    def _bypass_single(self, url: str):
        """
        Tek bir linki bypass eder. Alt sınıflar bunu implement etmeli.
        
        Döndürür:
            str: hedef URL (başarılı)
            BypassSentinel.NOT_FOUND: 404
            None: başarısız
        """
        ...

    def hedef_linki_bul(self, url: str):
        """Zincirleme bypass mantığı ile hedef linki bulur."""
        self._log.info(f"SÜREÇ BAŞLATILIYOR (curl_cffi): {url}")

        current_url = url
        start_time = time.time()

        for depth in range(1, self.MAX_DEPTH + 1):
            self._log.info(f"[{depth}] Bypass deneniyor: {current_url}")

            try:
                result = self._bypass_single(current_url)
            except Exception as e:
                self._log.error(f"Bypass sırasında hata: {e}")
                return None

            if result == BypassSentinel.NOT_FOUND:
                self._log.warning("Link bulunamadı (404).")
                return BypassSentinel.NOT_FOUND

            if not result:
                self._log.warning("Bypass başarısız, sonuç dönmedi.")
                return None

            self._log.info(f"Adım sonucu: {result}")

            if self.is_own_domain(result):
                self._log.info(f"Sonuç yine {self.SERVICE_NAME}! Tekrar bypass ediliyor...")
                current_url = result
            else:
                total_time = time.time() - start_time
                self._log.info(f"FİNAL ULAŞILDI: {result} ({total_time:.2f}s)")
                return result

        self._log.warning("Max derinliğe ulaşıldı.")
        return None
