import re
import time
import urllib.request
import urllib.parse
from curl_cffi import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from app.logger import get_logger
from app.constants import BypassSentinel, OUO_DOMAINS, extract_domain
from .base_bypass import BaseBypass


class OuoAutoBypass(BaseBypass):
    DOMAINS = OUO_DOMAINS
    SERVICE_NAME = "ouo"
    MAX_DEPTH = 10

    def __init__(self, debug_mode=False):
        super().__init__(debug_mode, extra_headers={
            'accept-language': 'en-GB,en-US;q=0.9,en;q=0.8',
            'referer': 'http://www.google.com/ig/adde?moduleurl=',
        })

    def _recaptcha_v3(self):
        """Google ReCAPTCHA v3 token'ı programatik olarak çözer."""
        try:
            ANCHOR_URL = 'https://www.google.com/recaptcha/api2/anchor?ar=1&k=6Lcr1ncUAAAAAH3cghg6cOTPGARa8adOf-y9zv2x&co=aHR0cHM6Ly9vdW8ucHJlc3M6NDQz&hl=en&v=pCoGBhjs9s8EhFOHJFe8cqis&size=invisible&cb=ahgyd1gkfkhe'
            url_base = 'https://www.google.com/recaptcha/'
            post_data = "v={}&reason=q&c={}&k={}&co={}"

            matches = re.findall(r'([api2|enterprise]+)/anchor\?(.*)', ANCHOR_URL)[0]
            url_base += matches[0] + '/'
            params_str = matches[1]

            anchor_url = url_base + 'anchor?' + params_str
            resp = self.client.get(anchor_url, timeout=5)
            anchor_html = resp.text

            token_match = re.findall(r'"recaptcha-token" value="(.*?)"', anchor_html)
            if not token_match:
                raise Exception("recaptcha-token bulunamadı")
            token = token_match[0]
            params = dict(pair.split('=') for pair in params_str.split('&'))
            post_data = post_data.format(params["v"], token, params["k"], params["co"])

            reload_url = url_base + 'reload?k=' + params["k"]
            resp = self.client.post(reload_url, data=post_data, headers={'content-type': 'application/x-www-form-urlencoded'}, timeout=5)
            reload_html = resp.text

            answer_match = re.findall(r'"rresp","(.*?)"', reload_html)
            if not answer_match:
                raise Exception("rresp bulunamadı")
            return answer_match[0]
        except Exception as e:
            self._log.error(f"ReCAPTCHA çözme hatası: {e}")
            raise e

    def _bypass_single(self, url):
        """Tek bir ouo linkini bypass eder."""
        # ouo.press kullan (Cloudflare daha yumuşak)
        work_url = url.replace("ouo.io", "ouo.press")
        p = urlparse(work_url)
        id_val = work_url.split('/')[-1]
        next_url = f"{p.scheme}://{p.hostname}/go/{id_val}"

        self._log.info(f"İstek atılıyor: {work_url}")
        res = self.client.get(work_url, impersonate="chrome124", timeout=10)

        # 404 Kontrolü
        if res.status_code == 404 or "ouo.io/js/404.js" in res.text or "LINK NOT FOUND" in res.text:
            return BypassSentinel.NOT_FOUND
            
        if res.status_code != 200:
            self._log.warning(f"HTTP {res.status_code} alındı.")
            return None

        has_form = '<form' in res.text.lower()
        if not has_form:
            self._log.warning("Form bulunamadı (Cloudflare engeli olabilir).")
            return None

        current_res = res
        for step in range(2):
            if current_res.headers.get('Location'):
                return current_res.headers.get('Location')

            soup = BeautifulSoup(current_res.content, 'lxml')
            form = soup.find('form')
            if not form:
                self._log.warning(f"Adım {step+1}: Form yok.")
                return None

            inputs = form.find_all("input", {"name": re.compile(r"token$")})
            data = {inp.get('name'): inp.get('value') for inp in inputs}
            
            try:
                data['x-token'] = self._recaptcha_v3()
            except Exception:
                return None

            h = {'content-type': 'application/x-www-form-urlencoded'}
            current_res = self.client.post(next_url, data=data, headers=h,
                                         allow_redirects=False, impersonate="chrome124", timeout=10)
            
            # Sonraki adım URL'si
            next_url = f"{p.scheme}://{p.hostname}/xreallcygo/{id_val}"

        return current_res.headers.get('Location')

    def hedef_linki_bul(self, url):
        """OUO özel: chain tracking ile zincirleme bypass."""
        self._log.info(f"🚀 SÜREÇ BAŞLATILIYOR (curl_cffi): {url}")
        
        current_url = url
        chain = [url]
        start_time = time.time()

        for depth in range(1, self.MAX_DEPTH + 1):
            self._log.info(f"🔗 [{depth}] Bypass deneniyor: {current_url}")
            
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

            chain.append(result)
            self._log.info(f"✅ Adım sonucu: {result}")

            if self.is_own_domain(result):
                self._log.info("🔄 Sonuç yine ouo! Tekrar bypass ediliyor...")
                current_url = result
            else:
                total_time = time.time() - start_time
                self._log.info(f"🎯 FİNAL ULAŞILDI: {result} ({total_time:.2f}s)")
                return result

        self._log.warning("⚠️ Max derinliğe ulaşıldı.")
        return chain[-1]

if __name__ == "__main__":
    bot = OuoAutoBypass(debug_mode=True)
    link = "https://ouo.io/94jkLO" 
    sonuc = bot.hedef_linki_bul(link)
    print(f"Sonuç: {sonuc}")