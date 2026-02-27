from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, declarative_base

# SQLite — WAL modu ile concurrent read/write güvenli
SQLALCHEMY_DATABASE_URL = "sqlite:///./sql_app.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False, "timeout": 15},
    pool_size=10,
    max_overflow=20,
    pool_recycle=3600,
)

# WAL modu — okuma ve yazma birbirini bloklamaz
@event.listens_for(engine, "connect")
def _set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA synchronous=NORMAL")  # Performans artışı
    cursor.close()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


from contextlib import contextmanager

@contextmanager
def get_db_session():
    """
    Context manager ile güvenli DB session yönetimi.
    
    Kullanım:
        with get_db_session() as db:
            record = db.query(Model).first()
            record.status = "done"
            # commit otomatik — hata olursa rollback yapılır
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()