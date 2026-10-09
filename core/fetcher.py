"""
Core fetcher.
Descarga fuentes con allowlist de dominios y guarda snapshots con hash SHA-256.
Único componente con acceso a red (Pilar 1).
Incluye limpieza de HTML para mitigar inyección de scripts (T05).
"""
import hashlib
import requests
from urllib.parse import urlparse, urljoin
from datetime import datetime, timezone
from bs4 import BeautifulSoup

ALLOWLIST = [
    "fundacioncodigolibre.org",
    "sportdharma.com",
    "github.com",
    "peopleforbikes.org",
]

USER_AGENT = "SportDharma-MASF/1.0 (contact@sportdharmaecosystem.com)"

MAX_REDIRECTS = 3
MAX_RESPONSE_CHARS = 500_000  # ~500KB de texto


def is_domain_allowed(url: str) -> bool:
    """Verifica que el dominio esté en la allowlist."""
    try:
        domain = urlparse(url).netloc.lower()
        if domain.startswith("www."):
            domain = domain[4:]
        return domain in ALLOWLIST
    except Exception:
        return False


def clean_html(raw_html: str) -> str:
    """
    Limpia HTML extrayendo solo texto visible.
    Mitiga T05: HTML malicioso (XSS/script) en fuente.
    """
    soup = BeautifulSoup(raw_html, "html.parser")
    for script in soup(["script", "style", "noscript", "iframe"]):
        script.decompose()
    text = soup.get_text(separator="\n", strip=True)
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    return "\n".join(lines)


def fetch_source(url: str) -> dict:
    """
    Descarga la URL con redirects controlados y devuelve un dict con:
    - content: texto limpio (sin HTML)
    - content_hash: SHA-256 del contenido limpio
    - retrieved_at: timestamp ISO
    - source_url: URL original
    """
    if not is_domain_allowed(url):
        return {"error": f"Dominio no permitido: {url}"}

    try:
        headers = {"User-Agent": USER_AGENT}
        current_url = url
        redirects_followed = 0

        # Bucle manual de redirects con revalidación de dominio
        while redirects_followed <= MAX_REDIRECTS:
            response = requests.get(
                current_url,
                headers=headers,
                timeout=30,
                allow_redirects=False
            )

            # Si es redirect, revalidar el nuevo dominio
            if response.status_code in (301, 302, 303, 307, 308):
                location = response.headers.get("Location")
                if not location:
                    return {"error": "Redirect sin Location header"}
                
                current_url = urljoin(current_url, location)
                
                if not is_domain_allowed(current_url):
                    return {"error": f"Redirect a dominio no permitido: {current_url}"}
                
                redirects_followed += 1
                continue

            # No es redirect, procesar respuesta
            response.raise_for_status()

            # Límite de tamaño (caracteres de texto)
            if len(response.text) > MAX_RESPONSE_CHARS:
                return {"error": f"Respuesta demasiado grande (>{MAX_RESPONSE_CHARS} caracteres)"}

            content = clean_html(response.text)
            content_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()

            return {
                "content": content,
                "content_hash": content_hash,
                "retrieved_at": datetime.now(timezone.utc).isoformat(),
                "source_url": url,
            }

        return {"error": f"Demasiados redirects (>{MAX_REDIRECTS})"}

    except requests.exceptions.RequestException as e:
        return {"error": str(e)}
    except Exception as e:
        return {"error": str(e)}