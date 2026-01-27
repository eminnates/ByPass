from fastapi import FastAPI, BackgroundTasks, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from pydantic import BaseModel, field_validator 
from urllib.parse import urlparse 
from pydantic import BaseModel
from . import models, database
from .services.engine_wrapper import run_bypass_process
from typing import Optional

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
        # 1. KURAL: Maske Kontrolü (HTTPS Zorunluluğu)
        # Gelen veri 'https://' ile başlamıyorsa hata ver
        if not v.startswith("https://"):
            raise ValueError('Güvenlik gereği linkler "https://" ile başlamalıdır.')

        try:

            parsed = urlparse(v)
            domain = parsed.netloc.lower()
            
            if domain.startswith("www."):
                domain = domain[4:]

            # Listede var mı?
            if domain not in ALLOWED_DOMAINS:
                raise ValueError(f"Bu site desteklenmiyor: {domain}. Sadece şunlar geçerli: {', '.join(ALLOWED_DOMAINS)}")
        
        except Exception:
            raise ValueError("Geçersiz URL formatı.")


        return v
    
@app.post("/bypass")
async def bypass_url(req: LinkRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    url = req.url.strip()
    
    cached_link = db.query(models.BypassLink).filter(models.BypassLink.original_url == url).first()
    
    if cached_link:
        if cached_link.status == "success":
            return {"status": "success", "resolved_url": cached_link.resolved_url, "safety_status": cached_link.safety_status, "source": "cache"}
        elif cached_link.status == "pending":
            return {"status": "pending", "message": "İşleniyor, lütfen bekleyin."}
        elif cached_link.status == "failed" or cached_link.status == "error":
            print(f"♻️ Retrying failed link: {url}")
            
            cached_link.status = "pending"
            cached_link.safety_status = None
            cached_link.webhook_url = req.webhook_url
            
            db.commit()
            
            background_tasks.add_task(run_bypass_process, cached_link.id, url)
            
            return {
                "status": "started", 
                "id": cached_link.id, 
                "message": "Önceki işlem başarısızdı, tekrar kuyruğa alındı."
            }
    
    new_record = models.BypassLink(original_url=url, status="pending", webhook_url=req.webhook_url)
    db.add(new_record)
    db.commit()
    db.refresh(new_record)
    
    background_tasks.add_task(run_bypass_process, new_record.id, url)
    
    return {"status": "started", "id": new_record.id, "message": "İşlem başlatıldı."}

@app.get("/status/{id}")
async def get_status(id: int, db: Session = Depends(get_db)):
    record = db.query(models.BypassLink).filter(models.BypassLink.id == id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Link bulunamadı")
    return {"status": record.status, "resolved_url": record.resolved_url, "safety_status": record.safety_status}

# --- YENİ EKLENEN ENDPOINT ---
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