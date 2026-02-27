# app/models.py
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func
from .database import Base
from .constants import LinkStatus

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