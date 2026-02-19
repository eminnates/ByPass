from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from pydantic import BaseModel, field_validator
from urllib.parse import urlparse
from . import models, database
from .logger import get_logger
from .services.engine_wrapper import run_bypass_process
from typing import Optional
from concurrent.futures import ThreadPoolExecutor
import threading

log = get_logger("api")

ALLOWED_DOMAINS = [
    # Selenium bypass (ağır)
    "ay.link",
    "ay.live",
    "ouo.io",
    "ouo.press",
    # Basit redirect (hafif)
    "bit.ly",
    "bit.do",
    "tinyurl.com",
    "t.co",
    "is.gd",
    "v.gd",
    "rb.gy",
    "shorturl.at",
    "shorturl.asia",
    "cutt.ly",
    "tl.tc",
    "s.id",
    "t.ly",
    "tiny.cc",
    "ow.ly",
    "buff.ly",
    "adf.ly",
    "bc.vc",
    "soo.gd",
    "goo.gl",
    "rebrand.ly",
]
# Tabloları oluştur
models.Base.metadata.create_all(bind=database.engine)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- KUYRUK SİSTEMİ (DUAL LANE) ---
# Selenium domainleri (ağır, 30s+)
SELENIUM_DOMAINS = {"ay.link", "ay.live"}

# Fast lane: Redirect ve curl_cffi bypass'lar (hafif, <10sn)
fast_executor = ThreadPoolExecutor(max_workers=20)
# Heavy lane: Selenium bypass'lar (ağır, Chrome gerektirir)
heavy_executor = ThreadPoolExecutor(max_workers=3)

# Kuyruk takibi için thread-safe yapı
_queue_lock = threading.Lock()
_heavy_queue: list[int] = []       # Selenium kuyruğunda bekleyenler
_heavy_active: set[int] = set()    # Selenium aktif işlemler
_fast_active: set[int] = set()     # Redirect aktif işlemler

def _is_heavy(url: str) -> bool:
    """URL'nin Selenium gerektiren bir domain olup olmadığını kontrol eder."""
    from urllib.parse import urlparse
    domain = urlparse(url).netloc.lower().replace("www.", "")
    return domain in SELENIUM_DOMAINS

def _tracked_heavy_bypass(link_id: int, url: str):
    """Selenium bypass — kuyruk takibi ile."""
    with _queue_lock:
        if link_id in _heavy_queue:
            _heavy_queue.remove(link_id)
        _heavy_active.add(link_id)
    
    log.info(f"[HEAVY] İşlem başladı: ID={link_id} | Aktif: {len(_heavy_active)} | Kuyrukta: {len(_heavy_queue)}")
    
    try:
        run_bypass_process(link_id, url)
    finally:
        with _queue_lock:
            _heavy_active.discard(link_id)
        log.info(f"[HEAVY] İşlem bitti: ID={link_id} | Aktif: {len(_heavy_active)} | Kuyrukta: {len(_heavy_queue)}")

def _tracked_fast_bypass(link_id: int, url: str):
    """Redirect bypass — anında işlenir, kuyruk yok."""
    with _queue_lock:
        _fast_active.add(link_id)
    
    log.info(f"[FAST] İşlem başladı: ID={link_id}")
    
    try:
        run_bypass_process(link_id, url)
    finally:
        with _queue_lock:
            _fast_active.discard(link_id)
        log.info(f"[FAST] İşlem bitti: ID={link_id}")

def submit_to_queue(link_id: int, url: str):
    """Domain'e göre fast veya heavy lane'e yönlendirir."""
    if _is_heavy(url):
        with _queue_lock:
            _heavy_queue.append(link_id)
        log.info(f"[HEAVY] Kuyruğa eklendi: ID={link_id} | Sıra: {len(_heavy_queue)}")
        heavy_executor.submit(_tracked_heavy_bypass, link_id, url)
    else:
        log.info(f"[FAST] Anında işleme alındı: ID={link_id}")
        fast_executor.submit(_tracked_fast_bypass, link_id, url)

