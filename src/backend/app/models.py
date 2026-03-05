# app/models.py
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Date
from sqlalchemy.sql import func
from .database import Base
from .constants import LinkStatus, ApiPlan


class BypassLink(Base):
    __tablename__ = "bypass_links"

    id = Column(Integer, primary_key=True, index=True)
    original_url = Column(String, unique=True, index=True)
    resolved_url = Column(String, nullable=True)
    status = Column(String, default=LinkStatus.PENDING)
    fail_reason = Column(String, nullable=True)  # link_not_found / timeout / unknown
    webhook_url = Column(String, nullable=True) 
    safety_status = Column(String, nullable=True)  # Clean/Malicious/Suspicious/None
    last_scanned_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class ApiKey(Base):
    """API Key — ticari erişim kontrolü."""
    __tablename__ = "api_keys"

    id = Column(Integer, primary_key=True, index=True)
    key_hash = Column(String, unique=True, index=True, nullable=False)  # SHA-256 hash
    name = Column(String, nullable=False)                               # Kullanıcı/uygulama adı
    plan = Column(String, default=ApiPlan.FREE, nullable=False)         # free/starter/pro/business/website
    daily_limit = Column(Integer, default=50, nullable=False)           # Günlük istek limiti
    requests_today = Column(Integer, default=0, nullable=False)         # Bugünkü kullanım sayacı
    last_reset_date = Column(Date, nullable=True)                       # Sayaç son sıfırlanma tarihi
    is_active = Column(Boolean, default=True, nullable=False)           # Aktif/pasif
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_used_at = Column(DateTime(timezone=True), nullable=True)