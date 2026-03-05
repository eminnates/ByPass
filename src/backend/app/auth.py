"""
API Key Authentication — FastAPI Dependency

Tüm korumalı endpoint'lerde Depends(require_api_key) ile kullanılır.
Fonksiyonlar:
    - require_api_key: X-API-Key header doğrulama + kota kontrolü
    - hash_key: API key'i SHA-256 ile hashler
    - verify_daily_quota: Günlük kullanım limiti kontrolü
"""

import hashlib
from datetime import date, datetime, timezone
from fastapi import Header, HTTPException, Depends, Request
from sqlalchemy.orm import Session
from app.models import ApiKey
from app.constants import PLAN_DAILY_LIMITS, RATE_LIMIT_PER_MINUTE
from app.rate_limiter import check_rate_limit
from app.logger import get_logger

log = get_logger("auth")


def hash_key(raw_key: str) -> str:
    """API key'i SHA-256 ile hashler."""
    return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()


def _get_db():
    """Auth için DB session — her istek sonunda kapatılır."""
    from app.database import SessionLocal
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def require_api_key(
    request: Request,
    x_api_key: str = Header(..., alias="X-API-Key", description="API erişim anahtarı"),
    db: Session = Depends(_get_db),
) -> ApiKey:
    """
    API key doğrulama dependency'si.
    
    1. Header'dan X-API-Key al
    2. SHA-256 hash ile DB'de ara
    3. Aktif mi kontrol et
    4. IP bazlı rate limit kontrol et
    5. Günlük kota kontrol et
    6. Sayacı artır
    
    Başarılıysa ApiKey nesnesi döndürür → endpoint içinde kullanılabilir.
    """
    if not x_api_key:
        raise HTTPException(status_code=401, detail="API key gerekli. Header: X-API-Key")

    # 1. Key hash'le ve DB'de ara
    key_hash = hash_key(x_api_key)
    api_key = db.query(ApiKey).filter(ApiKey.key_hash == key_hash).first()

    if not api_key:
        log.warning(f"Geçersiz API key denemesi: {x_api_key[:8]}...")
        raise HTTPException(status_code=401, detail="Geçersiz API key.")

    # 2. Aktif mi?
    if not api_key.is_active:
        log.warning(f"Devre dışı API key: {api_key.name}")
        raise HTTPException(status_code=403, detail="Bu API key devre dışı bırakılmış.")

    # 3. IP bazlı rate limit (tüm planlar için)
    client_ip = request.client.host if request.client else "unknown"
    rate_allowed, rate_remaining = check_rate_limit(
        f"ip:{client_ip}", RATE_LIMIT_PER_MINUTE
    )
    if not rate_allowed:
        log.warning(f"Rate limit aşıldı: IP={client_ip}")
        raise HTTPException(
            status_code=429,
            detail="Çok fazla istek. Lütfen biraz bekleyin.",
            headers={"Retry-After": "60"},
        )

    # 4. Günlük kota kontrolü
    today = date.today()
    if api_key.last_reset_date != today:
        # Yeni gün — sayacı sıfırla
        api_key.requests_today = 0
        api_key.last_reset_date = today

    daily_limit = PLAN_DAILY_LIMITS.get(api_key.plan, api_key.daily_limit)

    # 0 = sınırsız (website planı)
    if daily_limit > 0 and api_key.requests_today >= daily_limit:
        log.warning(f"Günlük kota aşıldı: {api_key.name} ({api_key.plan})")
        raise HTTPException(
            status_code=429,
            detail=f"Günlük istek limitine ulaşıldınız ({daily_limit}/{daily_limit}). "
                   f"Plan yükseltmek için iletişime geçin.",
            headers={"Retry-After": "86400"},  # 24 saat
        )

    # 5. Sayacı artır ve son kullanım güncelle
    api_key.requests_today += 1
    api_key.last_used_at = datetime.now(timezone.utc)
    db.commit()

    # Response header'lara kota bilgisi ekle (endpoint'te kullanılabilir)
    request.state.api_key = api_key
    request.state.rate_remaining = rate_remaining
    request.state.quota_remaining = (daily_limit - api_key.requests_today) if daily_limit > 0 else -1

    return api_key
