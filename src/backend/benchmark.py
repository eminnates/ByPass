"""
ByPass Performans Benchmark Scripti
====================================
Kullanım:
    python3 benchmark.py                   # Tüm testler
    python3 benchmark.py --api-only        # Sadece API testleri (backend çalışıyor olmalı)
    python3 benchmark.py --engine-only     # Sadece engine testleri (doğrudan Selenium)
    python3 benchmark.py --url URL         # Belirli bir URL test et

Sonuçlar: benchmark_results/ klasörüne JSON olarak kaydedilir.
"""

import time
import json
import os
import sys
import argparse
import statistics
from datetime import datetime

# --- RENK KODLARI ---
class C:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    END = '\033[0m'
    BOLD = '\033[1m'

def renkli(msg, renk):
    return f"{renk}{msg}{C.END}"

# --- SONUÇ KAYIT ---
RESULTS_DIR = "benchmark_results"
os.makedirs(RESULTS_DIR, exist_ok=True)

def kaydet(sonuclar):
    dosya = f"{RESULTS_DIR}/benchmark_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(dosya, "w", encoding="utf-8") as f:
        json.dump(sonuclar, f, indent=2, ensure_ascii=False, default=str)
    print(f"\n{renkli('📁 Sonuçlar kaydedildi:', C.GREEN)} {dosya}")

# --- ZAMANLAYICI ---
class Timer:
    def __init__(self, label):
        self.label = label
        self.start = None
        self.elapsed = None

    def __enter__(self):
        self.start = time.perf_counter()
        return self

    def __exit__(self, *args):
        self.elapsed = round(time.perf_counter() - self.start, 2)

# ==========================================
# TEST 1: API Benchmark (Backend çalışmalı)
# ==========================================
def test_api(url, base_url="http://127.0.0.1:8000"):
    import requests

    sonuc = {
        "test": "api_benchmark",
        "url": url,
        "asamalar": {},
        "toplam_sure": 0,
        "durum": "pending"
    }

    print(f"\n{renkli('='*60, C.HEADER)}")
    print(f"{renkli('  API BENCHMARK', C.BOLD)}")
    print(f"  URL: {url}")
    print(f"{renkli('='*60, C.HEADER)}\n")

    # 1. POST /bypass
    with Timer("POST /bypass") as t:
        try:
            resp = requests.post(f"{base_url}/bypass", json={"url": url}, timeout=10)
            data = resp.json()
        except Exception as e:
            print(f"{renkli('✗', C.RED)} Backend'e bağlanılamadı: {e}")
            sonuc["durum"] = "baglanti_hatasi"
            return sonuc

    sonuc["asamalar"]["post_bypass"] = t.elapsed
    print(f"  {renkli('→', C.BLUE)} POST /bypass: {renkli(f'{t.elapsed}s', C.YELLOW)}")

    if data.get("status") == "success":
        # Cache'den geldi
        sonuc["toplam_sure"] = t.elapsed
        sonuc["durum"] = "cache_hit"
        sonuc["kaynak"] = "cache"
        print(f"  {renkli('✓', C.GREEN)} Cache Hit! Toplam: {renkli(f'{t.elapsed}s', C.GREEN)}")
        return sonuc

    link_id = data.get("id")
    queue_pos = data.get("queue_position", "?")
    print(f"  {renkli('→', C.BLUE)} Kuyruk pozisyonu: {queue_pos}")

    # 2. Polling (/status)
    poll_start = time.perf_counter()
    poll_count = 0
    ilk_isleme_suresi = None

    while True:
        poll_count += 1
        time.sleep(3)

        with Timer(f"GET /status/{link_id}") as t:
            resp = requests.get(f"{base_url}/status/{link_id}", timeout=10)
            data = resp.json()

        current_pos = data.get("queue_position")
        status = data.get("status")

        # İlk kez işlenmeye başladı mı?
        if current_pos == 0 and ilk_isleme_suresi is None:
            ilk_isleme_suresi = round(time.perf_counter() - poll_start, 2)
            sonuc["asamalar"]["kuyruk_bekleme"] = ilk_isleme_suresi
            print(f"  {renkli('→', C.BLUE)} Kuyruk bekleme: {renkli(f'{ilk_isleme_suresi}s', C.YELLOW)}")

        if status == "success":
            poll_sure = round(time.perf_counter() - poll_start, 2)
            sonuc["asamalar"]["bypass_isleme"] = poll_sure
            sonuc["toplam_sure"] = round(poll_sure + sonuc["asamalar"]["post_bypass"], 2)
            sonuc["durum"] = "basarili"
            sonuc["poll_sayisi"] = poll_count
            sonuc["resolved_url"] = data.get("resolved_url")
            sonuc["safety_status"] = data.get("safety_status")
            print(f"  {renkli('✓', C.GREEN)} Başarılı! İşleme: {renkli(f'{poll_sure}s', C.YELLOW)}")
            break

        elif status in ("failed", "error"):
            poll_sure = round(time.perf_counter() - poll_start, 2)
            sonuc["asamalar"]["bypass_isleme"] = poll_sure
            sonuc["toplam_sure"] = round(poll_sure + sonuc["asamalar"]["post_bypass"], 2)
            sonuc["durum"] = f"basarisiz ({data.get('fail_reason', 'unknown')})"
            sonuc["fail_reason"] = data.get("fail_reason")
            print(f"  {renkli('✗', C.RED)} Başarısız: {data.get('fail_reason', '?')} ({poll_sure}s)")
            break

        elif poll_count > 60:  # 3 dakika max
            sonuc["durum"] = "timeout"
            sonuc["toplam_sure"] = round(time.perf_counter() - poll_start, 2)
            print(f"  {renkli('✗', C.RED)} Benchmark timeout (3dk)")
            break

        # İlerleme göster
        pos_str = f"sıra:{current_pos}" if current_pos else "işleniyor"
        sys.stdout.write(f"\r  {renkli('⏳', C.YELLOW)} Polling #{poll_count} ({pos_str})...   ")
        sys.stdout.flush()

    return sonuc

