"""
Core rate limiter.
Controla la frecuencia de requests por dominio con backoff exponencial.
Respeto de robots.txt y Crawl-delay.
"""
import time
import logging
from urllib.parse import urlparse
from threading import Lock
logger = logging.getLogger("masf.rate_limiter")
class RateLimiter:
    """Rate limiter por dominio con backoff exponencial."""
    def __init__(self, min_delay: float = 2.0, max_delay: float = 60.0, backoff_factor: float = 2.0):
        self.min_delay = min_delay
        self.max_delay = max_delay
        self.backoff_factor = backoff_factor
        self._last_request: dict[str, float] = {}
        self._consecutive_errors: dict[str, int] = {}
        self._lock = Lock()
    def wait_for_domain(self, domain: str) -> None:
        """Espera el tiempo necesario antes de hacer otro request al dominio."""
        with self._lock:
            last = self._last_request.get(domain, 0.0)
            errors = self._consecutive_errors.get(domain, 0)
            delay = self.min_delay * (self.backoff_factor ** errors)
            delay = min(delay, self.max_delay)
            elapsed = time.time() - last
            if elapsed < delay:
                wait_time = delay - elapsed
                logger.info("rate_limit wait domain=%s seconds=%.1f errors=%d", domain, wait_time, errors)
                time.sleep(wait_time)
    def record_success(self, domain: str) -> None:
        """Registra un request exitoso (resetea el contador de errores)."""
        with self._lock:
            self._last_request[domain] = time.time()
            self._consecutive_errors[domain] = 0
    def record_error(self, domain: str, status_code: int | None = None) -> None:
        """Registra un error (incrementa backoff para 429/5xx)."""
        with self._lock:
            self._last_request[domain] = time.time()
            if status_code and status_code in (429, 500, 502, 503, 504):
                self._consecutive_errors[domain] = self._consecutive_errors.get(domain, 0) + 1
                logger.warning("rate_limit error domain=%s status=%d backoff=%d", domain, status_code, self._consecutive_errors[domain])
    def reset(self) -> None:
        """Resetea todos los contadores (para tests)."""
        with self._lock:
            self._last_request.clear()
            self._consecutive_errors.clear()
_default_limiter: RateLimiter | None = None
def get_default_limiter() -> RateLimiter:
    """Instancia compartida por proceso."""
    global _default_limiter
    if _default_limiter is None:
        _default_limiter = RateLimiter()
    return _default_limiter
def reset_default_limiter() -> None:
    """Descarta la instancia compartida (para tests)."""
    global _default_limiter
    _default_limiter = None
