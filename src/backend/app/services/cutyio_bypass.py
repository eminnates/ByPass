"""
Cuty.io Bypass — curl_cffi ile Reklamlı Kısaltıcı Bypass

cuty.io (cutyion.com) timer + form submit yapısı kullanan bir kısaltıcı.
Mekanizma: GET → HTML parse → Form/token çıkar → POST → Final URL al
"""

import re
import base64
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup
from app.constants import BypassSentinel, CUTYIO_DOMAINS
from .base_bypass import BaseBypass


class CutyIoBypass(BaseBypass):
    DOMAINS = CUTYIO_DOMAINS
    SERVICE_NAME = "cutyio"

    def _bypass_single(self, url):
        """Tek bir cuty.io linkini bypass eder."""
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
            page_url = str(res.url)

            # 404 içerik kontrolü
            if "not found" in html.lower() and "404" in html:
                return BypassSentinel.NOT_FOUND

            # JS'den doğrudan URL çıkarmayı dene
            js_patterns = [
                r'var\s+url\s*=\s*["\']([^"\']+)["\']',
                r'var\s+destination\s*=\s*["\']([^"\']+)["\']',
                r'var\s+redirect\s*=\s*["\']([^"\']+)["\']',
                r'window\.location\.href\s*=\s*["\']([^"\']+)["\']',
                r'window\.location\.replace\s*\(\s*["\']([^"\']+)["\']\s*\)',
                r'"url"\s*:\s*"([^"]+)"',
                r'"redirect"\s*:\s*"([^"]+)"',
                r'"destination"\s*:\s*"([^"]+)"',
            ]

            for pattern in js_patterns:
                matches = re.findall(pattern, html, re.IGNORECASE)
                for match in matches:
                    if match.startswith("http") and not self.is_own_domain(match):
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

                if not data:
                    continue

                if action:
                    form_url = action if action.startswith('http') else urljoin(page_url, action)
                else:
                    form_url = page_url

                headers = {
                    'content-type': 'application/x-www-form-urlencoded',
                    'referer': page_url,
                    'origin': f"https://{urlparse(page_url).netloc}",
                }

                self._log.info(f"Form submit: {form_url} | data: {list(data.keys())}")

                if method == 'post':
                    form_res = self.client.post(
                        form_url, data=data, headers=headers,
                        allow_redirects=False, impersonate="chrome124", timeout=30
                    )
                else:
                    form_res = self.client.get(
                        form_url, params=data,
                        allow_redirects=False, impersonate="chrome124", timeout=30
                    )

                # Redirect kontrolü
                location = form_res.headers.get('Location')
                if location:
                    if not self.is_own_domain(location):
                        self._log.info(f"Form redirect: {location}")
                        return location
                    else:
                        self._log.info(f"Ara redirect: {location}")
                        next_res = self.client.get(
                            location, impersonate="chrome124", timeout=30
                        )
                        html = next_res.text

                        for pattern in js_patterns:
                            matches = re.findall(pattern, html, re.IGNORECASE)
                            for match in matches:
                                if match.startswith("http") and not self.is_own_domain(match):
                                    return match

                # Form sonuç sayfasından URL çıkar
                if form_res.status_code == 200:
                    result_html = form_res.text
                    for pattern in js_patterns:
                        matches = re.findall(pattern, result_html, re.IGNORECASE)
                        for match in matches:
                            if match.startswith("http") and not self.is_own_domain(match):
                                return match

            # Meta refresh kontrolü
            meta_refresh = soup.find('meta', attrs={'http-equiv': re.compile(r'refresh', re.I)})
            if meta_refresh:
                content = meta_refresh.get('content', '')
                match = re.search(r'url=([^\s;"\']+)', content, re.IGNORECASE)
                if match and not self.is_own_domain(match.group(1)):
                    self._log.info(f"Meta refresh URL: {match.group(1)}")
                    return match.group(1)

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
    bot = CutyIoBypass(debug_mode=True)
    link = "https://cuty.io/test"
    sonuc = bot.hedef_linki_bul(link)
    print(f"Sonuç: {sonuc}")
