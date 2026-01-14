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

class AyLinkBypassUltimate:
    def __init__(self):
        self.log("🖥️ Sanal Ekran (GUI) hazırlanıyor...")
        try:
            self.display = Display(visible=0, size=(1920, 1080))
            self.display.start()
            self.log("✅ Sanal monitör aktif.")
        except Exception as e:
            self.log(f"⚠️ Ekran hatası (Lokaldeysen görmezden gel): {e}")

        self.log("🔧 Tarayıcı GUI Modunda başlatılıyor...")
        self.options = uc.ChromeOptions()
        
        self.options.add_argument('--no-sandbox')
        self.options.add_argument('--disable-dev-shm-usage')
        self.options.add_argument("--mute-audio")
        self.options.add_argument("--disable-popup-blocking")
        self.options.add_argument("--start-maximized")
        self.options.add_argument("--window-size=1920,1080")
        self.options.add_argument("--disable-blink-features=AutomationControlled")
        self.options.page_load_strategy = 'normal'

    def log(self, mesaj):
        zaman = datetime.datetime.now().strftime("%H:%M:%S")
        print(f"[{zaman}] {mesaj}")

    def debug_foto(self, driver, isim):
        try:
            dosya = f"debug_{isim}.png"
            driver.save_screenshot(dosya)
            self.log(f"📸 Durum Fotosu: {dosya}")
        except: pass

    def rastgele_bekle(self, min_s=1, max_s=3):
        time.sleep(random.uniform(min_s, max_s))

    def cloudflare_gec(self, driver):
        """Cloudflare'i sanal fare ile geçer."""
        self.log("🛡️ Cloudflare kontrol ediliyor (GUI Modu)...")
        try:
            # 1. Cloudflare kutusunu bul
            container = WebDriverWait(driver, 5).until(
                EC.visibility_of_element_located((By.CSS_SELECTOR, ".cf-turnstile"))
            )
            
            driver.execute_script("arguments[0].scrollIntoView({block: 'center', inline: 'nearest'});", container)
            time.sleep(1)
            
            # 2. Sol kenara tıkla
            genislik = container.size['width']
            sol_kenar_offset = -(genislik / 2) + 25
            
            action = ActionChains(driver)
            self.log(f"🖱️ Sanal fare ile tıklanıyor (Offset: {sol_kenar_offset})...")
            
            action.move_to_element(container).move_by_offset(sol_kenar_offset, 0).click().perform()
            time.sleep(0.3)
            
            # Klavye desteği
            try: driver.find_element(By.TAG_NAME, "body").click()
            except: pass
            for _ in range(5):
                action.send_keys(Keys.TAB).perform()
                time.sleep(0.1)
                action.send_keys(Keys.SPACE).perform()
            
            self.log("⏳ Doğrulama bekleniyor...")
            time.sleep(5)
            return True
            
        except:
            self.log("✅ Cloudflare kutusu yok (Geçilmiş olabilir).")
            return False

    def reklam_kapat(self, driver, ana_pencere_id, korunacak_pencere_id=None):
        """İstenmeyen reklam sekmelerini kapatır."""
        try:
            handles = driver.window_handles
            if len(handles) > 1:
                for handle in handles:
                    if handle != ana_pencere_id and handle != korunacak_pencere_id:
                        driver.switch_to.window(handle)
                        self.log("   🗑️ Reklam sekmesi kapatılıyor...")
                        driver.close()
                
                # Nereye döneceğini belirle
                if korunacak_pencere_id:
                    driver.switch_to.window(korunacak_pencere_id)
                else:
                    driver.switch_to.window(ana_pencere_id)
        except: 
            driver.switch_to.window(ana_pencere_id)

    def buton_bul_tikla(self, driver):
        """İlk ve İkinci sayfadaki butonları bulup tıklar."""
        seciciler = [
            (By.CSS_SELECTOR, "div.complete a.btn"),
            (By.ID, "btn-main"),
            (By.CSS_SELECTOR, ".btn-go"),
            (By.XPATH, "//a[contains(text(), 'Go to Link')]")
        ]
        
        for tip, secici in seciciler:
            try:
                btn = WebDriverWait(driver, 4).until(EC.element_to_be_clickable((tip, secici)))
                self.log(f"✅ Buton bulundu ({secici}).")
                
                # Önce Cloudflare var mı diye bak (Butonun üstüne binmiş olabilir)
                self.cloudflare_gec(driver)
                
                try:
                    ActionChains(driver).move_to_element(btn).click().perform()
                except:
                    driver.execute_script("arguments[0].click();", btn)
                return True
            except: pass
        return False

    def baslat(self, url):
        self.log(f"🚀 SÜREÇ BAŞLIYOR: {url}")
        driver = uc.Chrome(options=self.options, use_subprocess=True)
        hedef_link = None

        try:
            driver.get(url)
            ana_pencere_id = driver.current_window_handle
            
            self.log("⏳ Site yükleniyor (5sn)...")
            time.sleep(5)
            
            # --- ADIM 1: CLOUDFLARE ---
            self.cloudflare_gec(driver)
            
            # --- ADIM 2: İLK BUTON (REKLAM TETİKLEME) ---
            if not self.buton_bul_tikla(driver):
                self.log("❌ Buton yok. Cloudflare tekrar kontrol ediliyor...")
                self.cloudflare_gec(driver)
                if not self.buton_bul_tikla(driver):
                    self.debug_foto(driver, "buton_bulunamadi")
                    return None

            self.rastgele_bekle(2, 3)
            self.reklam_kapat(driver, ana_pencere_id)
            
            self.log("⏱️ İkinci aşama bekleniyor...")
            time.sleep(2)

            # --- ADIM 3: İKİNCİ BUTON (ARA SAYFAYA GEÇİŞ) ---
            # Butona basmadan önce pencere sayısını al
            pencere_sayisi_once = len(driver.window_handles)
            
            if self.buton_bul_tikla(driver):
                self.log("✌️ 2. Tıklama yapıldı (Ara sayfa için)...")
                
                # Yeni sekme açılmasını bekle
                ara_sayfa_id = None
                for _ in range(10):
                    if len(driver.window_handles) > pencere_sayisi_once:
                        # Son açılan pencere ara sayfadır
                        ara_sayfa_id = driver.window_handles[-1]
                        break
                    time.sleep(1)
                
                if ara_sayfa_id:
                    self.log("✅ Ara sayfaya geçiliyor...")
                    driver.switch_to.window(ara_sayfa_id)
                    time.sleep(3)
                    
                    # Ara sayfada da Cloudflare olabilir
                    self.cloudflare_gec(driver)
                    
                    # --- ADIM 4: PLAY BUTONU (ÇİFT VURUŞ) ---
                    self.log("⏳ Play butonu aranıyor...")
                    try:
                        play_btn = WebDriverWait(driver, 8).until(EC.element_to_be_clickable((By.ID, "btnPlay")))
                        
                        # Vuruş 1: Reklamı aç
                        self.log("▶️ Play (1/2) - Reklam tetikleme...")
                        try: 
                            ActionChains(driver).move_to_element(play_btn).click().perform()
                        except:
                            driver.execute_script("arguments[0].click();", play_btn)
                        time.sleep(2)
                        
                        # Reklamı kapat (Ara sayfayı koru!)
                        # Burası çok önemli: ana_pencere_id VE ara_sayfa_id HARİCİNDEKİLERİ kapat.
                        self.reklam_kapat(driver, ana_pencere_id, korunacak_pencere_id=ara_sayfa_id)
                        
                        # Vuruş 2: Gerçek tıklama
                        self.log("▶️ Play (2/2) - Gerçek tıklama...")
                        try: play_btn = driver.find_element(By.ID, "btnPlay")
                        except: pass # DOM değişmediyse eski elementi kullan
                        
                        driver.execute_script("arguments[0].click();", play_btn)
                        
                        self.log("⏳ Son yönlendirme bekleniyor...")
                        time.sleep(5)
                        
                        # Eğer yeni bir sekme daha açıldıysa (hedef orasıdır)
                        tum_sekmeler = driver.window_handles
                        if len(tum_sekmeler) > 1:
                            driver.switch_to.window(tum_sekmeler[-1])
                        
                        hedef_link = driver.current_url
                        self.log(f"🎉 SONUÇ: {hedef_link}")

                    except Exception as e:
                        self.log(f"⚠️ Play butonu hatası: {e}")
                        # Otomatik yönlenmiş olabilir mi?
                        if "ay.link" not in driver.current_url:
                            hedef_link = driver.current_url
                            self.log(f"🎉 SONUÇ (Otomatik): {hedef_link}")
                else:
                    self.log("⚠️ Yeni sekme açılmadı, ana sayfada kalındı.")

        except Exception as e:
            self.log(f"❌ GENEL HATA: {e}")
            self.debug_foto(driver, "kritik_hata")
        finally:
            self.log("🏁 Tarayıcı kapatılıyor.")
            driver.quit()
            try: self.display.stop()
            except: pass
            
        return hedef_link

if __name__ == "__main__":
    bot = AyLinkBypassUltimate()
    link = "https://ay.link/efsak"
    print(f"\nSonuç: {bot.baslat(link)}")