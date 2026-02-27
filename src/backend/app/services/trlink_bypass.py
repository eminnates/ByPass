"""
TRLink Bypass — curl_cffi ile Reklamlı Kısaltıcı Bypass

tr.link (TRLink) Türkiye'nin en popüler para kazandıran link kısaltma servisi.
Reklam sayfası + countdown timer kullanır.
Mekanizma: GET → HTML parse → Token/form çıkar → POST ile final URL al
"""

import re
from urllib.parse import urlparse
from bs4 import BeautifulSoup
from app.constants import BypassSentinel, TRLINK_DOMAINS
from .base_bypass import BaseBypass


class TRLinkBypass(BaseBypass):
    DOMAINS = TRLINK_DOMAINS
    SERVICE_NAME = "trlink"

    def __init__(self, debug_mode=False):
        super().__init__(debug_mode, extra_headers={
            'accept-language': 'tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7',
        })

    def _bypass_single(self, url):
        """Tek bir tr.link linkini bypass eder."""
        self._log.info(f"İstek atılıyor: {url}")

        try:
            # 1. Sayfayı yükle
            res = self.client.get(url, impersonate="chrome124", timeout=30, allow_redirects=True)

            # 404 Kontrolü
            if res.status_code == 404:
                return BypassSentinel.NOT_FOUND

            if res.status_code != 200:
                self._log.warning(f"HTTP {res.status_code} alındı.")
                return None

            html = res.text
            final_url = str(res.url)

            # Direkt redirect olduysa
            original_domain = urlparse(url).netloc.lower()
            final_domain = urlparse(final_url).netloc.lower()
            if original_domain != final_domain:
                self._log.info(f"Direkt redirect: {final_url}")
                return final_url

            # 404 içerik kontrolü
            if "404" in html and ("bulunamad" in html or "not found" in html.lower()):
                return BypassSentinel.NOT_FOUND

            # JS içinden hedef URL çıkarmayı dene
            patterns = [
                r'var\s+url\s*=\s*["\']([^"\']+)["\']',
                r'window\.location\.href\s*=\s*["\']([^"\']+)["\']',
                r'window\.location\.replace\s*\(\s*["\']([^"\']+)["\']\s*\)',
                r'window\.open\s*\(\s*["\']([^"\']+)["\']\s*\)',
                r'href\s*=\s*["\']([^"\']*https?://[^"\']+)["\']',
                r'data-url\s*=\s*["\']([^"\']+)["\']',
                r'var\s+destination\s*=\s*["\']([^"\']+)["\']',
                r'redirect[_-]?url\s*[=:]\s*["\']([^"\']+)["\']',
            ]

            for pattern in patterns:
                matches = re.findall(pattern, html, re.IGNORECASE)
                for match in matches:
                    if match.startswith("http") and "tr.link" not in match and "trlink" not in match:
                        self._log.info(f"JS'den URL çıkarıldı: {match}")
                        return match

            # Form submit denemesi
            soup = BeautifulSoup(html, 'lxml')

            forms = soup.find_all('form')
            for form in forms:
                action = form.get('action', '')
                method = form.get('method', 'get').lower()

                inputs = form.find_all('input')
                data = {}
                for inp in inputs:
                    name = inp.get('name')
                    value = inp.get('value', '')
                    if name:
                        data[name] = value

                if data:
                    form_url = action if action.startswith('http') else f"https://tr.link{action}"

                    headers = {
                        'content-type': 'application/x-www-form-urlencoded',
                        'referer': url,
                    }

                    if method == 'post':
                        form_res = self.client.post(
                            form_url, data=data, headers=headers,
                            allow_redirects=False, impersonate="chrome124", timeout=30
                        )
                    else:
                        form_res = self.client.get(
                            form_url, params=data, headers=headers,
                            allow_redirects=False, impersonate="chrome124", timeout=30
                        )

                    location = form_res.headers.get('Location')
                    if location and "tr.link" not in location:
                        self._log.info(f"Form redirect: {location}")
                        return location

                    if form_res.status_code in (301, 302, 303, 307, 308):
                        if location:
                            return location

            # Meta refresh kontrolü
            meta_refresh = soup.find('meta', attrs={'http-equiv': re.compile(r'refresh', re.I)})
            if meta_refresh:
                content = meta_refresh.get('content', '')
                match = re.search(r'url=([^\s;"\']+)', content, re.IGNORECASE)
                if match:
                    self._log.info(f"Meta refresh URL: {match.group(1)}")
                    return match.group(1)

            # Link etiketlerinden dene
            links = soup.find_all('a', href=True)
            for link in links:
                href = link.get('href', '')
                text = link.get_text(strip=True).lower()
                classes = ' '.join(link.get('class', []))

                if any(kw in text for kw in ['devam', 'continue', 'get link', 'linke git', 'skip']):
                    if href.startswith('http') and 'tr.link' not in href:
                        return href
                if any(kw in classes for kw in ['btn', 'button', 'redirect', 'continue']):
                    if href.startswith('http') and 'tr.link' not in href:
                        return href

            self._log.warning("Bypass yöntemi bulunamadı.")
            return None

        except Exception as e:
            self._log.error(f"Bypass hatası: {e}")
            return None


if __name__ == "__main__":
    bot = TRLinkBypass(debug_mode=True)
    link = "https://tr.link/test"
    sonuc = bot.hedef_linki_bul(link)
    print(f"Sonuç: {sonuc}")
