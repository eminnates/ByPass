"""
ByPass Performans Benchmark Scripti v2
=======================================
Yeni mimari: Scrapling (AyLink) + curl_cffi (OUO) + HTTP Redirect

Kullanım:
    python3 benchmark.py                   # Tüm testler
    python3 benchmark.py --api-only        # Sadece API testleri (backend çalışıyor olmalı)
    python3 benchmark.py --engine-only     # Sadece engine testleri (doğrudan)
    python3 benchmark.py --redirect-only   # Sadece redirect testleri
    python3 benchmark.py --url URL         # Belirli bir URL test et

Sonuçlar: benchmark_results/ klasörüne JSON olarak kaydedilir.
"""

import time
import json
import os
import sys
import argparse
import statistics
import threading
import psutil
from datetime import datetime

# --- RENK KODLARI ---
class C:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    CYAN = '\033[96m'
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

class MemMonitor:
    def __init__(self):
        self.process = psutil.Process()
        self.running = True
        self.peak_mb = 0.0
        self.thread = threading.Thread(target=self._monitor, daemon=True)

    def _monitor(self):
        while self.running:
            try:
                mem = self.process.memory_info().rss
                for child in self.process.children(recursive=True):
                    try:
                        mem += child.memory_info().rss
                    except Exception:
                        pass
                mb = mem / (1024 * 1024)
                if mb > self.peak_mb:
                    self.peak_mb = mb
            except Exception:
                pass
            time.sleep(0.05)
            
    def start(self):
        self.thread.start()
        
    def stop(self):
        self.running = False
        self.thread.join(timeout=0.5)
        return self.peak_mb

class Timer:
    def __init__(self, label, track_mem=True):
        self.label = label
        self.track_mem = track_mem
        self.start_perf = None
        self.start_process = None
        self.mem_monitor = None
        
        self.elapsed = 0.0
        self.cpu_time = 0.0
        self.peak_mem = 0.0

    def __enter__(self):
        self.start_perf = time.perf_counter()
        self.start_process = time.process_time()
        if self.track_mem:
            self.mem_monitor = MemMonitor()
            self.mem_monitor.start()
        return self

    def __exit__(self, *args):
        self.elapsed = round(time.perf_counter() - self.start_perf, 3)
        self.cpu_time = round(time.process_time() - self.start_process, 3)
        if self.track_mem and self.mem_monitor:
            self.peak_mem = round(self.mem_monitor.stop(), 1)
