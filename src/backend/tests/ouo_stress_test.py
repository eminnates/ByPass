"""
OUO 3x Eşzamanlı Stres Testi
3 OUO bypass'ı aynı anda çalıştırır, RAM'i 2 saniyede bir ölçer.
"""
import threading
import psutil
import time
import sys
import os

# Backend modüllerini import edebilmek için path ekle
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "app"))
os.chdir(os.path.dirname(__file__))

from app.services.ouo_bypass import OuoAutoBypass

TEST_URL = "https://ouo.io/ays39a"  # Test linki
NUM_WORKERS = 3
MONITOR_INTERVAL = 2  # saniye

# Sonuç takibi
results = {}
peak_ram = {"value": 0}
monitoring = {"active": True}


def ram_monitor():
    """Her 2 saniyede RAM durumunu yazdırır."""
    start_time = time.time()
    baseline = psutil.virtual_memory().used / (1024**2)
    
    while monitoring["active"]:
        mem = psutil.virtual_memory()
        used = mem.used / (1024**2)
        avail = mem.available / (1024**2)
        delta = used - baseline
        elapsed = time.time() - start_time
        
        if used > peak_ram["value"]:
            peak_ram["value"] = used
        
        # Chrome process'leri say
        chrome_count = 0
        chrome_rss = 0
        for proc in psutil.process_iter(['name', 'memory_info']):
            try:
                if 'chrome' in proc.info['name'].lower():
                    chrome_count += 1
                    chrome_rss += proc.info['memory_info'].rss / (1024**2)
            except (psutil.NoSuchProcess, psutil.AccessDenied, AttributeError):
                pass
        
        print(
            f"[{elapsed:5.0f}s] "
            f"RAM: {used:.0f}MB (+{delta:.0f}MB) | "
            f"Boş: {avail:.0f}MB | "
            f"Chrome: {chrome_count} proc / {chrome_rss:.0f}MB",
            flush=True
        )
        time.sleep(MONITOR_INTERVAL)


def run_ouo(worker_id, url):
    """Tek bir OUO bypass çalıştırır."""
    print(f"[Worker-{worker_id}] Başlıyor: {url}", flush=True)
    start = time.time()
    
    try:
        bot = OuoAutoBypass(debug_mode=False)
        result = bot.hedef_linki_bul(url)
        elapsed = time.time() - start
        results[worker_id] = {
            "status": "success" if result and not result.startswith("__") else "failed",
            "result": result,
            "time": elapsed,
        }
        print(f"[Worker-{worker_id}] Bitti: {result} ({elapsed:.1f}s)", flush=True)
    except Exception as e:
        elapsed = time.time() - start
        results[worker_id] = {"status": "error", "result": str(e), "time": elapsed}
        print(f"[Worker-{worker_id}] HATA: {e} ({elapsed:.1f}s)", flush=True)


def main():
    print("=" * 65, flush=True)
    print("  OUO 3x EŞZAMANLI STRES TESTİ", flush=True)
    print("=" * 65, flush=True)
    
    mem_before = psutil.virtual_memory()
    baseline_used = mem_before.used / (1024**2)
    baseline_avail = mem_before.available / (1024**2)
    
    print(f"\nBAŞLANGIÇ: {baseline_used:.0f}MB kullanım / {baseline_avail:.0f}MB boş", flush=True)
    print(f"TEST: {NUM_WORKERS}x OUO bypass eşzamanlı", flush=True)
    print(f"URL: {TEST_URL}\n", flush=True)
    
    # RAM monitörünü başlat
    monitor_thread = threading.Thread(target=ram_monitor, daemon=True)
    monitor_thread.start()
    
    # 3 OUO worker'ı başlat
    workers = []
    for i in range(1, NUM_WORKERS + 1):
        t = threading.Thread(target=run_ouo, args=(i, TEST_URL))
        workers.append(t)
        t.start()
        time.sleep(0.5)  # Hafif stagger — hepsinin aynı anda driver indirmesini engelle
    
    # Hepsinin bitmesini bekle
    for t in workers:
        t.join(timeout=180)
    
    # Monitoring durdur
    monitoring["active"] = False
    time.sleep(0.5)
    
    # Sonuçlar
    mem_after = psutil.virtual_memory()
    
    print(f"\n{'=' * 65}", flush=True)
    print("  SONUÇLAR", flush=True)
    print(f"{'=' * 65}", flush=True)
    
    for wid, res in sorted(results.items()):
        print(f"  Worker-{wid}: {res['status']} | {res['time']:.1f}s | {res['result']}", flush=True)
    
    total_delta = peak_ram["value"] - baseline_used
    
    print(f"\n  Peak RAM kullanımı:     {peak_ram['value']:.0f} MB", flush=True)
    print(f"  RAM artışı (delta):    +{total_delta:.0f} MB", flush=True)
    print(f"  Sonrası boş RAM:       {mem_after.available/(1024**2):.0f} MB", flush=True)
    
    # VPS simülasyonu
    print(f"\n{'─' * 40}", flush=True)
    print("  VPS 2GB SİMÜLASYONU", flush=True)
    print(f"{'─' * 40}", flush=True)
    vps_base = 530  # OS(400) + FastAPI(100) + Nginx(30)
    vps_chrome = total_delta  # Gerçek Chrome artışı
    vps_total = vps_base + vps_chrome
    
    print(f"  OS + FastAPI + Nginx:   {vps_base} MB", flush=True)
    print(f"  3x Chrome (gerçek):    +{vps_chrome:.0f} MB", flush=True)
    print(f"  TOPLAM:                 {vps_total:.0f} MB / 2048 MB", flush=True)
    
    if vps_total > 2048:
        fazla = vps_total - 2048
        print(f"\n  ⚠️  {fazla:.0f}MB FAZLA — 1GB swap gerekli!", flush=True)
    else:
        kalan = 2048 - vps_total
        print(f"\n  ✅ YETERLİ! {kalan:.0f}MB buffer var.", flush=True)
    
    print(f"\n{'=' * 65}", flush=True)
    print("  TEST BİTTİ", flush=True)
    print(f"{'=' * 65}\n", flush=True)


if __name__ == "__main__":
    main()