# ==========================================
# TEST 2: Engine Benchmark (Doğrudan Selenium)
# ==========================================
def test_engine(url):
    sys.path.insert(0, os.path.dirname(__file__))

    sonuc = {
        "test": "engine_benchmark",
        "url": url,
        "asamalar": {},
        "toplam_sure": 0,
        "durum": "pending"
    }

    print(f"\n{renkli('='*60, C.HEADER)}")
    print(f"{renkli('  ENGINE BENCHMARK (Doğrudan Selenium)', C.BOLD)}")
    print(f"  URL: {url}")
    print(f"{renkli('='*60, C.HEADER)}\n")

    # Hangi bot?
    if "ay.link" in url or "ay.live" in url:
        bot_adi = "AyLink"
        with Timer("Bot import") as t:
            from app.services.aylink_bypass import AyLinkBypassUltimate
        sonuc["asamalar"]["import"] = t.elapsed

        with Timer("Bot init") as t:
            bot = AyLinkBypassUltimate(debug_mode=False)
        sonuc["asamalar"]["init"] = t.elapsed
        print(f"  {renkli('→', C.BLUE)} Chrome başlatma: {renkli(f'{t.elapsed}s', C.YELLOW)}")

        with Timer("Bypass") as t:
            result = bot.baslat(url)
        sonuc["asamalar"]["bypass"] = t.elapsed

    elif "ouo" in url:
        bot_adi = "OUO"
        with Timer("Bot import") as t:
            from app.services.ouo_bypass import OuoAutoBypass
        sonuc["asamalar"]["import"] = t.elapsed

        with Timer("Bot init") as t:
            bot = OuoAutoBypass(debug_mode=False)
        sonuc["asamalar"]["init"] = t.elapsed
        print(f"  {renkli('→', C.BLUE)} Chrome başlatma: {renkli(f'{t.elapsed}s', C.YELLOW)}")

        with Timer("Bypass") as t:
            result = bot.hedef_linki_bul(url)
        sonuc["asamalar"]["bypass"] = t.elapsed

    else:
        print(f"  {renkli('✗', C.RED)} Desteklenmeyen URL")
        sonuc["durum"] = "desteklenmiyor"
        return sonuc

    sonuc["toplam_sure"] = round(sum(sonuc["asamalar"].values()), 2)
    sonuc["bot"] = bot_adi

    if result and not result.startswith("__"):
        sonuc["durum"] = "basarili"
        sonuc["resolved_url"] = result
        print(f"  {renkli('✓', C.GREEN)} Sonuç: {result}")
    elif result == "__NOT_FOUND__":
        sonuc["durum"] = "404"
        print(f"  {renkli('✗', C.RED)} 404 - Link bulunamadı")
    elif result == "__TIMEOUT__":
        sonuc["durum"] = "timeout"
        print(f"  {renkli('✗', C.RED)} Zaman aşımı")
    else:
        sonuc["durum"] = "basarisiz"
        print(f"  {renkli('✗', C.RED)} Başarısız")

    print(f"\n  {renkli('⏱  SÜRE DAĞILIMI:', C.BOLD)}")
    for adim, sure in sonuc["asamalar"].items():
        bant = "█" * int(sure)
        print(f"     {adim:20s} {renkli(f'{sure:6.2f}s', C.YELLOW)} {renkli(bant, C.BLUE)}")
    toplam = sonuc["toplam_sure"]
    print(f"     {'TOPLAM':20s} {renkli(f'{toplam:6.2f}s', C.GREEN)}")

    return sonuc

