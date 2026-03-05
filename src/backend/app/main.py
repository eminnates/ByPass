"""
ByPass API — FastAPI Endpoints

Tüm HTTP endpoint'leri burada tanımlı.
Kuyruk yönetimi queue_manager modülünde merkezileştirilmiştir.
Güvenlik: API key auth + rate limiting + SSRF koruması.
"""

import os
from dotenv import load_dotenv
from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel, field_validator
from urllib.parse import urlparse
from typing import Optional

load_dotenv()

from . import models, database
from .constants import LinkStatus, ALLOWED_DOMAINS, is_heavy
from .logger import get_logger
from .auth import require_api_key
from .security import validate_webhook_url
from .queue_manager import submit_to_queue, get_queue_position, get_queue_info, get_heavy_queue_length, shutdown as shutdown_executors

log = get_logger("api")

# Tabloları oluştur (ApiKey tablosu dahil)
models.Base.metadata.create_all(bind=database.engine)

app = FastAPI(
    title="ByPass API",
    description="Kısaltılmış URL bypass servisi. API key gerektirir.",
    version="1.0.0",
)

# =========================================================================
# CORS — API key güvenliği ana kapı, CORS kısıtlaması gereksiz.
# Ticari API standardı: tüm origin'lere izin ver (Stripe, OpenAI gibi).
# =========================================================================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,  # wildcard ile credentials=True uyumsuz
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "X-API-Key", "Accept"],
)


@app.on_event("shutdown")
def on_shutdown():
    """Graceful shutdown — aktif işlemleri tamamla."""
    log.info("Uygulama kapatılıyor, executor'lar bekleniyor...")
    shutdown_executors()


# =========================================================================
# DB SESSION
# =========================================================================
def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()


# =========================================================================
# PYDANTIC MODELLER
# =========================================================================
class LinkRequest(BaseModel):
    url: str
    webhook_url: Optional[str] = None

    @field_validator('url')
    def validate_url_rules(cls, v: str):
        # Max uzunluk kontrolü
        if len(v) > 2048:
            raise ValueError('URL çok uzun (max 2048 karakter).')

        # Control character kontrolü
        if any(ord(c) < 32 for c in v):
            raise ValueError('URL geçersiz karakter içeriyor.')

        if not v.startswith("https://"):
            raise ValueError('Güvenlik gereği linkler "https://" ile başlamalıdır.')

        parsed = urlparse(v)
        domain = parsed.netloc.lower()

        if domain.startswith("www."):
            domain = domain[4:]

        if domain not in ALLOWED_DOMAINS:
            raise ValueError(f"Bu site desteklenmiyor: {domain}.")

        return v

    @field_validator('webhook_url')
    def validate_webhook_url(cls, v: Optional[str]):
        if v is None:
            return v

        # Max uzunluk
        if len(v) > 2048:
            raise ValueError('Webhook URL çok uzun (max 2048 karakter).')

        # SSRF koruması
        is_valid, error = validate_webhook_url(v)
        if not is_valid:
            raise ValueError(f'Webhook URL geçersiz: {error}')

        return v


# =========================================================================
# KORUMASIZ ENDPOINTS — Auth gerekmez (monitoring + bilgi)
# =========================================================================
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


@app.get("/queue")
async def queue_info():
    """Kuyruk durumu — monitoring amaçlı, auth gerekmez."""
    return get_queue_info()


# =========================================================================
# KORUMALI ENDPOINTS — API key gerektirir
# =========================================================================
@app.post("/bypass")
async def bypass_url(
    req: LinkRequest,
    request: Request,
    db: Session = Depends(get_db),
    api_key=Depends(require_api_key),
):
    url = req.url.strip()

    cached_link = db.query(models.BypassLink).filter(models.BypassLink.original_url == url).first()

    # Response header'larında kota bilgisi
    response_headers = {}
    if hasattr(request.state, "quota_remaining"):
        remaining = request.state.quota_remaining
        response_headers["X-RateLimit-Remaining"] = str(remaining) if remaining >= 0 else "unlimited"

    if cached_link:
        if cached_link.status == LinkStatus.SUCCESS:
            return JSONResponse(
                content={"status": LinkStatus.SUCCESS, "resolved_url": cached_link.resolved_url, "safety_status": cached_link.safety_status, "source": "cache"},
                headers=response_headers,
            )
        elif cached_link.status == LinkStatus.PENDING:
            position = get_queue_position(cached_link.id)
            return JSONResponse(
                content={"status": LinkStatus.PENDING, "id": cached_link.id, "queue_position": position, "message": "İşleniyor, lütfen bekleyin."},
                headers=response_headers,
            )
        elif cached_link.status in (LinkStatus.FAILED, LinkStatus.ERROR):
            log.info(f"Başarısız link tekrar deneniyor: {url}")

            cached_link.status = LinkStatus.PENDING
            cached_link.safety_status = None
            cached_link.webhook_url = req.webhook_url
            db.commit()

            submit_to_queue(cached_link.id, url)

            return JSONResponse(
                content={
                    "status": "started",
                    "id": cached_link.id,
                    "queue_position": get_heavy_queue_length() if is_heavy(url) else 0,
                    "message": "Tekrar kuyruğa alındı.",
                },
                headers=response_headers,
            )

    new_record = models.BypassLink(original_url=url, status=LinkStatus.PENDING, webhook_url=req.webhook_url)
    db.add(new_record)
    db.commit()
    db.refresh(new_record)

    submit_to_queue(new_record.id, url)

    return JSONResponse(
        content={
            "status": "started",
            "id": new_record.id,
            "queue_position": get_heavy_queue_length() if is_heavy(url) else 0,
            "message": "İşlem kuyruğa alındı.",
        },
        headers=response_headers,
    )


@app.get("/status/{id}")
async def get_status(
    id: int,
    db: Session = Depends(get_db),
    api_key=Depends(require_api_key),
):
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


@app.get("/analysis/{id}")
async def get_analysis(
    id: int,
    db: Session = Depends(get_db),
    api_key=Depends(require_api_key),
):
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