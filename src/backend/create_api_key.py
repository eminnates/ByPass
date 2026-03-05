#!/usr/bin/env python3
"""
API Key Oluşturma CLI — Admin Aracı

Kullanım:
    python create_api_key.py --name "Web Sitem" --plan website
    python create_api_key.py --name "Test Kullanıcı" --plan free
    python create_api_key.py --name "Premium Müşteri" --plan pro
    python create_api_key.py --list
    python create_api_key.py --deactivate KEY_ID

Planlar: free (50/gün), starter (500/gün), pro (5000/gün), business (50000/gün), website (sınırsız)
"""

import sys
import os
import argparse
import secrets
import hashlib
from datetime import datetime, timezone

# Path setup
sys.path.insert(0, os.path.dirname(__file__))

from app.database import SessionLocal, engine
from app.models import ApiKey, Base
from app.constants import ApiPlan, PLAN_DAILY_LIMITS


def hash_key(raw_key: str) -> str:
    return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()


def create_key(name: str, plan: str):
    """Yeni API key oluşturur."""
    # Plan doğrulama
    valid_plans = [p.value for p in ApiPlan]
    if plan not in valid_plans:
        print(f"❌ Geçersiz plan: {plan}")
        print(f"   Geçerli planlar: {', '.join(valid_plans)}")
        return

    # Tabloyu oluştur (yoksa)
    Base.metadata.create_all(bind=engine)

    # API key oluştur (32 byte = 64 hex karakter)
    raw_key = f"bp_{secrets.token_hex(24)}"  # bp_<48 hex chars> = toplam 51 karakter
    key_hash = hash_key(raw_key)

    daily_limit = PLAN_DAILY_LIMITS.get(plan, 50)

    db = SessionLocal()
    try:
        api_key = ApiKey(
            key_hash=key_hash,
            name=name,
            plan=plan,
            daily_limit=daily_limit,
            requests_today=0,
            is_active=True,
        )
        db.add(api_key)
        db.commit()
        db.refresh(api_key)

        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print("✅ API Key Oluşturuldu!")
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print(f"   ID:        {api_key.id}")
        print(f"   Ad:        {name}")
        print(f"   Plan:      {plan}")
        print(f"   Limit:     {'Sınırsız' if daily_limit == 0 else f'{daily_limit}/gün'}")
        print(f"   Key:       {raw_key}")
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print("⚠️  Bu key bir daha gösterilmez! Sakla.")
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

    finally:
        db.close()


def list_keys():
    """Tüm API key'leri listeler."""
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        keys = db.query(ApiKey).all()
        if not keys:
            print("Henüz API key oluşturulmamış.")
            return

        print(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print(f"  {'ID':>4}  {'Ad':<20}  {'Plan':<10}  {'Kullanım':<15}  {'Aktif':>5}")
        print(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

        for k in keys:
            limit_str = "∞" if k.daily_limit == 0 else str(k.daily_limit)
            usage = f"{k.requests_today}/{limit_str}"
            status = "✅" if k.is_active else "❌"
            print(f"  {k.id:>4}  {k.name:<20}  {k.plan:<10}  {usage:<15}  {status:>5}")

        print(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    finally:
        db.close()


def deactivate_key(key_id: int):
    """API key'i devre dışı bırakır."""
    db = SessionLocal()
    try:
        api_key = db.query(ApiKey).filter(ApiKey.id == key_id).first()
        if not api_key:
            print(f"❌ ID={key_id} bulunamadı.")
            return

        api_key.is_active = False
        db.commit()
        print(f"✅ API key devre dışı bırakıldı: {api_key.name} (ID={key_id})")
    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="ByPass API Key Yönetimi")
    parser.add_argument("--name", type=str, help="Kullanıcı/uygulama adı")
    parser.add_argument("--plan", type=str, default="free", 
                        help="Plan: free, starter, pro, business, website")
    parser.add_argument("--list", action="store_true", help="Tüm key'leri listele")
    parser.add_argument("--deactivate", type=int, help="Key ID devre dışı bırak")
    args = parser.parse_args()

    if args.list:
        list_keys()
    elif args.deactivate:
        deactivate_key(args.deactivate)
    elif args.name:
        create_key(args.name, args.plan)
    else:
        parser.print_help()
