"""
Core fetcher.
Descarga fuentes con allowlist de dominios y guarda snapshots con hash SHA-256.
Unico componente con acceso a red (Pilar 1).
Incluye limpieza de HTML para mitigar inyeccion de scripts (T05).
Soporte fallback a Playwright para sitios con renderizado JS.
Integracion de cache (core/cache.py): FetchCache de Genspark.
"""
import hashlib
import logging
import requests
from urllib.parse import urlparse, urljoin
from datetime import datetime, timezone
from bs4 import BeautifulSoup
from core.cache import get_default_cache
logger = logging.getLogger("masf.fetcher")
ALLOWLIST = [
    "fundacioncodigolibre.org",
    "sportdharma.com",
    "github.com",
    "peopleforbikes.org",
    "openaffiliate.dev",
    "freakingnomads.com",
    "nomadglobal.com",
    "devinci.com",
    "3t.bike",
    "bikepacking.com",
    "thetravelingvagabond.com",
    "localhost",
]
USER_AGENT = "SportDharma-MASF/1.0 (contact@sportdharmaecosystem.com)"
MAX_REDIRECTS = 3
MAX_RESPONSE_CHARS = 500_000
MIN_CONTENT_CHARS = 150
def is_domain_allowed(url: str) -> bool:
    """Check the existing hostname allowlist before cache or network access."""
    try:
        parsed = urlparse(url)
        if parsed.scheme not in {"http", "https"} or not parsed.hostname:
            return False
        domain = parsed.hostname.lower()
        if domain.startswith("www."):
            domain = domain[4:]
        if ":" in domain:
            domain = domain.split(":")[0]
        return domain in ALLOWLIST
    except (TypeError, ValueError):
        return False
def clean_html(raw_html: str) -> str:
    soup = BeautifulSoup(raw_html, "html.parser")
    for script in soup(["script", "style", "noscript", "iframe"]):
        script.decompose()
    text = soup.get_text(separator="\n", strip=True)
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    return "\n".join(lines)
def _maybe_cache(cache, url: str, result: dict, use_cache: bool) -> dict:
    """Guarda en cache un resultado de fetch exitoso (best-effort)."""
    if use_cache and "error" not in result:
        try:
            cache.put(url, result)
        except Exception as e:
            logger.warning("cache STORE_FAILED url=%s reason=%s", url, type(e).__name__)
    return result
def fetch_with_playwright(url: str) -> dict:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return {"error": "Playwright no instalado"}
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page(user_agent=USER_AGENT)
            response = page.goto(url, wait_until="networkidle", timeout=15000)
            if response is None or not response.ok:
                browser.close()
                return {"error": "Playwright fallo"}
            page.wait_for_timeout(2000)
            html = page.content()
            browser.close()
            content = clean_html(html)
            if len(content) > MAX_RESPONSE_CHARS:
                return {"error": "Respuesta muy grande"}
            content_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()
            return {
                "content": content,
                "content_hash": content_hash,
                "retrieved_at": datetime.now(timezone.utc).isoformat(),
                "source_url": url,
                "method": "playwright",
            }
    except Exception:
        logger.exception("playwright_fetch_failed")
        return {"error": "Error Playwright"}
def fetch_source(url: str, use_cache: bool = True, cache=None) -> dict:
    """Fetch an allowlisted URL, optionally using the filesystem cache."""
    if not is_domain_allowed(url):
        return {"error": f"Dominio no permitido: {url}"}
    if cache is None:
        cache = get_default_cache()
    if use_cache:
        try:
            cached = cache.get(url)
            if cached is not None:
                return cached
        except (OSError, ValueError, TypeError):
            logger.warning("masf_cache_read_failed")
    try:
        headers = {"User-Agent": USER_AGENT}
        current_url = url
        redirects_followed = 0
        while redirects_followed <= MAX_REDIRECTS:
            response = requests.get(
                current_url, headers=headers, timeout=15, allow_redirects=False
            )
            if response.status_code in (301, 302, 303, 307, 308):
                location = response.headers.get("Location")
                if not location:
                    return {"error": "Redirect sin Location"}
                current_url = urljoin(current_url, location)
                if not is_domain_allowed(current_url):
                    return {"error": "Redirect no permitido"}
                redirects_followed += 1
                continue
            response.raise_for_status()
            if len(response.text) > MAX_RESPONSE_CHARS:
                return {"error": "Respuesta muy grande"}
            content = clean_html(response.text)
            if len(content) < MIN_CONTENT_CHARS:
                result = fetch_with_playwright(url)
            else:
                content_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()
                result = {
                    "content": content,
                    "content_hash": content_hash,
                    "retrieved_at": datetime.now(timezone.utc).isoformat(),
                    "source_url": url,
                    "method": "requests",
                }
            return _maybe_cache(cache, url, result, use_cache)
        return {"error": "Demasiados redirects"}
    except requests.exceptions.RequestException:
        result = fetch_with_playwright(url)
        return _maybe_cache(cache, url, result, use_cache)
    except Exception:
        logger.exception("fetch_source_failed")
        return {"error": "Error de descarga"}