# ==========================================
# TEST: Engine Benchmark (Doğrudan motor)
# ==========================================
def test_engine(url):
    sys.path.insert(0, os.path.dirname(__file__))

    sonuc = {
        "test": "engine",
        "url": url,
        "asamalar": {},
        "alt_asamalar": {}, # sub-phases that don't add to sum
        "toplam_sure": 0,
        "durum": "pending",
        "motor": "?"
    }

    # Motor seç
    if "ay.link" in url or "ay.live" in url:
        motor = "AyLink (Scrapling + API)"
        lane = "HEAVY→FAST"


        import scrapling.fetchers.stealth_chrome
        original_enter = scrapling.fetchers.stealth_chrome.StealthySession.__enter__
        original_fetch = scrapling.fetchers.stealth_chrome.StealthySession.fetch
        
        def mock_enter(self):
            t0 = time.perf_counter()
            res = original_enter(self)
            sonuc["alt_asamalar"]["browser_init"] = {"time": round(time.perf_counter() - t0, 3)}
            return res
            
        def mock_fetch(self, target_url, *args, **kwargs):
            t0 = time.perf_counter()
            res = original_fetch(self, target_url, *args, **kwargs)
            sonuc["alt_asamalar"]["page_load_and_wait"] = {"time": round(time.perf_counter() - t0, 3)}
            return res
            
        scrapling.fetchers.stealth_chrome.StealthySession.__enter__ = mock_enter
        scrapling.fetchers.stealth_chrome.StealthySession.fetch = mock_fetch
        
        try:
            with Timer("import", track_mem=False) as t:
                from app.services.aylink_bypass import AyLinkBypassUltimate
            sonuc["asamalar"]["import"] = {"time": t.elapsed, "cpu": t.cpu_time, "mem": t.peak_mem}

            with Timer("init") as t:
                bot = AyLinkBypassUltimate(debug_mode=False)
            sonuc["asamalar"]["init"] = {"time": t.elapsed, "cpu": t.cpu_time, "mem": t.peak_mem}

            # 2 aşamalı test: token_al (HEAVY) + api_bypass (FAST)
            with Timer("token_al [HEAVY]") as t:
                tokens = bot.token_al(url)
            sonuc["asamalar"]["token_al_heavy"] = {"time": t.elapsed, "cpu": t.cpu_time, "mem": t.peak_mem}

            if tokens and tokens != "__NOT_FOUND__":
                with Timer("api_bypass [FAST]") as t:
                    result = bot.api_bypass(tokens)
                sonuc["asamalar"]["api_bypass_fast"] = {"time": t.elapsed, "cpu": t.cpu_time, "mem": t.peak_mem}
            elif tokens == "__NOT_FOUND__":
                result = "__NOT_FOUND__"
            else:
                result = None
        finally:
            scrapling.fetchers.stealth_chrome.StealthySession.__enter__ = original_enter
            scrapling.fetchers.stealth_chrome.StealthySession.fetch = original_fetch

    elif "ouo" in url:
        motor = "OUO (curl_cffi)"
        lane = "FAST"

        with Timer("import") as t:
            from app.services.ouo_bypass import OuoAutoBypass
        sonuc["asamalar"]["import"] = {"time": t.elapsed, "cpu": t.cpu_time, "mem": t.peak_mem}

        with Timer("init") as t:
            bot = OuoAutoBypass(debug_mode=False)
        sonuc["asamalar"]["init"] = {"time": t.elapsed, "cpu": t.cpu_time, "mem": t.peak_mem}

        with Timer("bypass [FAST]") as t:
            result = bot.hedef_linki_bul(url)
        sonuc["asamalar"]["bypass_fast"] = {"time": t.elapsed, "cpu": t.cpu_time, "mem": t.peak_mem}

    elif "tr.link" in url:
        motor = "TRLink (curl_cffi)"
        lane = "FAST"

        with Timer("import") as t:
            from app.services.trlink_bypass import TRLinkBypass
        sonuc["asamalar"]["import"] = {"time": t.elapsed, "cpu": t.cpu_time, "mem": t.peak_mem}

        with Timer("init") as t:
            bot = TRLinkBypass(debug_mode=False)
        sonuc["asamalar"]["init"] = {"time": t.elapsed, "cpu": t.cpu_time, "mem": t.peak_mem}

        with Timer("bypass [FAST]") as t:
            result = bot.hedef_linki_bul(url)
        sonuc["asamalar"]["bypass_fast"] = {"time": t.elapsed, "cpu": t.cpu_time, "mem": t.peak_mem}

    elif "shorte.st" in url or "sh.st" in url or "gestyy.com" in url or "destyy.com" in url:
        motor = "Shorte.st (curl_cffi)"
        lane = "FAST"

        with Timer("import") as t:
            from app.services.shortest_bypass import ShorteStBypass
        sonuc["asamalar"]["import"] = {"time": t.elapsed, "cpu": t.cpu_time, "mem": t.peak_mem}

        with Timer("init") as t:
            bot = ShorteStBypass(debug_mode=False)
        sonuc["asamalar"]["init"] = {"time": t.elapsed, "cpu": t.cpu_time, "mem": t.peak_mem}

        with Timer("bypass [FAST]") as t:
            result = bot.hedef_linki_bul(url)
        sonuc["asamalar"]["bypass_fast"] = {"time": t.elapsed, "cpu": t.cpu_time, "mem": t.peak_mem}

    elif "cuty.io" in url or "cutyion.com" in url or "cutyio.com" in url:
        motor = "Cuty.io (curl_cffi)"
        lane = "FAST"

        with Timer("import") as t:
            from app.services.cutyio_bypass import CutyIoBypass
        sonuc["asamalar"]["import"] = {"time": t.elapsed, "cpu": t.cpu_time, "mem": t.peak_mem}

        with Timer("init") as t:
            bot = CutyIoBypass(debug_mode=False)
        sonuc["asamalar"]["init"] = {"time": t.elapsed, "cpu": t.cpu_time, "mem": t.peak_mem}

        with Timer("bypass [FAST]") as t:
            result = bot.hedef_linki_bul(url)
        sonuc["asamalar"]["bypass_fast"] = {"time": t.elapsed, "cpu": t.cpu_time, "mem": t.peak_mem}

    else:
        # Redirect test
        motor = "Redirect (HTTP)"
        lane = "FAST"

        with Timer("import") as t:
            from app.services.redirect_bypass import resolve
        sonuc["asamalar"]["import"] = {"time": t.elapsed, "cpu": t.cpu_time, "mem": t.peak_mem}

        with Timer("resolve [FAST]") as t:
            result = resolve(url)
        sonuc["asamalar"]["resolve_fast"] = {"time": t.elapsed, "cpu": t.cpu_time, "mem": t.peak_mem}

    sonuc["motor"] = motor
    sonuc["lane"] = lane
    sonuc["toplam_sure"] = round(sum(v["time"] for v in sonuc["asamalar"].values()), 2)

    # Sonuç değerlendirme
    if result and not str(result).startswith("__"):
        sonuc["durum"] = "basarili"
        sonuc["resolved_url"] = result
        durum_icon = renkli('✓', C.GREEN)
        durum_text = renkli(result, C.CYAN)
    elif result == "__NOT_FOUND__":
        sonuc["durum"] = "404"
        durum_icon = renkli('✗', C.YELLOW)
        durum_text = renkli("404 - Link bulunamadı", C.YELLOW)
    elif result == "__TIMEOUT__":
        sonuc["durum"] = "timeout"
        durum_icon = renkli('✗', C.RED)
        durum_text = renkli("Zaman aşımı", C.RED)
    else:
        sonuc["durum"] = "basarisiz"
        durum_icon = renkli('✗', C.RED)
        durum_text = renkli("Başarısız", C.RED)

    # Ekrana yazdır
    print(f"  {renkli(f'[{lane}]', C.BLUE)} {motor}")
    for adim, metrics in sonuc["asamalar"].items():
        if adim == "import" or adim == "init":
            continue
        sure = metrics["time"]
        cpu = metrics["cpu"]
        mem = metrics["mem"]
        bant = "█" * max(1, int(sure))
        
        metrics_str = f"cpu: {cpu:5.2f}s | mem: {mem:5.1f}MB"
        print(f"     {adim:25s} {renkli(f'{sure:6.2f}s', C.YELLOW)} [{renkli(metrics_str, C.CYAN)}] {renkli(bant, C.BLUE)}")

    # Print sub-phases
    for adim, metrics in sonuc.get("alt_asamalar", {}).items():
        sure = metrics["time"]
        bant = "░" * max(1, int(sure))
        print(f"     {renkli('└─ '+adim, C.cyan if hasattr(C, 'cyan') else C.CYAN):25s} {renkli(f'{sure:6.2f}s', C.YELLOW)} {renkli(bant, C.BLUE)}")

    toplam_str = renkli(f'{sonuc["toplam_sure"]:6.2f}s', C.GREEN)
    print(f"     {'TOPLAM':25s} {toplam_str}")
    print(f"  {durum_icon} {durum_text}")

    return sonuc

