"""
Shorte.st Bypass — curl_cffi ile Reklamlı Kısaltıcı Bypass

shorte.st reklam sayfası gösterip JS ile hedef URL'ye yönlendiren bir servis.
Mekanizma: GET → JS parse → destinationUrl/nextUrl çıkar → Final URL döndür
"""

import re
import base64
from bs4 import BeautifulSoup
from app.constants import BypassSentinel, SHORTEST_DOMAINS
from .base_bypass import BaseBypass


class ShorteStBypass(BaseBypass):
    DOMAINS = SHORTEST_DOMAINS
    SERVICE_NAME = "shortest"

    def __init__(self, debug_mode=False):
        super().__init__(debug_mode, extra_headers={
            'referer': 'https://www.google.com/',
        })

    def _bypass_single(self, url):
        """Tek bir shorte.st linkini bypass eder."""
        self._log.info(f"İstek atılıyor: {url}")

        try:
            res = self.client.get(url, impersonate="chrome124", timeout=30)

            # 404 Kontrolü
            if res.status_code == 404:
                return BypassSentinel.NOT_FOUND

            if res.status_code != 200:
                self._log.warning(f"HTTP {res.status_code} alındı.")
                return None

            html = res.text

            # 404 kontrolü (içerik bazlı)
            if "LINK NOT FOUND" in html or "Link not found" in html:
                return BypassSentinel.NOT_FOUND

            # JS'den hedef URL çıkar
            js_patterns = [
                r'var\s+destinationUrl\s*=\s*["\']([^"\']+)["\']',
                r'var\s+nextUrl\s*=\s*["\']([^"\']+)["\']',
                r'var\s+finalUrl\s*=\s*["\']([^"\']+)["\']',
                r'var\s+destination\s*=\s*["\']([^"\']+)["\']',
                r'var\s+goToUrl\s*=\s*["\']([^"\']+)["\']',
                r'"destinationUrl"\s*:\s*"([^"]+)"',
                r'"nextUrl"\s*:\s*"([^"]+)"',
                r'location\.href\s*=\s*["\']([^"\']+)["\']',
                r'window\.location\s*=\s*["\']([^"\']+)["\']',
                r'skipUrl\s*[=:]\s*["\']([^"\']+)["\']',
            ]

            for pattern in js_patterns:
                matches = re.findall(pattern, html, re.IGNORECASE)
                for match in matches:
                    if match.startswith("http") and not self.is_own_domain(match):
                        if "ad." not in match and "track." not in match:
                            self._log.info(f"JS'den URL çıkarıldı: {match}")
                            return match

            # HTML/meta etiketlerinden dene
            soup = BeautifulSoup(html, 'lxml')

            # Meta refresh
            meta_refresh = soup.find('meta', attrs={'http-equiv': re.compile(r'refresh', re.I)})
            if meta_refresh:
                content = meta_refresh.get('content', '')
                match = re.search(r'url=([^\s;"\']+)', content, re.IGNORECASE)
                if match and not self.is_own_domain(match.group(1)):
                    self._log.info(f"Meta refresh URL: {match.group(1)}")
                    return match.group(1)

            # Skip butonlarındaki href
            skip_links = soup.find_all('a', id=re.compile(r'skip|proceed|continue', re.I))
            if not skip_links:
                skip_links = soup.find_all('a', class_=re.compile(r'skip|proceed|continue', re.I))
            for link in skip_links:
                href = link.get('href', '')
                if href.startswith('http') and not self.is_own_domain(href):
                    self._log.info(f"Skip butonundan URL: {href}")
                    return href

            # Base64 encoded URL denemesi
            atob_pattern = r'atob\s*\(\s*["\']([^"\']+)["\']\s*\)'
            for match in re.findall(atob_pattern, html):
                try:
                    decoded = base64.b64decode(match).decode('utf-8')
                    if decoded.startswith('http') and not self.is_own_domain(decoded):
                        self._log.info(f"Base64'ten URL çıkarıldı: {decoded}")
                        return decoded
                except Exception:
                    pass

            self._log.warning("Bypass yöntemi bulunamadı.")
            return None

        except Exception as e:
            self._log.error(f"Bypass hatası: {e}")
            return None


if __name__ == "__main__":
    bot = ShorteStBypass(debug_mode=True)
    link = "https://shorte.st/test"
    sonuc = bot.hedef_linki_bul(link)
    print(f"Sonuç: {sonuc}")