def get_queue_position(link_id: int) -> Optional[int]:
    """Verilen ID'nin kuyruktaki sırasını döner. Fast lane = her zaman 0."""
    with _queue_lock:
        # Fast lane — her zaman anında işlenir
        if link_id in _fast_active:
            return 0
        # Heavy lane — aktif veya sırada
        if link_id in _heavy_active:
            return 0
        if link_id in _heavy_queue:
            return _heavy_queue.index(link_id) + 1
    return None

def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

class LinkRequest(BaseModel):
    url: str
    webhook_url: Optional[str] = None

    @field_validator('url')
    def validate_url_rules(cls, v: str):
        if not v.startswith("https://"):
            raise ValueError('Güvenlik gereği linkler "https://" ile başlamalıdır.')

        parsed = urlparse(v)
        domain = parsed.netloc.lower()
        
        if domain.startswith("www."):
            domain = domain[4:]

        if domain not in ALLOWED_DOMAINS:
            raise ValueError(f"Bu site desteklenmiyor: {domain}. Sadece şunlar geçerli: {', '.join(ALLOWED_DOMAINS)}")

        return v
    
@app.post("/bypass")
async def bypass_url(req: LinkRequest, db: Session = Depends(get_db)):
    url = req.url.strip()
    
    cached_link = db.query(models.BypassLink).filter(models.BypassLink.original_url == url).first()
    
    if cached_link:
        if cached_link.status == "success":
            return {"status": "success", "resolved_url": cached_link.resolved_url, "safety_status": cached_link.safety_status, "source": "cache"}
        elif cached_link.status == "pending":
            position = get_queue_position(cached_link.id)
            return {"status": "pending", "id": cached_link.id, "queue_position": position, "message": "İşleniyor, lütfen bekleyin."}
        elif cached_link.status == "failed" or cached_link.status == "error":
            log.info(f"Başarısız link tekrar deneniyor: {url}")
            
            cached_link.status = "pending"
            cached_link.safety_status = None
            cached_link.webhook_url = req.webhook_url
            
            db.commit()
            
            submit_to_queue(cached_link.id, url)
            
            return {
                "status": "started", 
                "id": cached_link.id,
                "queue_position": len(_heavy_queue),
                "message": "Önceki işlem başarısızdı, tekrar kuyruğa alındı."
            }
    
    new_record = models.BypassLink(original_url=url, status="pending", webhook_url=req.webhook_url)
    db.add(new_record)
    db.commit()
    db.refresh(new_record)
    
    submit_to_queue(new_record.id, url)
    
    return {
        "status": "started", 
        "id": new_record.id, 
        "queue_position": len(_heavy_queue),
        "message": "İşlem kuyruğa alındı."
    }

@app.get("/status/{id}")
async def get_status(id: int, db: Session = Depends(get_db)):
    record = db.query(models.BypassLink).filter(models.BypassLink.id == id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Link bulunamadı")
    
    position = get_queue_position(id)
    return {
        "status": record.status, 
        "resolved_url": record.resolved_url, 
        "safety_status": record.safety_status,
        "fail_reason": record.fail_reason,
        "queue_position": position
    }

# --- KUYRUK DURUMU ENDPOINTİ ---
@app.get("/queue")
async def get_queue_info():
    with _queue_lock:
        return {
            "fast": {
                "active_count": len(_fast_active),
                "active_ids": list(_fast_active)
            },
            "heavy": {
                "active_count": len(_heavy_active),
                "active_ids": list(_heavy_active),
                "waiting_count": len(_heavy_queue),
                "waiting_ids": list(_heavy_queue)
            }
        }

@app.get("/analysis/{id}")
async def get_analysis(id: int, db: Session = Depends(get_db)):
    record = db.query(models.BypassLink).filter(models.BypassLink.id == id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Link bulunamadı")
    
    return {
        "original_url": record.original_url,
        "resolved_url": record.resolved_url,
        "safety_status": record.safety_status,
        "fail_reason": record.fail_reason,
        "last_scanned_at": record.last_scanned_at
    }