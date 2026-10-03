"""
Core fetcher.
Descarga fuentes con allowlist de dominios y guarda snapshots con hash SHA-256.
Único componente con acceso a red (Pilar 1).
"""
import hashlib
import requests
from urllib.parse import urlparse
from datetime import datetime, timezone

ALLOWLIST = [
    "fundacioncodigolibre.org",
    "sportdharma.com",
    "github.com",
]

USER_AGENT = "SportDharma-MASF/1.0 (contact@sportdharmaecosystem.com)"


def is_domain_allowed(url: str) -> bool:
    """Verifica que el dominio esté en la allowlist."""
    domain = urlparse(url).netloc.lower()
    # Quitar www. si existe
    if domain.startswith("www."):
        domain = domain[4:]
    return domain in ALLOWLIST


def fetch_source(url: str) -> dict:
    """
    Descarga la URL y devuelve un dict con:
    - content: texto descargado
    - content_hash: SHA-256 del contenido
    - retrieved_at: timestamp ISO
    - source_url: URL original
    """
    if not is_domain_allowed(url):
        return {"error": f"Dominio no permitido: {url}"}

    try:
        headers = {"User-Agent": USER_AGENT}
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()

        content = response.text
        content_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()

        return {
            "content": content,
            "content_hash": content_hash,
            "retrieved_at": datetime.now(timezone.utc).isoformat(),
            "source_url": url,
        }
    except Exception as e:
        return {"error": str(e)}