from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from pydantic import BaseModel, field_validator
from urllib.parse import urlparse
from . import models, database
from .services.engine_wrapper import run_bypass_process
from typing import Optional
from concurrent.futures import ThreadPoolExecutor
import threading

ALLOWED_DOMAINS = [
    "ay.link",
    "ay.live",
    "ouo.io",
    "ouo.press",
    "tl.tc"
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

# --- KUYRUK SİSTEMİ ---
# max_workers=1 → Aynı anda sadece 1 Chrome tarayıcı çalışır
# Diğer istekler sırada bekler
bypass_executor = ThreadPoolExecutor(max_workers=1)

# Kuyruk takibi için thread-safe yapı
_queue_lock = threading.Lock()
_queue_list: list[int] = []        # Sırada bekleyen ID'ler
_active_id: Optional[int] = None   # Şu an işlenen ID

def _tracked_bypass(link_id: int, url: str):
    """Kuyruk takibi ile bypass işlemini çalıştırır."""
    global _active_id
    
    # Sıradan çıkar, aktif olarak işaretle
    with _queue_lock:
        if link_id in _queue_list:
            _queue_list.remove(link_id)
        _active_id = link_id
    
    print(f"🚀 İşlem başladı: ID={link_id} | Kuyrukta bekleyen: {len(_queue_list)}")
    
    try:
        run_bypass_process(link_id, url)
    finally:
        with _queue_lock:
            _active_id = None
        print(f"✅ İşlem bitti: ID={link_id} | Kuyrukta bekleyen: {len(_queue_list)}")

def submit_to_queue(link_id: int, url: str):
    """İşlemi kuyruğa ekler."""
    with _queue_lock:
        _queue_list.append(link_id)
    
    print(f"📥 Kuyruğa eklendi: ID={link_id} | Sıra: {len(_queue_list)}")
    bypass_executor.submit(_tracked_bypass, link_id, url)

def get_queue_position(link_id: int) -> Optional[int]:
    """Verilen ID'nin kuyruktaki sırasını döner (1-indexed). Bulunamazsa None."""
    with _queue_lock:
        if _active_id == link_id:
            return 0  # 0 = şu an işleniyor
        if link_id in _queue_list:
            return _queue_list.index(link_id) + 1
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
            print(f"♻️ Retrying failed link: {url}")
            
            cached_link.status = "pending"
            cached_link.safety_status = None
            cached_link.webhook_url = req.webhook_url
            
            db.commit()
            
            submit_to_queue(cached_link.id, url)
            
            return {
                "status": "started", 
                "id": cached_link.id,
                "queue_position": len(_queue_list),
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
        "queue_position": len(_queue_list),
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
        "queue_position": position
    }

# --- KUYRUK DURUMU ENDPOINTİ ---
@app.get("/queue")
async def get_queue_info():
    with _queue_lock:
        return {
            "active_id": _active_id,
            "waiting_count": len(_queue_list),
            "waiting_ids": list(_queue_list)
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
        "last_scanned_at": record.last_scanned_at
    }