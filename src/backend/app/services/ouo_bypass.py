import undetected_chromedriver as uc
import time
import datetime
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from pyvirtualdisplay import Display

class OuoAutoBypass:
    def __init__(self):
        self.log("🖥️ Sanal ekran (Xvfb) başlatılıyor...")
        self.display = Display(visible=0, size=(1920, 1080))
        self.display.start()

        self.log("🌐 Tarayıcı ayarları yapılıyor...")
        self.options = uc.ChromeOptions()
        
        self.options.add_argument('--no-sandbox')
        self.options.add_argument('--disable-dev-shm-usage')
        self.options.add_argument("--mute-audio")
        self.options.add_argument("--disable-popup-blocking")
        self.options.add_argument("--start-maximized")
        self.options.add_argument("--disable-blink-features=AutomationControlled")
        self.options.add_argument("--password-store=basic")
        self.options.page_load_strategy = 'eager' 
        
        self.log("✅ Tarayıcı konfigürasyonu tamam.")

    def log(self, mesaj):
        zaman = datetime.datetime.now().strftime("%H:%M:%S")
        print(f"[{zaman}] {mesaj}")

    def screenshot_al(self, driver, isim):
        try:
            dosya_adi = f"debug_{isim}.png"
            driver.save_screenshot(dosya_adi)
            self.log(f"📸 EKRAN GÖRÜNTÜSÜ KAYDEDİLDİ: {dosya_adi}")
        except Exception as e:
            self.log(f"⚠️ Screenshot alınamadı: {e}")

    def insan_taklidi_yap(self, driver):
        try:
            body = driver.find_element(By.TAG_NAME, 'body')
            action = ActionChains(driver)
            action.move_to_element(body).move_by_offset(10, 20).perform()
        except:
            pass

    def guvenli_ve_hizli_temizlik(self, driver, ana_pencere_id):
        """
        Sekmeleri kapatırken oturumu çökertmemek için güvenli temizlik yapar.
        Asla tek kalan sekmeyi veya ana sekmeyi kapatmaz.
        """
        try:
            tum_pencereler = driver.window_handles
            
            # Eğer sadece 1 pencere varsa işlem yapma (kapatırsak session ölür)
            if len(tum_pencereler) <= 1:
                return driver.current_window_handle

            self.log(f"🧹 [Hibrit Temizlik] {len(tum_pencereler)} pencere kontrol ediliyor...")
            
            driver.set_page_load_timeout(5)
            yeni_ana_pencere = ana_pencere_id
            
            to_close = [] # Kapatılacakların listesi

            for handle in tum_pencereler:
                # Ana pencereyi şimdilik es geç
                if handle == ana_pencere_id:
                    continue 

                try:
                    driver.switch_to.window(handle)
                    mevcut_url = driver.current_url
                    
                    if "ouo" in mevcut_url:
                        self.log(f"   ✅ Yeni 'ouo' sekmesi bulundu, korunuyor.")
                        yeni_ana_pencere = handle 
                    elif "google.com/recaptcha" in mevcut_url:
                         self.log("   ✅ Captcha penceresi korunuyor.")
                    else:
                        self.log(f"   🗑️ Reklam tespit edildi ({handle})...")
                        to_close.append(handle)
                        
                except Exception:
                    self.log("   🗑️ Yanıt vermeyen sayfa, kapatılacak.")
                    to_close.append(handle)

            # Şimdi listelenenleri kapat
            for handle in to_close:
                # Yeni ana pencereyi yanlışlıkla kapatma
                if handle != yeni_ana_pencere:
                    try:
                        driver.switch_to.window(handle)
                        driver.close()
                    except:
                        pass
            
            driver.set_page_load_timeout(30)
            
            # Güvenli pencereye geçiş yap
            if yeni_ana_pencere in driver.window_handles:
                driver.switch_to.window(yeni_ana_pencere)
                return yeni_ana_pencere
            else:
                # Eğer o da yoksa, kalan ilk pencereye geç
                driver.switch_to.window(driver.window_handles[0])
                return driver.window_handles[0]

        except Exception as e:
            self.log(f"⚠️ Temizlik hatası: {e}")
            driver.set_page_load_timeout(30)
            try:
                if len(driver.window_handles) > 0:
                    driver.switch_to.window(driver.window_handles[0])
                    return driver.window_handles[0]
            except: 
                pass
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
                # --- ZAMAN AŞIMI ---
                if time.time() - start_time > max_sure:
                    self.log("❌ ZAMAN AŞIMI!")
                    self.screenshot_al(driver, "timeout_error")
                    break

                try:
                    current_url = driver.current_url
                except Exception as e:
                    # GİRİNTİ DÜZELTİLDİ: Hata yakalama bloğu
                    if "invalid session" in str(e).lower():
                        self.log("❌ Tarayıcı oturumu kapandı/çöktü. İşlem sonlandırılıyor.")
                        break
                    
                    self.log("⚠️ URL okunamadı, bekleniyor...")
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

                # ============================================================
                #    AŞAMA 2: GO SAYFASI
                # ============================================================
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
                        try:
                            btn.click()
                        except:
                            driver.execute_script("arguments[0].click();", btn)
                        
                        time.sleep(2)
                        ana_pencere_id = self.guvenli_ve_hizli_temizlik(driver, ana_pencere_id)
                        
                        time.sleep(2)
                        continue 

                    except Exception as e:
                        self.log(f"❌ Go Sayfası Hatası: {e}")
                        try:
                            driver.execute_script("document.getElementById('form-go').submit();")
                        except: pass
                        time.sleep(2)

                # ============================================================
                #    AŞAMA 1: İLK SAYFA
                # ============================================================
                else:
                    try:
                        self.log("📍 Durum: Aşama 1 (Ben robot değilim).")
                        
                        try:
                            cf_iframe = driver.find_element(By.XPATH, "//iframe[starts-with(@src, 'https://challenges.cloudflare.com')]")
                            if cf_iframe:
                                self.log("⚠️ Cloudflare Turnstile algılandı! Çözülmeye çalışılıyor...")
                                self.insan_taklidi_yap(driver)
                                time.sleep(2)
                        except:
                            pass

                        btn = WebDriverWait(driver, 10).until(
                            EC.presence_of_element_located((By.ID, "btn-main"))
                        )
                        self.log("✅ Buton bulundu.")

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
                        time.sleep(2)

        except Exception as e:
            self.log(f"❌ KRİTİK HATA: {e}")
            self.screenshot_al(driver, "critical_crash")
        finally:
            self.log("🏁 Tarayıcı kapatılıyor.")
            try:
                driver.quit()
            except: pass
            
            try:
                self.display.stop()
                self.log("🛑 Sanal ekran kapatıldı.")
            except: pass
            
        return bulunan_link

if __name__ == "__main__":
    bot = OuoAutoBypass()
    link = "https://ouo.io/94jkLO" 
    sonuc = bot.hedef_linki_bul(link)
    
    print("\n" + "="*40)
    print(f"🎯 SONUÇ: {sonuc}")
    print("="*40 + "\n")