"""
Core robots.
Respeto de robots.txt con cache por dominio.
"""
import logging
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser
from threading import Lock
logger = logging.getLogger("masf.robots")
class RobotsChecker:
    """Cache de robots.txt por dominio."""
    def __init__(self, user_agent: str = "*"):
        self.user_agent = user_agent
        self._cache: dict[str, RobotFileParser] = {}
        self._lock = Lock()
    def is_allowed(self, url: str) -> bool:
        """Verifica si el URL está permitido por robots.txt."""
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        robots_url = f"{parsed.scheme}://{domain}/robots.txt"
        with self._lock:
            rp = self._cache.get(domain)
            if rp is None:
                rp = RobotFileParser()
                rp.set_url(robots_url)
                try:
                    rp.read()
                    logger.info("robots loaded domain=%s", domain)
                except Exception as e:
                    logger.warning("robots load_failed domain=%s error=%s", domain, type(e).__name__)
                    rp.allow_all = True
                self._cache[domain] = rp
        return rp.can_fetch(self.user_agent, url)
    def get_crawl_delay(self, url: str) -> float | None:
        """Obtiene el Crawl-delay de robots.txt (en segundos)."""
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        with self._lock:
            rp = self._cache.get(domain)
            if rp is None:
                return None
            delay = rp.crawl_delay(self.user_agent)
            return float(delay) if delay else None
    def clear_cache(self) -> None:
        """Limpia el cache de robots.txt (para tests)."""
        with self._lock:
            self._cache.clear()
_default_checker: RobotsChecker | None = None
def get_default_checker(user_agent: str = "*") -> RobotsChecker:
    """Instancia compartida por proceso."""
    global _default_checker
    if _default_checker is None:
        _default_checker = RobotsChecker(user_agent)
    return _default_checker
def reset_default_checker() -> None:
    """Descarta la instancia compartida (para tests)."""
    global _default_checker
    _default_checker = None
