# app/models.py
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func
from .database import Base

class BypassLink(Base):
    __tablename__ = "bypass_links"

    id = Column(Integer, primary_key=True, index=True)
    original_url = Column(String, unique=True, index=True)
    resolved_url = Column(String, nullable=True)
    status = Column(String, default="pending")
    # YENİ SÜTUN:
    webhook_url = Column(String, nullable=True) 
    safety_status = Column(String, nullable=True)  # Clean/Malicious/Suspicious/None
    last_scanned_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())