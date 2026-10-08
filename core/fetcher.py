"""
Core fetcher.
Descarga fuentes con allowlist de dominios y guarda snapshots con hash SHA-256.
Único componente con acceso a red (Pilar 1).
Incluye limpieza de HTML para mitigar inyección de scripts (T05).
"""
import hashlib
import requests
from urllib.parse import urlparse
from datetime import datetime, timezone
from bs4 import BeautifulSoup


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


def clean_html(raw_html: str) -> str:
    """
    Limpia HTML extrayendo solo texto visible.
    Mitiga T05: HTML malicioso (XSS/script) en fuente.
    """
    soup = BeautifulSoup(raw_html, "html.parser")
    
    # Eliminar scripts y estilos
    for script in soup(["script", "style", "noscript", "iframe"]):
        script.decompose()
    
    # Extraer texto
    text = soup.get_text(separator="\n", strip=True)
    
    # Limpiar líneas vacías múltiples
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    return "\n".join(lines)


def fetch_source(url: str) -> dict:
    """
    Descarga la URL y devuelve un dict con:
    - content: texto limpio (sin HTML)
    - content_hash: SHA-256 del contenido limpio
    - retrieved_at: timestamp ISO
    - source_url: URL original
    """
    if not is_domain_allowed(url):
        return {"error": f"Dominio no permitido: {url}"}

    try:
        headers = {"User-Agent": USER_AGENT}
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()

        # Limpiar HTML (mitiga T05)
        raw_html = response.text
        content = clean_html(raw_html)

        # Hash del contenido LIMPIO (no del HTML crudo)
        content_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()

        return {
            "content": content,
            "content_hash": content_hash,
            "retrieved_at": datetime.now(timezone.utc).isoformat(),
            "source_url": url,
        }
    except Exception as e:
        return {"error": str(e)}