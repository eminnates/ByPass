"""
ByPass API — FastAPI Endpoints

Tüm HTTP endpoint'leri burada tanımlı.
Kuyruk yönetimi queue_manager modülünde merkezileştirilmiştir.
"""

from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from pydantic import BaseModel, field_validator
from urllib.parse import urlparse
from typing import Optional

from . import models, database
from .constants import LinkStatus, ALLOWED_DOMAINS, is_heavy
from .logger import get_logger
from .queue_manager import submit_to_queue, get_queue_position, get_queue_info, get_heavy_queue_length, shutdown as shutdown_executors

log = get_logger("api")

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


@app.on_event("shutdown")
def on_shutdown():
    """Graceful shutdown — aktif işlemleri tamamla."""
    log.info("Uygulama kapatılıyor, executor'lar bekleniyor...")
    shutdown_executors()


# =========================================================================
# PYDANTIC MODELLER
# =========================================================================
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
            raise ValueError(f"Bu site desteklenmiyor: {domain}.")

        return v


# =========================================================================
# ENDPOINTS
# =========================================================================
@app.post("/bypass")
async def bypass_url(req: LinkRequest, db: Session = Depends(get_db)):
    url = req.url.strip()

    cached_link = db.query(models.BypassLink).filter(models.BypassLink.original_url == url).first()

    if cached_link:
        if cached_link.status == LinkStatus.SUCCESS:
            return {"status": LinkStatus.SUCCESS, "resolved_url": cached_link.resolved_url, "safety_status": cached_link.safety_status, "source": "cache"}
        elif cached_link.status == LinkStatus.PENDING:
            position = get_queue_position(cached_link.id)
            return {"status": LinkStatus.PENDING, "id": cached_link.id, "queue_position": position, "message": "İşleniyor, lütfen bekleyin."}
        elif cached_link.status in (LinkStatus.FAILED, LinkStatus.ERROR):
            log.info(f"Başarısız link tekrar deneniyor: {url}")

            cached_link.status = LinkStatus.PENDING
            cached_link.safety_status = None
            cached_link.webhook_url = req.webhook_url
            db.commit()

            submit_to_queue(cached_link.id, url)

            return {
                "status": "started",
                "id": cached_link.id,
                "queue_position": get_heavy_queue_length() if is_heavy(url) else 0,
                "message": "Tekrar kuyruğa alındı.",
            }

    new_record = models.BypassLink(original_url=url, status=LinkStatus.PENDING, webhook_url=req.webhook_url)
    db.add(new_record)
    db.commit()
    db.refresh(new_record)

    submit_to_queue(new_record.id, url)

    return {
        "status": "started",
        "id": new_record.id,
        "queue_position": get_heavy_queue_length() if is_heavy(url) else 0,
        "message": "İşlem kuyruğa alındı.",
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
        "queue_position": position,
    }


@app.get("/queue")
async def queue_info():
    return get_queue_info()


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
        "last_scanned_at": record.last_scanned_at,
    }


@app.get("/health")
async def health_check():
    """VPS monitoring için basit health check."""
    queue = get_queue_info()
    return {
        "status": "ok",
        "heavy_active": queue["heavy"]["active_count"],
        "heavy_waiting": queue["heavy"]["waiting_count"],
        "fast_active": queue["fast"]["active_count"],
    }