# ==========================================
# TEST 3: Cache Performansı
# ==========================================
def test_cache(url, base_url="http://127.0.0.1:8000"):
    import requests

    print(f"\n{renkli('='*60, C.HEADER)}")
    print(f"{renkli('  CACHE BENCHMARK', C.BOLD)}")
    print(f"{renkli('='*60, C.HEADER)}\n")

    sureler = []
    for i in range(5):
        with Timer(f"Cache #{i+1}") as t:
            resp = requests.post(f"{base_url}/bypass", json={"url": url}, timeout=10)
            data = resp.json()
        sureler.append(t.elapsed)
        kaynak = "CACHE" if data.get("source") == "cache" else "YENİ"
        print(f"  #{i+1} → {renkli(f'{t.elapsed}s', C.YELLOW)} ({kaynak})")

    # Cache olan süreleri filtrele
    if len(sureler) > 1:
        cache_sureleri = sureler[1:]  # İlki yeni olabilir
        print(f"\n  Ortalama cache: {renkli(f'{statistics.mean(cache_sureleri):.3f}s', C.GREEN)}")
        print(f"  Min/Max: {min(cache_sureleri):.3f}s / {max(cache_sureleri):.3f}s")

    return {"test": "cache_benchmark", "sureler": sureler}

# ==========================================
# ÖZET RAPOR
# ==========================================
def rapor_yazdir(sonuclar):
    print(f"\n{renkli('='*60, C.HEADER)}")
    print(f"{renkli('  PERFORMANS RAPORU', C.BOLD)}")
    print(f"{renkli('='*60, C.HEADER)}\n")

    for s in sonuclar:
        durum_renk = C.GREEN if "basarili" in s.get("durum", "") or s.get("durum") == "cache_hit" else C.RED
        sure_val = s.get("toplam_sure", 0)
        print(f"  {s['test']:25s} | {renkli(f'{sure_val:6.2f}s', C.YELLOW)} | {renkli(s.get('durum', '?'), durum_renk)}")

    toplam_sureler = [s["toplam_sure"] for s in sonuclar if s.get("toplam_sure", 0) > 0]
    if toplam_sureler:
        print(f"\n  Ortalama: {renkli(f'{statistics.mean(toplam_sureler):.2f}s', C.GREEN)}")

# ==========================================
# MAIN
# ==========================================
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="ByPass Performans Benchmark")
    parser.add_argument("--api-only", action="store_true", help="Sadece API testleri")
    parser.add_argument("--engine-only", action="store_true", help="Sadece engine testleri")
    parser.add_argument("--cache-only", action="store_true", help="Sadece cache testi")
    parser.add_argument("--url", type=str, help="Test edilecek URL")
    args = parser.parse_args()

    # Varsayılan test URL'leri
    TEST_URLS = {
        "aylink": "https://ay.link/sarisin",
        "ouo": "https://ouo.io/94jkLO",
        "aylink_404": "https://ay.link/bulinkmevcut",
        "ouo_404": "https://ouo.io/asdfasdf123",
    }

    sonuclar = []

    if args.url:
        # Tek URL testi
        if args.engine_only:
            sonuclar.append(test_engine(args.url))
        else:
            sonuclar.append(test_api(args.url))
    elif args.cache_only:
        # Cache test (önce çözülmüş bir URL lazım)
        test_url = list(TEST_URLS.values())[0]
        sonuclar.append(test_cache(test_url))
    elif args.api_only:
        for isim, url in TEST_URLS.items():
            print(f"\n{renkli(f'--- Test: {isim} ---', C.BOLD)}")
            sonuclar.append(test_api(url))
    elif args.engine_only:
        # Sadece gerçek URL'ler (404 olmayanlar)
        for isim in ["aylink", "ouo"]:
            print(f"\n{renkli(f'--- Test: {isim} ---', C.BOLD)}")
            sonuclar.append(test_engine(TEST_URLS[isim]))
    else:
        # Varsayılan: 404 testleri (hızlı) + 1 API testi
        print(renkli("\n  404 Algılama Hız Testi\n", C.BOLD))
        for isim in ["aylink_404", "ouo_404"]:
            sonuclar.append(test_engine(TEST_URLS[isim]))

        print(renkli("\n  API Testi (Cache)\n", C.BOLD))
        sonuclar.append(test_api(TEST_URLS["aylink"]))

    rapor_yazdir(sonuclar)
    kaydet(sonuclar)
