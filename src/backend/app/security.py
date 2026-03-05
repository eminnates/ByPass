"""
SSRF Koruması — Webhook URL Validasyonu

Private IP aralıkları, loopback, cloud metadata endpoint'leri ve
internal hostname'leri bloklar.
"""

import socket
import ipaddress
from urllib.parse import urlparse
from app.logger import get_logger

log = get_logger("security")

# Bloklanan hostname'ler
_BLOCKED_HOSTNAMES = {
    "localhost",
    "metadata.google.internal",        # GCP metadata
    "metadata.internal",
}

# Cloud metadata IP'leri
_BLOCKED_IPS = {
    ipaddress.ip_address("169.254.169.254"),  # AWS/GCP/Azure metadata
    ipaddress.ip_address("fd00::1"),           # link-local metadata (IPv6)
}


def _is_private_or_blocked(ip_str: str) -> bool:
    """IP adresinin private, loopback veya bloklanan bir adres olup olmadığını kontrol eder."""
    try:
        ip = ipaddress.ip_address(ip_str)
        if ip.is_private or ip.is_loopback or ip.is_reserved or ip.is_link_local:
            return True
        if ip in _BLOCKED_IPS:
            return True
        return False
    except ValueError:
        return True  # Geçersiz IP → blokla


def validate_webhook_url(url: str) -> tuple[bool, str]:
    """
    Webhook URL'sini SSRF açıklarına karşı doğrular.
    
    Returns:
        (is_valid, error_message)
    """
    if not url:
        return True, ""

    # 1. Schema kontrolü
    try:
        parsed = urlparse(url)
    except Exception:
        return False, "Geçersiz URL formatı."

    if parsed.scheme not in ("http", "https"):
        return False, "Webhook URL sadece http:// veya https:// olabilir."

    hostname = parsed.hostname
    if not hostname:
        return False, "Webhook URL'de hostname bulunamadı."

    # 2. Bloklanan hostname kontrolü
    if hostname.lower() in _BLOCKED_HOSTNAMES:
        return False, f"Bu hostname webhook için kullanılamaz: {hostname}"

    # 3. DNS çözümle ve IP kontrolü yap
    try:
        addr_infos = socket.getaddrinfo(hostname, parsed.port or 443, proto=socket.IPPROTO_TCP)
    except socket.gaierror:
        return False, f"Webhook hostname çözümlenemedi: {hostname}"

    for family, _, _, _, sockaddr in addr_infos:
        ip_str = sockaddr[0]
        if _is_private_or_blocked(ip_str):
            log.warning(f"SSRF bloklandı: {url} → {ip_str}")
            return False, "Webhook URL private/internal bir adrese işaret ediyor."

    return True, ""
