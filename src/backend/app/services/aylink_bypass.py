import undetected_chromedriver as uc
import time
import datetime
import random
import sys
import os
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from pyvirtualdisplay import Display
from app.logger import get_logger

_log = get_logger("aylink")

class AyLinkBypassUltimate:
    def __init__(self, debug_mode=False):
        self.debug_mode = debug_mode
        self.display = None

        _log.info(f"Başlatılıyor... (Debug Modu: {'AÇIK' if debug_mode else 'KAPALI'})")

        if not self.debug_mode:
            _log.info("Sanal Ekran (GUI) hazırlanıyor...")
            try:
                self.display = Display(visible=0, size=(1920, 1080))
                self.display.start()
                _log.info("Sanal monitör aktif (Arka plan modu).")
            except Exception as e:
                _log.warning(f"Ekran hatası: {e}")
        else:
            _log.info("Debug modu açık: Tarayıcı gerçek ekranda açılacak.")

        self.options = uc.ChromeOptions()
        self.options.add_argument('--no-sandbox')
        self.options.add_argument('--disable-dev-shm-usage')
        self.options.add_argument("--mute-audio")
        
        # Bildirim İzni Fix'i
        prefs = {
            "profile.default_content_setting_values.notifications": 1
        }
        self.options.add_experimental_option("prefs", prefs)

        self.options.add_argument("--disable-popup-blocking")
        self.options.add_argument("--start-maximized")
        self.options.add_argument("--window-size=1920,1080")
        self.options.page_load_strategy = 'eager'

    def log(self, mesaj):
        _log.info(mesaj)

    def hata_analiz_kaydet(self, driver, hata_tipi="genel"):
        try:
            klasor = "hata_logs"
            if not os.path.exists(klasor): os.makedirs(klasor)
            zaman = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            dosya_adi = f"{klasor}/{hata_tipi}_{zaman}"
            driver.save_screenshot(f"{dosya_adi}.png")
            with open(f"{dosya_adi}.html", "w", encoding="utf-8") as f:
                f.write(driver.page_source)
            self.log(f"📸 Hata Analizi: {dosya_adi}")
        except: pass

    def rastgele_bekle(self, min_s=1, max_s=3):
        time.sleep(random.uniform(min_s, max_s))

    def sayfa_404_mi(self, driver):
        """Sayfada 404 hatası varsa link geçersizdir."""
        try:
            kaynak = driver.page_source
            if "404 - Link bulunamad" in kaynak or ">Link bulunamad" in kaynak:
                return True
            # Title kontrolü
            baslik = driver.title or ""
            if "404" in baslik:
                return True
        except Exception:
            pass
        return False

    def cloudflare_gec(self, driver):
        self.log("🛡️ Cloudflare kontrol ediliyor...")
        try:
            container = WebDriverWait(driver, 2).until(
                EC.visibility_of_element_located((By.CSS_SELECTOR, ".cf-turnstile"))
            )
            driver.execute_script("arguments[0].scrollIntoView({block: 'center', inline: 'nearest'});", container)
            time.sleep(0.5)
            genislik = container.size['width']
            sol_kenar_offset = -(genislik / 2) + 25
            action = ActionChains(driver)
            action.move_to_element(container).move_by_offset(sol_kenar_offset, 0).click().perform()
            time.sleep(0.3)
            try: driver.find_element(By.TAG_NAME, "body").click()
            except: pass
            if not self.debug_mode:
                for _ in range(5):
                    action.send_keys(Keys.TAB).perform()
                    time.sleep(0.1)
                    action.send_keys(Keys.SPACE).perform()
            self.log("⏳ Doğrulama bekleniyor...")
            time.sleep(2)
            return True
        except:
            self.log("✅ Cloudflare kutusu yok veya geçildi.")
            return False

    def reklam_kapat(self, driver, ana_pencere_id):
        try:
            handles = driver.window_handles
            if len(handles) > 1:
                for handle in handles:
                    if handle != ana_pencere_id:
                        driver.switch_to.window(handle)
                        driver.close()
                driver.switch_to.window(ana_pencere_id)
        except: pass

    def akilli_sekme_filtresi(self, driver):
        """
        Tüm sekmeleri gezer. 'btnPlay', 'btnPermission' veya 'btnDownload' bulursa ID döner.
        """
        self.log("🔍 Tüm sekmelerde Butonlar taranıyor (Play/Allow)...")
        tum_sekmeler = driver.window_handles
        hedef_sekme = None
        bulunan_buton_id = None
        
        olasi_idler = ["btnPlay", "btnPermission", "btnDownload"]

        for handle in tum_sekmeler:
            try:
                driver.switch_to.window(handle)
                for buton_id in olasi_idler:
                    if len(driver.find_elements(By.ID, buton_id)) > 0:
                        self.log(f"✅ HEDEF BULUNDU! Sekme: {handle} | Buton: #{buton_id}")
                        hedef_sekme = handle
                        bulunan_buton_id = buton_id
                        break
                if hedef_sekme: break
            except: pass

        if hedef_sekme:
            for handle in tum_sekmeler:
                if handle != hedef_sekme:
                    try:
                        driver.switch_to.window(handle)
                        driver.close()
                    except: pass
            driver.switch_to.window(hedef_sekme)
            return bulunan_buton_id
        else:
            return None

    def buton_bul_tikla(self, driver):
        seciciler = [
            (By.CSS_SELECTOR, "div.complete a.btn"),
            (By.ID, "btn-main"),
            (By.CSS_SELECTOR, ".btn-go"),
            (By.XPATH, "//a[contains(text(), 'Go to Link')]")
        ]
        # CF kontrolü ONCE yap, her selektör içinde değil
        self.cloudflare_gec(driver)
        
        for tip, secici in seciciler:
            try:
                btn = WebDriverWait(driver, 3).until(EC.element_to_be_clickable((tip, secici)))
                self.log(f"✅ Buton bulundu ({secici}).")
                try: ActionChains(driver).move_to_element(btn).click().perform()
                except: driver.execute_script("arguments[0].click();", btn)
                return True
            except: pass
        return False

    def baslat(self, url):
        self.log(f"🚀 SÜREÇ BAŞLIYOR: {url}")
        driver = uc.Chrome(options=self.options, use_subprocess=True, version_main=143)
        hedef_link = None

        try:
            driver.get(url)
            ana_pencere_id = driver.current_window_handle
            time.sleep(2)

            # --- 404 KONTROLÜ ---
            if self.sayfa_404_mi(driver):
                self.log("Link bulunamadı (404). İşlem iptal ediliyor.")
                return "__NOT_FOUND__"

            self.cloudflare_gec(driver)
            
            # --- SAYFA 1: REKLAM TETİKLEME ---
            if not self.buton_bul_tikla(driver):
                # Buton yoksa tekrar 404 kontrolü yap (yönlendirme olmuş olabilir)
                if self.sayfa_404_mi(driver):
                    self.log("Link bulunamadı (404). İşlem iptal ediliyor.")
                    return "__NOT_FOUND__"
                self.hata_analiz_kaydet(driver, "buton_bulunamadi_1")
                return None

            self.rastgele_bekle(0.5, 1.5)
            self.reklam_kapat(driver, ana_pencere_id)
            time.sleep(1)

            # --- SAYFA 2: ARA SAYFAYA GEÇİŞ (RETRY LOOP) ---
            
            # Bu değişkeni döngü dışında tanımlıyoruz
            bulunan_buton = None
            
            # Ara sayfa geçişini maksimum 3 kez deneyeceğiz
            for deneme in range(1, 4):
                if self.buton_bul_tikla(driver):
                    self.log(f"✌️ Ara sayfaya geçiş tıklaması yapıldı (Deneme {deneme})...")
                    time.sleep(2) # Yeni sayfanın/popup'ın açılması için süre
                    
                    # Buton var mı diye kontrol et
                    bulunan_buton = self.akilli_sekme_filtresi(driver)
                    
                    if bulunan_buton:
                        # Buton bulunduysa döngüden çık, devam et
                        break
                    else:
                        self.log("⚠️ Buton bulunamadı, ana sekmeye dönülüp tekrar denenecek...")
                        
                        # Ana pencereye geri dön
                        try:
                            driver.switch_to.window(ana_pencere_id)
                        except Exception as e:
                            self.log(f"❌ Ana pencereye dönülemedi: {e}")
                            break # Ana pencere yoksa yapacak bir şey yok
                        
                        # Biraz bekle ve tekrar dene
                        time.sleep(1)
                else:
                    self.log("❌ Ara sayfa butonu (Go to Link) bulunamadı.")
                    break

            # -----------------------------------------------
            
            if bulunan_buton:
                self.cloudflare_gec(driver)
                ana_pencere_id = driver.current_window_handle
                
                self.log(f"🥊 '{bulunan_buton}' butonuna ısrarla tıklanacak...")
                
                # --- SON AŞAMA: WHACK-A-MOLE ---
                for deneme in range(1, 7):
                    try:
                        hedef_btn = WebDriverWait(driver, 5).until(
                            EC.element_to_be_clickable((By.ID, bulunan_buton))
                        )
                        
                        self.log(f"▶️ Tıklama Denemesi ({deneme}/6)")
                        try: ActionChains(driver).move_to_element(hedef_btn).click().perform()
                        except: driver.execute_script("arguments[0].click();", hedef_btn)
                        
                        time.sleep(1)
                        self.reklam_kapat(driver, ana_pencere_id)
                        
                        mevcut_url = driver.current_url
                        if "ay.link" not in mevcut_url and "ay.live" not in mevcut_url and "bildirim" not in mevcut_url:
                            self.log("🎉 URL değişti, işlem tamam!")
                            break
                        
                    except Exception as e:
                        self.log(f"✅ Buton kayboldu veya sayfa değişti.")
                        break
                # ------------------------------
                
                self.log("⏳ Son Yönlendirme bekleniyor...")
                time.sleep(2)
                
                if "bildirim" in driver.current_url:
                    self.log("⚠️ Bildirim sayfasındayız, yönlendirme bekleniyor (5sn)...")
                    time.sleep(5)
                
                if len(driver.window_handles) > 1:
                    driver.switch_to.window(driver.window_handles[-1])
                
                hedef_link = driver.current_url
                    
            else:
                self.log("❌ 3 Denemede de geçerli bir buton (Play/Allow) bulunamadı.")
                self.hata_analiz_kaydet(driver, "buton_yok_final")

        except Exception as e:
            self.log(f"❌ KRİTİK HATA: {e}")
            self.hata_analiz_kaydet(driver, "kritik_cokme")
            
        finally:
            self.log("🏁 Kapatılıyor...")
            driver.quit()
            if self.display:
                try: self.display.stop()
                except: pass
            
        return hedef_link

if __name__ == "__main__":
    bot = AyLinkBypassUltimate(debug_mode=True)
    link = "https://ay.link/sarisin" 
    print(f"\n🎯 NİHAİ SONUÇ: {bot.baslat(link)}")