# ==========================================
# TEST: API Benchmark (Backend çalışmalı)
# ==========================================
def test_api(url, base_url="http://127.0.0.1:8000"):
    import requests

    sonuc = {
        "test": "api",
        "url": url,
        "asamalar": {},
        "toplam_sure": 0,
        "durum": "pending"
    }

    # 1. POST /bypass
    with Timer("POST /bypass") as t:
        try:
            resp = requests.post(f"{base_url}/bypass", json={"url": url}, timeout=10)
            data = resp.json()
        except Exception as e:
            print(f"  {renkli('✗', C.RED)} Backend'e bağlanılamadı: {e}")
            sonuc["durum"] = "baglanti_hatasi"
            return sonuc

    sonuc["asamalar"]["post_bypass"] = {"time": t.elapsed, "cpu": t.cpu_time, "mem": t.peak_mem}
    print(f"  {renkli('→', C.BLUE)} POST /bypass: {renkli(f'{t.elapsed}s', C.YELLOW)}")

    if data.get("status") == "success":
        sonuc["toplam_sure"] = t.elapsed
        sonuc["durum"] = "cache_hit"
        print(f"  {renkli('✓', C.GREEN)} Cache Hit! Toplam: {renkli(f'{t.elapsed}s', C.GREEN)}")
        return sonuc

    link_id = data.get("id")
    queue_pos = data.get("queue_position", "?")
    print(f"  {renkli('→', C.BLUE)} Kuyruk pozisyonu: {queue_pos}")

    # 2. Polling
    poll_start = time.perf_counter()
    poll_count = 0

    while True:
        poll_count += 1
        time.sleep(3)

        resp = requests.get(f"{base_url}/status/{link_id}", timeout=10)
        data = resp.json()
        status = data.get("status")

        if status == "success":
            poll_sure = round(time.perf_counter() - poll_start, 2)
            sonuc["asamalar"]["bypass_isleme"] = {"time": poll_sure, "cpu": 0, "mem": 0}
            sonuc["toplam_sure"] = round(poll_sure + sonuc["asamalar"]["post_bypass"], 2)
            sonuc["durum"] = "basarili"
            sonuc["resolved_url"] = data.get("resolved_url")
            toplam = sonuc["toplam_sure"]
            print(f"  {renkli('✓', C.GREEN)} Başarılı! {renkli(f'{toplam}s', C.GREEN)}")
            print(f"  → {renkli(data.get('resolved_url', '?'), C.CYAN)}")
            break
        elif status in ("failed", "error"):
            poll_sure = round(time.perf_counter() - poll_start, 2)
            sonuc["toplam_sure"] = round(poll_sure + sonuc["asamalar"]["post_bypass"], 2)
            sonuc["durum"] = f"basarisiz ({data.get('fail_reason', '?')})"
            print(f"  {renkli('✗', C.RED)} Başarısız: {data.get('fail_reason', '?')}")
            break
        elif poll_count > 40:
            sonuc["durum"] = "timeout"
            print(f"  {renkli('✗', C.RED)} Benchmark timeout (2dk)")
            break

        sys.stdout.write(f"\r  {renkli('⏳', C.YELLOW)} Polling #{poll_count}...   ")
        sys.stdout.flush()

    return sonuc

