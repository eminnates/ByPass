"""
AyLink Bypass — 2 Aşamalı (Heavy/Fast) Mimari

Heavy aşama (token_al):  StealthyFetcher ile sayfa yükle → token çıkar (browser gerekli)
Fast aşama (api_bypass):  httpx ile /get/tk + /links/go2 çağır (browser yok, saf HTTP)
"""
import time
import re
import httpx
from urllib.parse import urlparse
from scrapling.fetchers import StealthyFetcher
from app.logger import get_logger
from app.constants import BypassSentinel

_log = get_logger("aylink")


class AyLinkBypassUltimate:
    def __init__(self, debug_mode=False):
        self.debug_mode = debug_mode
        _log.info(f"AyLink Bypass (Scrapling) hazır. Debug: {debug_mode}")

    def log(self, mesaj):
        _log.info(mesaj)

    # =========================================================================
    # HEAVY AŞAMA — Browser gerektirir (3 worker limit)
    # =========================================================================
    def token_al(self, url):
        """
        StealthyFetcher ile sayfayı yükle ve token'ları çıkar.
        Bu metot browser açar → HEAVY worker'da çalışmalı.
        
        Döndürür:
            dict: {"host", "alias", "_a", "_t", "_d"} — başarılı
            "__NOT_FOUND__" — 404 sayfası
            None — başarısız
        """
        self.log(f"📡 [HEAVY] Sayfa yükleniyor: {url}")
        
        try:
            extra_flags = [
                "--disable-dev-shm-usage",     # Avoids /dev/shm out of memory on small VPS
                "--no-sandbox",                 # Reduces overhead
                "--disable-setuid-sandbox",
                "--single-process",             # Critical for aggressive RAM usage reduction
                "--disable-gpu",                # Redundant but safe
                "--disable-software-rasterizer",
                "--disable-extensions",
                "--mute-audio",
                "--js-flags=--max-old-space-size=128", # Limits V8 JS engine memory
            ]

            page = StealthyFetcher.fetch(
                url,
                headless=True,
                network_idle=True,
                disable_resources=True,    # Drops images, fonts, css, media etc.
                extra_flags=extra_flags
            )

            html = page.html_content
            page_url = page.url
            title = page.css("title::text").get() or ""
            
            self.log(f"✅ Sayfa yüklendi → {page_url}")

            # 404 kontrolü
            if "404 - Link bulunamad" in html or ">Link bulunamad" in html or "404" in title:
                self.log("❌ Link bulunamadı (404).")
                return BypassSentinel.NOT_FOUND

            # Token çıkar
            m = re.search(
                r"_a\s*=\s*'([^']+)',\s*_t\s*=\s*'([^']+)',\s*_d\s*=\s*'([^']+)'",
                html,
            )
            if not m:
                self.log("❌ JS tokenları bulunamadı.")
                return None

            parsed = urlparse(page_url)
            tokens = {
                "host": parsed.netloc,
                "alias": parsed.path.strip("/"),
                "_a": m.group(1),
                "_t": m.group(2),
                "_d": m.group(3),
            }
            self.log(f"🔑 Token'lar çıkarıldı: host={tokens['host']}, alias={tokens['alias']}")
            return tokens

        except Exception as e:
            self.log(f"❌ Token alma hatası: {e}")
            return None

    # =========================================================================
    # FAST AŞAMA — Browser gerektirmez (sınırsız worker)
    # =========================================================================
    @staticmethod
    def api_bypass(tokens):
        """
        Token'larla direkt API çağrısı yaparak final URL'yi alır.
        Browser AÇILMAZ — saf HTTP, çok hızlı.

        Args:
            tokens: {"host", "alias", "_a", "_t", "_d"}
        
        Döndürür:
            str: final URL — başarılı
            None — başarısız
        """
        host = tokens["host"]
        alias = tokens["alias"]

        headers = {
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "X-Requested-With": "XMLHttpRequest",
            "Origin": f"https://{host}",
            "Referer": f"https://{host}/{alias}",
        }

        try:
            with httpx.Client(timeout=10) as client:
                # Adım 1: Session token al
                tk_resp = client.post(
                    f"https://{host}/get/tk",
                    data=f"_a={tokens['_a']}&_t={tokens['_t']}&_d={tokens['_d']}",
                    headers=headers,
                )

                if tk_resp.status_code != 200:
                    _log.warning(f"[FAST] Token isteği başarısız: HTTP {tk_resp.status_code}")
                    return None

                tk_data = tk_resp.json()
                if not tk_data.get("status"):
                    _log.warning(f"[FAST] Token alınamadı: {tk_data}")
                    return None

                tkn = tk_data.get("th") or tk_data.get("token")

                # Adım 2: Final link al
                go2_resp = client.post(
                    f"https://{host}/links/go2",
                    data=f"alias={alias}&tkn={tkn}",
                    headers=headers,
                )

                if go2_resp.status_code != 200:
                    _log.warning(f"[FAST] Go2 isteği başarısız: HTTP {go2_resp.status_code}")
                    return None

                go2_data = go2_resp.json()
                final_url = go2_data.get("url")

                if final_url:
                    # bildirim.vip yönlendirmesi
                    if "bildirim.vip" in final_url:
                        try:
                            redir_resp = client.get(final_url, follow_redirects=True)
                            final_url = str(redir_resp.url)
                        except Exception:
                            pass
                    
                    _log.info(f"[FAST] 🎯 Final URL: {final_url}")
                    return final_url
                else:
                    _log.warning(f"[FAST] URL alınamadı: {go2_data}")
                    return None

        except Exception as e:
            _log.error(f"[FAST] API Bypass hatası: {e}")
            return None

    # =========================================================================
    # COMBO — Geriye uyumluluk (tek çağrıda her iki aşamayı çalıştırır)
    # =========================================================================
    def baslat(self, url):
        """
        Tam bypass: token_al (heavy) + api_bypass (fast).
        engine_wrapper bunu doğrudan çağırabilir, ama ideal olan
        aşamaları ayrı worker'larda çalıştırmaktır.
        """
        self.log(f"🚀 SÜREÇ BAŞLIYOR: {url}")
        start = time.time()

        try:
            # Heavy aşama
            tokens = self.token_al(url)
            
            if tokens == BypassSentinel.NOT_FOUND:
                return BypassSentinel.NOT_FOUND
            if not tokens:
                return None

            # Fast aşama
            final_url = self.api_bypass(tokens)

            if final_url:
                total = time.time() - start
                self.log(f"🎉 BYPASS BAŞARILI! ({total:.1f}s) → {final_url}")
                return final_url
            else:
                self.log("❌ API Bypass başarısız.")
                return None

        except Exception as e:
            self.log(f"❌ KRİTİK HATA: {e}")
            return None

        finally:
            total = time.time() - start
            self.log(f"🏁 Süreç tamamlandı ({total:.1f}s)")


if __name__ == "__main__":
    bot = AyLinkBypassUltimate(debug_mode=True)
    link = "https://ay.link/sarisin"
    print(f"\n🎯 NİHAİ SONUÇ: {bot.baslat(link)}")