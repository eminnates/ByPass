import undetected_chromedriver as uc
import time
import datetime
import os # Eklendi
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from pyvirtualdisplay import Display

class OuoAutoBypass:
    def __init__(self, debug_mode=False): # Debug modu eklendi
        self.debug_mode = debug_mode
        self.display = None

        self.log(f"🔧 Başlatılıyor... (Debug Modu: {'AÇIK ✅' if debug_mode else 'KAPALI ❌'})")

        if not self.debug_mode:
            self.log("🖥️ Sanal ekran (Xvfb) başlatılıyor...")
            try:
                self.display = Display(visible=0, size=(1920, 1080))
                self.display.start()
                self.log("✅ Sanal monitör aktif.")
            except Exception as e:
                self.log(f"⚠️ Ekran hatası: {e}")
        else:
            self.log("👀 Debug modu açık: Tarayıcı gerçek ekranda açılacak.")

        self.options = uc.ChromeOptions()
        
        self.options.add_argument('--no-sandbox')
        self.options.add_argument('--disable-dev-shm-usage')
        self.options.add_argument("--mute-audio")
        self.options.add_argument("--disable-popup-blocking")
        self.options.add_argument("--start-maximized")
        self.options.add_argument("--window-size=1920,1080") # Çözünürlük sabitlendi
        self.options.add_argument("--disable-blink-features=AutomationControlled")
        self.options.add_argument("--password-store=basic")
        self.options.page_load_strategy = 'eager' 
        
        self.log("✅ Tarayıcı konfigürasyonu tamam.")

    def log(self, mesaj):
        zaman = datetime.datetime.now().strftime("%H:%M:%S")
        print(f"[{zaman}] {mesaj}")

    # --- YENİ EKLENEN FONKSİYON ---
    def hata_analiz_kaydet(self, driver, hata_tipi="genel"):
        """Hata anında ekran görüntüsü ve HTML kaynağını kaydeder."""
        try:
            klasor = "hata_logs"
            if not os.path.exists(klasor): os.makedirs(klasor)
            zaman = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            dosya_adi = f"{klasor}/OUO_{hata_tipi}_{zaman}" # OUO öneki eklendi
            
            # 1. Ekran Görüntüsü
            driver.save_screenshot(f"{dosya_adi}.png")
            
            # 2. HTML Kaynağı
            with open(f"{dosya_adi}.html", "w", encoding="utf-8") as f:
                f.write(driver.page_source)
                
            self.log(f"📸 Hata Analizi Kaydedildi: {dosya_adi}")
        except Exception as e:
            self.log(f"⚠️ Hata analizi kaydedilemedi: {e}")
    # ------------------------------

    def insan_taklidi_yap(self, driver):
        try:
            body = driver.find_element(By.TAG_NAME, 'body')
            action = ActionChains(driver)
            action.move_to_element(body).move_by_offset(10, 20).perform()
        except:
            pass

    def guvenli_ve_hizli_temizlik(self, driver, ana_pencere_id):
        try:
            tum_pencereler = driver.window_handles
            if len(tum_pencereler) <= 1:
                return driver.current_window_handle

            self.log(f"🧹 Temizlik: {len(tum_pencereler)} pencere kontrol ediliyor...")
            driver.set_page_load_timeout(5)
            yeni_ana_pencere = ana_pencere_id
            to_close = [] 

            for handle in tum_pencereler:
                if handle == ana_pencere_id: continue 

                try:
                    driver.switch_to.window(handle)
                    mevcut_url = driver.current_url
                    
                    if "ouo" in mevcut_url:
                        yeni_ana_pencere = handle 
                    elif "google.com/recaptcha" in mevcut_url:
                         pass # Koru
                    else:
                        to_close.append(handle)
                except:
                    to_close.append(handle)

            for handle in to_close:
                if handle != yeni_ana_pencere:
                    try:
                        driver.switch_to.window(handle)
                        driver.close()
                    except: pass
            
            driver.set_page_load_timeout(30)
            
            if yeni_ana_pencere in driver.window_handles:
                driver.switch_to.window(yeni_ana_pencere)
                return yeni_ana_pencere
            else:
                driver.switch_to.window(driver.window_handles[0])
                return driver.window_handles[0]

        except Exception as e:
            self.log(f"⚠️ Temizlik hatası: {e}")
            try:
                if len(driver.window_handles) > 0:
                    driver.switch_to.window(driver.window_handles[0])
                    return driver.window_handles[0]
            except: pass
            return ana_pencere_id

    def hedef_linki_bul(self, baslangic_url):
        self.log(f"🚀 SÜREÇ BAŞLATILIYOR: {baslangic_url}")
        
        driver = uc.Chrome(options=self.options, use_subprocess=True, version_main=143)
        bulunan_link = None
        
        try:
            driver.get(baslangic_url)
            self.log("Sayfaya gidildi.")
            start_time = time.time()
            max_sure = 120 

            ana_pencere_id = driver.current_window_handle

            while True:
                if time.time() - start_time > max_sure:
                    self.log("❌ ZAMAN AŞIMI!")
                    self.hata_analiz_kaydet(driver, "zaman_asimi") # GÜNCELLENDİ
                    break

                try:
                    current_url = driver.current_url
                except Exception as e:
                    if "invalid session" in str(e).lower():
                        self.log("❌ Oturum kapandı.")
                        break
                    time.sleep(1)
                    continue

                # --- 1. HEDEF KONTROLÜ ---
                if "ouo" not in current_url and "about:blank" not in current_url and "google.com" not in current_url:
                    bulunan_link = current_url
                    self.log(f"✅ HEDEF BULUNDU: {current_url}")
                    break

                if "Method Not Allowed" in driver.page_source:
                    driver.refresh()
                    time.sleep(3)
                    continue

                # --- 2. GO SAYFASI ---
                if "/go/" in current_url:
                    self.log("📍 Durum: '/go/' sayfasındayız.")
                    try:
                        try:
                            timer_element = driver.find_element(By.ID, "timer")
                            loop_count = 0
                            while timer_element.text != "0":
                                loop_count += 1
                                if loop_count > 10: break
                                self.log(f"      ...Bekleniyor: {timer_element.text}")
                                self.insan_taklidi_yap(driver)
                                time.sleep(1)
                        except:
                            self.log("⚠️ Timer yok veya 0.")

                        self.log("🖱️ Buton aranıyor...")
                        btn = WebDriverWait(driver, 10).until(
                             EC.element_to_be_clickable((By.ID, "btn-main"))
                        )
                        
                        self.log("🖱️ Butona tıklandı!")
                        try: btn.click()
                        except: driver.execute_script("arguments[0].click();", btn)
                        
                        time.sleep(2)
                        ana_pencere_id = self.guvenli_ve_hizli_temizlik(driver, ana_pencere_id)
                        time.sleep(2)
                        continue 

                    except Exception as e:
                        self.log(f"❌ Go Sayfası Hatası: {e}")
                        self.hata_analiz_kaydet(driver, "go_sayfasi_hata") # EKLENDİ
                        try: driver.execute_script("document.getElementById('form-go').submit();")
                        except: pass
                        time.sleep(2)

                # --- 3. İLK SAYFA ---
                else:
                    try:
                        self.log("📍 Durum: Aşama 1 (Ben robot değilim).")
                        
                        try:
                            cf_iframe = driver.find_element(By.XPATH, "//iframe[starts-with(@src, 'https://challenges.cloudflare.com')]")
                            if cf_iframe:
                                self.log("⚠️ CF Turnstile algılandı.")
                                self.insan_taklidi_yap(driver)
                                time.sleep(2)
                        except: pass

                        btn = WebDriverWait(driver, 10).until(
                            EC.presence_of_element_located((By.ID, "btn-main"))
                        )
                        self.log("✅ Buton bulundu.")

                        # Reklam iframelerini sil
                        driver.execute_script("""
                            var iframes = document.querySelectorAll('iframe');
                            iframes.forEach(function(iframe) {
                                if (iframe.id.includes('container') || window.getComputedStyle(iframe).zIndex > 1000) {
                                    iframe.remove();
                                }
                            });
                        """)
                        
                        self.log("🖱️ Tıklanıyor...")
                        actions = ActionChains(driver)
                        actions.move_to_element(btn).click().perform()
                        
                        self.log("⏳ Popup bekleniyor...")
                        time.sleep(2) 
                        
                        ana_pencere_id = self.guvenli_ve_hizli_temizlik(driver, ana_pencere_id)
                        time.sleep(2)

                    except Exception as e:
                        self.log(f"⚠️ Aşama 1 Hatası: {e}")
                        self.hata_analiz_kaydet(driver, "asama_1_hata") # EKLENDİ
                        time.sleep(2)

        except Exception as e:
            self.log(f"❌ KRİTİK HATA: {e}")
            self.hata_analiz_kaydet(driver, "kritik_cokme") # GÜNCELLENDİ
        finally:
            self.log("🏁 Tarayıcı kapatılıyor.")
            try: driver.quit()
            except: pass
            
            try:
                if self.display:
                    self.display.stop()
                    self.log("🛑 Sanal ekran kapatıldı.")
            except: pass
            
        return bulunan_link

if __name__ == "__main__":
    # Test için debug modunu açabilirsin (True)
    bot = OuoAutoBypass(debug_mode=True)
    link = "https://ouo.io/94jkLO" 
    sonuc = bot.hedef_linki_bul(link)
    
    print("\n" + "="*40)
    print(f"🎯 SONUÇ: {sonuc}")
    print("="*40 + "\n")