# ==========================================
# ÖZET RAPOR
# ==========================================
def rapor_yazdir(sonuclar):
    print(f"\n{renkli('='*70, C.HEADER)}")
    print(f"{renkli('  PERFORMANS RAPORU', C.BOLD)}")
    print(f"{renkli('='*70, C.HEADER)}\n")

    basarili = []
    for s in sonuclar:
        durum = s.get("durum", "?")
        if "basarili" in durum or durum == "cache_hit":
            renk = C.GREEN
            basarili.append(s["toplam_sure"])
        elif durum == "404":
            renk = C.YELLOW
        else:
            renk = C.RED

        motor = s.get("motor", s.get("test", "?"))
        lane = s.get("lane", "")
        sure = s.get("toplam_sure", 0)
        print(f"  {motor:30s} {renkli(f'[{lane}]', C.BLUE):>20s}  {renkli(f'{sure:6.2f}s', C.YELLOW)}  {renkli(durum, renk)}")

    if basarili:
        print(f"\n  {renkli('Başarılı ortalama:', C.BOLD)} {renkli(f'{statistics.mean(basarili):.2f}s', C.GREEN)}")
        print(f"  {renkli('En hızlı:', C.BOLD)}          {renkli(f'{min(basarili):.2f}s', C.GREEN)}")
        print(f"  {renkli('En yavaş:', C.BOLD)}          {renkli(f'{max(basarili):.2f}s', C.YELLOW)}")

