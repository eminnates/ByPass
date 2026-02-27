"""
Scrapling ile ay.link bypass deneme scripti v3
StealthySession(solve_cloudflare=True) + JS API Bypass
"""
import time
import re
import httpx
from scrapling.fetchers import StealthyFetcher

TEST_URL = "https://ay.live/efsane"

def js_api_bypass_with_httpx(host, _a, _t, _d, alias, cookies):
    """Token'lar ve cookie'lerle direkt API isteği yap."""
    print(f"\n⚡ JS API Bypass deneniyor...")
    
    headers = {
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "X-Requested-With": "XMLHttpRequest",
        "Origin": f"https://{host}",
        "Referer": f"https://{host}/{alias}",
    }
    
    with httpx.Client(timeout=10, cookies=cookies) as client:
        # Adım 1: Token al
        print(f"   [1/2] Token isteniyor: https://{host}/get/tk")
        tk_resp = client.post(
            f"https://{host}/get/tk",
            data=f"_a={_a}&_t={_t}&_d={_d}",
            headers=headers,
        )
        print(f"   Token yanıtı ({tk_resp.status_code}): {tk_resp.text[:200]}")
        
        tk_data = tk_resp.json()
        if not tk_data.get("status"):
            print("   ❌ Token alınamadı")
            return None
        
        tkn = tk_data.get("th") or tk_data.get("token")
        print(f"   ✅ Token alındı: {str(tkn)[:30]}...")
        
        # Adım 2: Final link al
        print(f"   [2/2] Final link isteniyor: https://{host}/links/go2")
        go2_resp = client.post(
            f"https://{host}/links/go2",
            data=f"alias={alias}&tkn={tkn}",
            headers=headers,
        )
        print(f"   Go2 yanıtı ({go2_resp.status_code}): {go2_resp.text[:200]}")
        
        go2_data = go2_resp.json()
        final_url = go2_data.get("url")
        
        if final_url:
            print(f"   🎯 FİNAL URL: {final_url}")
            return final_url
        else:
            print(f"   ❌ URL alınamadı: {go2_data}")
            return None

def test_full_bypass():
    """Tam bypass akışı: Scrapling ile sayfa yükle → tokenları çıkar → API ile bypass."""
    print(f"🚀 Scrapling + JS API Bypass Testi: {TEST_URL}")
    print("=" * 60)
    
    start = time.time()
    
    # --- ADIM 1: Sayfayı yükle ---
    print("📡 StealthyFetcher ile sayfa yükleniyor...")
    page = StealthyFetcher.fetch(
        TEST_URL,
        headless=True,
        network_idle=True,
    )
    
    fetch_time = time.time() - start
    print(f"✅ Sayfa yüklendi ({fetch_time:.1f}s) → {page.url}")
    
    html = page.html_content
    
    # --- ADIM 2: Token'ları çıkar ---
    m1 = re.search(r"_a\s*=\s*'([^']+)',\s*_t\s*=\s*'([^']+)',\s*_d\s*=\s*'([^']+)'", html)
    if not m1:
        print("❌ Token'lar bulunamadı, bypass yapılamaz.")
        return
    
    _a, _t, _d = m1.groups()
    
    # Host ve alias
    from urllib.parse import urlparse
    parsed = urlparse(page.url)
    host = parsed.netloc
    alias = parsed.path.strip("/")
    
    print(f"� host={host}, alias={alias}")
    
    # --- ADIM 3: Cookie'leri al (Turnstile çözülmemişse bile sayfa cookie'leri var) ---
    # Scrapling'den cookie almak zor olabilir, httpx ile direkt deneyelim
    cookies = {}
    
    # --- ADIM 4: JS API Bypass ---
    final = js_api_bypass_with_httpx(host, _a, _t, _d, alias, cookies)
    
    total = time.time() - start
    print(f"\n{'='*60}")
    if final:
        print(f"🎉 BAŞARILI! Final URL: {final}")
    else:
        print(f"❌ Bypass başarısız")
    print(f"⏱️ Toplam süre: {total:.1f}s")

if __name__ == "__main__":
    test_full_bypass()
