from fastapi import FastAPI, BackgroundTasks, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from . import models, database
from .services.engine_wrapper import run_bypass_process
from typing import Optional

# Tabloları oluştur
models.Base.metadata.create_all(bind=database.engine)

app = FastAPI()

# Dependency
def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

class LinkRequest(BaseModel):
    url: str
    webhook_url: Optional[str] = None

@app.post("/bypass")
async def bypass_url(req: LinkRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    url = req.url.strip()
    
    # 1. ADIM: HIZLI KONTROL (Cache Check)
    cached_link = db.query(models.BypassLink).filter(models.BypassLink.original_url == url).first()
    
    if cached_link:
        if cached_link.status == "success":
            return {"status": "success", "resolved_url": cached_link.resolved_url, "source": "cache"}
        elif cached_link.status == "pending":
            return {"status": "pending", "message": "İşleniyor, lütfen bekleyin."}
    
    # 2. ADIM: YOKSA YENİ KAYIT AÇ VE İŞLEMİ BAŞLAT
    new_record = models.BypassLink(original_url=url, status="pending", webhook_url=req.webhook_url)
    db.add(new_record)
    db.commit()
    db.refresh(new_record)
    
    # İşlemi arka plana at (Kullanıcıyı bekletme)
    background_tasks.add_task(run_bypass_process, new_record.id, url)
    
    return {"status": "started", "id": new_record.id, "message": "İşlem başlatıldı."}

@app.get("/status/{id}")
async def get_status(id: int, db: Session = Depends(get_db)):
    record = db.query(models.BypassLink).filter(models.BypassLink.id == id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Link bulunamadı")
    return {"status": record.status, "resolved_url": record.resolved_url}