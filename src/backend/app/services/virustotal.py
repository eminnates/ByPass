import httpx
import os
import base64
import asyncio
from dotenv import load_dotenv
from app.logger import get_logger

load_dotenv()

log = get_logger("virustotal")

VIRUSTOTAL_API_KEY = os.getenv("VT_API_KEY") 
BASE_URL = "https://www.virustotal.com/api/v3"

async def scan_url_with_virustotal(url: str):
    if not VIRUSTOTAL_API_KEY:
        log.warning("VT_API_KEY bulunamadı! .env dosyasını kontrol et.")
        return "Unknown"

    headers = {"x-apikey": VIRUSTOTAL_API_KEY}
    
    try:
        url_id = base64.urlsafe_b64encode(url.encode()).decode().strip("=")
    except Exception as e:
        log.error(f"URL Encode Hatası: {e}")
        return "Error"

    async with httpx.AsyncClient() as client:
        try:
            # 1. RAPOR KONTROLÜ
            lookup_resp = await client.get(f"{BASE_URL}/urls/{url_id}", headers=headers)
            
            if lookup_resp.status_code == 200:
                stats = lookup_resp.json()["data"]["attributes"]["last_analysis_stats"]
                return parse_vt_stats(stats)
            
            # 2. YENİ TARAMA BAŞLATMA
            log.info(f"VT Raporu yok, yeni tarama başlatılıyor: {url}")
            scan_resp = await client.post(f"{BASE_URL}/urls", data={"url": url}, headers=headers)
            
            if scan_resp.status_code != 200:
                log.error(f"VT Tarama Hatası (Kod: {scan_resp.status_code})")
                log.error(f"VT Cevabı: {scan_resp.text}")
                return "Error"
                
            analysis_id = scan_resp.json()["data"]["id"]
            analysis_url = f"{BASE_URL}/analyses/{analysis_id}"
            
            # 3. SONUCU BEKLEME
            for _ in range(10): 
                await asyncio.sleep(2)
                result = await client.get(analysis_url, headers=headers)
                
                if result.status_code == 200:
                    data = result.json()["data"]["attributes"]
                    if data.get("status") == "completed":
                        return parse_vt_stats(data.get("stats"))
            
            return "Timeout"
            
        except Exception as e:
            log.error(f"VT Kritik Hata: {e}", exc_info=True)
            return "Error"

def parse_vt_stats(stats):
    if not stats: return "Unknown"
    if stats.get("malicious", 0) > 0: return "Malicious"
    elif stats.get("suspicious", 0) > 0: return "Suspicious"
    return "Clean"