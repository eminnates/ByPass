import logging
import os
from datetime import datetime
from logging.handlers import RotatingFileHandler

# --- Log klasörünü oluştur ---
LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs")
os.makedirs(LOG_DIR, exist_ok=True)

# --- Log dosyası adı (günlük) ---
LOG_FILE = os.path.join(LOG_DIR, f"bypass_{datetime.now().strftime('%Y-%m-%d')}.log")

# --- Format ---
LOG_FORMAT = "[%(asctime)s] %(levelname)-8s %(name)-20s | %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# --- Root logger ayarı (bir kez çalışır) ---
logging.basicConfig(
    level=logging.INFO,
    format=LOG_FORMAT,
    datefmt=DATE_FORMAT,
    handlers=[
        # Konsola yaz
        logging.StreamHandler(),
        # Dosyaya yaz (max 5MB, 3 yedek = en fazla 20MB disk)
        RotatingFileHandler(LOG_FILE, maxBytes=5*1024*1024, backupCount=3, encoding="utf-8"),
    ],
)

def get_logger(name: str) -> logging.Logger:
    """Modül adıyla bir logger döner."""
    return logging.getLogger(name)
