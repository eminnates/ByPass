import time
from playwright.sync_api import sync_playwright
from app.constants import BypassSentinel, OUO_DOMAINS
from .base_bypass import BaseBypass


class OuoAutoBypass(BaseBypass):
    DOMAINS = OUO_DOMAINS
    SERVICE_NAME = "ouo"
    MAX_DEPTH = 6
    NAV_TIMEOUT_MS = 15000
    STEP_TIMEOUT_SEC = 16
    POLL_INTERVAL_MS = 120
    CLICK_TIMEOUT_MS = 220

    def __init__(self, debug_mode=False):
        # We still call super to initialize things, even if we don't use self.client directly
        super().__init__(debug_mode, skip_session=True)
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None

    def _start_browser(self):
        if not self.playwright:
            self.playwright = sync_playwright().start()
            extra_flags = [
                "--disable-dev-shm-usage",
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--single-process",
                "--disable-gpu",
                "--disable-software-rasterizer",
                "--disable-extensions",
                "--mute-audio",
                "--disable-background-networking",
                "--disable-background-timer-throttling",
                "--disable-breakpad",
                "--disable-component-update",
                "--disable-default-apps",
                "--disable-features=Translate,BackForwardCache,OptimizationHints,MediaRouter,DialMediaRouteProvider",
                "--disable-hang-monitor",
                "--disable-popup-blocking",
                "--disable-renderer-backgrounding",
                "--disable-sync",
                "--metrics-recording-only",
                "--no-first-run",
                "--no-default-browser-check",
                "--renderer-process-limit=1",
                "--disable-site-isolation-trials",
                "--blink-settings=imagesEnabled=false",
                "--js-flags=--max-old-space-size=96",
            ]
            self.browser = self.playwright.chromium.launch(headless=True, args=extra_flags)
            self.context = self.browser.new_context(
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
                viewport={"width": 360, "height": 640},
                device_scale_factor=1,
                reduced_motion="reduce",
                color_scheme="light",
                service_workers="block",
            )

    def _get_page(self):
        if self.page and not self.page.is_closed():
            return self.page

        self.page = self.context.new_page()

        # Gereksiz kaynakları yüklemeyi reddederek hızı artırıyoruz
        def route_intercept(route):
            if route.request.resource_type in ["image", "stylesheet", "media", "font"]:
                route.abort()
            else:
                route.continue_()

        self.page.route("**/*", route_intercept)
        return self.page

    def _stop_browser(self):
        if self.page:
            try:
                self.page.close()
            except Exception:
                pass
            self.page = None
        if self.context:
            self.context.close()
            self.context = None
        if self.browser:
            self.browser.close()
            self.browser = None
        if self.playwright:
            self.playwright.stop()
            self.playwright = None

    def _bypass_single(self, url):
        """Tek bir ouo linkini bypass eder (Playwright ile)."""
        self._start_browser()
        work_url = url.replace("ouo.io", "ouo.press")
        self._log.info(f"İstek atılıyor (Playwright): {work_url}")

        page = self._get_page()
        
        try:
            # domcontentloaded kullanarak tüm elementleri beklemeyip süreci hızlandırıyoruz
            page.goto(work_url, wait_until="commit", timeout=self.NAV_TIMEOUT_MS)
            
            # Check for 404
            title = page.title()
            if "404" in title:
                return BypassSentinel.NOT_FOUND
            try:
                if page.locator("text=LINK NOT FOUND").first.is_visible(timeout=1200):
                    return BypassSentinel.NOT_FOUND
            except Exception:
                pass
            
            # Adım 1 & 2 için genel bekleme ve tıklama döngüsü
            start_time = time.monotonic()
            while time.monotonic() - start_time < self.STEP_TIMEOUT_SEC:
                # Buton varsa tıkla
                try:
                    page.evaluate('document.querySelector("button#btn-main") && document.querySelector("button#btn-main").click()')
                except Exception:
                    pass
                
                # Sayfa ouo dışında bir yere gittiyse, başardık demektir
                if "ouo.press" not in page.url and "ouo.io" not in page.url:
                    final_url = page.url
                    return final_url
                    
                # Ouo domaninde kalıyorsak, kısa bir mola verip tekrar dene
                # Navigasyonlar sayfa yenilenmesine sebep olur ve döngü devam eder.
                try:
                    page.wait_for_timeout(self.POLL_INTERVAL_MS)
                except Exception:
                    pass
            
            # Süre dolduysa heavy kuyruğu gereksiz meşgul etmemek için timeout sentinel döndür
            return BypassSentinel.TIMEOUT

        except Exception as e:
            self._log.error(f"Playwright hatası: {e}")
            return None

    def hedef_linki_bul(self, url: str, close_browser_after: bool = True):
        """OUO özel: chain tracking ile zincirleme bypass."""
        self._log.info(f"🚀 SÜREÇ BAŞLATILIYOR: {url}")
        current_url = url
        chain = [url]
        start_time = time.monotonic()

        try:
            for depth in range(1, self.MAX_DEPTH + 1):
                self._log.info(f"🔗 [{depth}] Bypass deneniyor: {current_url}")
                try:
                    result = self._bypass_single(current_url)
                except Exception as e:
                    self._log.error(f"Bypass sırasında hata: {e}")
                    return None

                if result is BypassSentinel.NOT_FOUND:
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
                    elapsed = time.monotonic() - start_time
                    self._log.info(f"🎯 FİNAL ULAŞILDI: {result} ({elapsed:.2f}s)")
                    return result

            self._log.warning("⚠️ Max derinliğe ulaşıldı.")
            return chain[-1]

        finally:
            if close_browser_after:   # ← Singleton kullanımında False geçilir
                self._stop_browser()

if __name__ == "__main__":
    bot = OuoAutoBypass(debug_mode=True)
    link = "https://ouo.io/94jkLO" 
    sonuc = bot.hedef_linki_bul(link)
    print(f"Sonuç: {sonuc}")