# ==========================================
# MAIN
# ==========================================
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="ByPass Performans Benchmark v2")
    parser.add_argument("--api-only", action="store_true", help="Sadece API testleri")
    parser.add_argument("--engine-only", action="store_true", help="Sadece engine testleri")
    parser.add_argument("--redirect-only", action="store_true", help="Sadece redirect testleri")
    parser.add_argument("--url", type=str, help="Belirli bir URL test et")
    args = parser.parse_args()

    # Test URL'leri
    TESTS = {
        # Heavy (browser)
        "aylink":      ("https://ay.live/efsane",          "AyLink"),
        "aylink_404":  ("https://ay.link/bulinkmevcut",    "AyLink 404"),
        # Fast (HTTP)
        "ouo":         ("https://ouo.io/94jkLO",           "OUO"),
        "ouo_404":     ("https://ouo.io/asdfasdf123",      "OUO 404"),
        # Redirect (HTTP)
        "tinyurl":     ("https://tinyurl.com/3mzv5xsn",    "TinyURL"),
        "cutt":        ("https://cutt.ly/test",             "Cutt.ly"),
        # TR Shortener'lar (HTTP - curl_cffi)
        "trlink":      ("https://tr.link/test",             "TRLink"),
        "shortest":    ("https://shorte.st/test",           "Shorte.st"),
        "cutyio":      ("https://cuty.io/test",             "Cuty.io"),
    }

    sonuclar = []

    print(f"\n{renkli('='*70, C.HEADER)}")
    print(f"{renkli('  BYPASS BENCHMARK v2 — Scrapling / curl_cffi / HTTP', C.BOLD)}")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{renkli('='*70, C.HEADER)}")

    if args.url:
        print(f"\n{renkli(f'--- Tek URL Testi ---', C.BOLD)}")
        if args.api_only:
            sonuclar.append(test_api(args.url))
        else:
            sonuclar.append(test_engine(args.url))
    elif args.redirect_only:
        for key in ["tinyurl", "cutt"]:
            url, label = TESTS[key]
            print(f"\n{renkli(f'--- {label} ---', C.BOLD)}")
            sonuclar.append(test_engine(url))
    elif args.engine_only:
        for key in ["aylink", "ouo", "tinyurl", "cutt", "trlink", "shortest", "cutyio"]:
            url, label = TESTS[key]
            print(f"\n{renkli(f'--- {label} ---', C.BOLD)}")
            sonuclar.append(test_engine(url))
    elif args.api_only:
        for key in ["aylink", "ouo", "tinyurl", "trlink", "shortest", "cutyio"]:
            url, label = TESTS[key]
            print(f"\n{renkli(f'--- {label} (API) ---', C.BOLD)}")
            sonuclar.append(test_api(url))
    else:
        # Varsayılan: Tüm engine testleri + 404 testleri
        for key in ["aylink", "aylink_404", "ouo", "ouo_404", "tinyurl", "cutt", "trlink", "shortest", "cutyio"]:
            url, label = TESTS[key]
            print(f"\n{renkli(f'--- {label} ---', C.BOLD)}")
            sonuclar.append(test_engine(url))

    rapor_yazdir(sonuclar)
    kaydet(sonuclar)
