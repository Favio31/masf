"""
Core cache.
Cache en filesystem para los resultados de core/fetcher.py (sin DB, solo stdlib).
Diseno
Clave de la entrada: SHA-256 de la URL normalizada. El content_hash NO puede ser
la clave: solo se conoce DESPUES de descargar, que es justo lo que el cache evita.
El content_hash se guarda dentro de la entrada y se usa para dos cosas:
Integridad al leer: si el contenido en disco ya no coincide con su hash
(archivo manipulado o corrupto), la entrada se invalida y cuenta como miss.
Deteccion de cambios al refrescar: si una URL vuelve con un hash distinto,
la entrada se reemplaza y se registra el evento `content_changed`.
TTL configurable (default 24 h) via constructor o MASF_CACHE_TTL_SECONDS.
Una entrada vencida cuenta como miss pero se conserva hasta que se refresca (asi se
detecta el cambio de hash) o hasta purge_expired(); `size_bytes` la incluye.
Solo se cachean resultados exitosos. Los errores nunca se guardan.
Escritura atomica (archivo temporal + os.replace): un crash no deja JSON a medias.
Logging estructurado: una linea JSON por evento en el logger "masf.cache".
Metricas por proceso (hits/misses/...) y tamano en disco calculado al pedirlo.
"""
from __future__ import annotations
import hashlib
import json
import logging
import os
import tempfile
import threading
import time
from pathlib import Path
from typing import Callable, Optional
from urllib.parse import urlsplit, urlunsplit
logger = logging.getLogger("masf.cache")
CACHE_VERSION = 1
DEFAULT_CACHE_DIR = "cache"
DEFAULT_TTL_SECONDS = 24 * 60 * 60
ENV_CACHE_DIR = "MASF_CACHE_DIR"
ENV_CACHE_TTL = "MASF_CACHE_TTL_SECONDS"
_REQUIRED_RESULT_KEYS = ("content", "content_hash", "retrieved_at", "source_url", "method")
def _log(event: str, level: int = logging.INFO, **fields) -> None:
    """Emite una linea JSON por evento (facil de grepear y de parsear)."""
    if logger.isEnabledFor(level):
        logger.log(level, json.dumps({"event": event, **fields}, ensure_ascii=False, sort_keys=True))
def normalize_url(url: str) -> str:
    """Esquema y host en minusculas, sin fragmento (no cambia lo que sirve el servidor)."""
    parts = urlsplit(url.strip())
    return urlunsplit((parts.scheme.lower(), parts.netloc.lower(), parts.path, parts.query, ""))
def cache_key(url: str) -> str:
    """SHA-256 hex de la URL normalizada."""
    return hashlib.sha256(normalize_url(url).encode("utf-8")).hexdigest()
def _ttl_from_env(default: int) -> int:
    raw = os.environ.get(ENV_CACHE_TTL)
    if raw is None:
        return default
    try:
        return int(raw)
    except ValueError:
        _log("invalid_ttl_env", logging.WARNING, value=raw, using=default)
        return default
class FetchCache:
    """Cache de resultados de fetch_source() en `cache_dir/<sha256(url)>.json`."""
    def __init__(
        self,
        cache_dir: Optional[os.PathLike | str] = None,
        ttl_seconds: Optional[int] = None,
        clock: Callable[[], float] = time.time,
    ) -> None:
        self.cache_dir = Path(cache_dir or os.environ.get(ENV_CACHE_DIR) or DEFAULT_CACHE_DIR)
        self.ttl_seconds = ttl_seconds if ttl_seconds is not None else _ttl_from_env(DEFAULT_TTL_SECONDS)
        self._clock = clock
        self._lock = threading.Lock()
        self._counters = self._empty_counters()
    @staticmethod
    def _empty_counters() -> dict:
        return {"hits": 0, "misses": 0, "expired": 0, "invalidated": 0, "stores": 0, "content_changed": 0}
    def _bump(self, name: str) -> None:
        with self._lock:
            self._counters[name] += 1
    def _path(self, url: str) -> Path:
        return self.cache_dir / f"{cache_key(url)}.json"
    @staticmethod
    def _read_entry(path: Path) -> Optional[dict]:
        try:
            entry = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return None
        return entry if isinstance(entry, dict) else None
    @staticmethod
    def _is_valid_result(result: object) -> bool:
        return (
            isinstance(result, dict)
            and "error" not in result
            and all(isinstance(result.get(k), str) for k in _REQUIRED_RESULT_KEYS)
        )
    @staticmethod
    def _remove(path: Path) -> None:
        try:
            path.unlink()
        except FileNotFoundError:
            pass
        except OSError as exc:
            _log("remove_failed", logging.WARNING, path=str(path), error=str(exc))
    def get(self, url: str) -> Optional[dict]:
        """Devuelve el resultado cacheado (misma forma que fetch_source) o None."""
        key = cache_key(url)
        path = self._path(url)
        if not path.exists():
            self._bump("misses")
            _log("cache_miss", url=url, key=key, reason="absent")
            return None
        entry = self._read_entry(path)
        result = entry.get("result") if entry else None
        stored_at = entry.get("stored_at") if entry else None
        if (
            entry is None
            or entry.get("cache_version") != CACHE_VERSION
            or entry.get("url") != normalize_url(url)
            or not isinstance(stored_at, (int, float))
            or not self._is_valid_result(result)
        ):
            return self._invalidate_on_read(url, key, path, "corrupt_or_incompatible")
        age = self._clock() - stored_at
        if age < 0 or age >= self.ttl_seconds:
            self._bump("expired")
            self._bump("misses")
            _log("cache_miss", url=url, key=key, reason="expired", age_seconds=round(age, 3),
                 ttl_seconds=self.ttl_seconds)
            return None
        actual = hashlib.sha256(result["content"].encode("utf-8")).hexdigest()
        if actual != result["content_hash"]:
            return self._invalidate_on_read(url, key, path, "hash_mismatch")
        self._bump("hits")
        _log("cache_hit", url=url, key=key, age_seconds=round(age, 3), content_hash=result["content_hash"])
        return dict(result)
    def put(self, url: str, result: dict) -> bool:
        """Guarda un resultado exitoso. Devuelve False si no es cacheable."""
        if not self._is_valid_result(result):
            _log("cache_skip", url=url, reason="not_cacheable")
            return False
        key = cache_key(url)
        path = self._path(url)
        previous = self._read_entry(path) if path.exists() else None
        previous_result = previous.get("result") if previous else None
        if isinstance(previous_result, dict) and previous_result.get("content_hash") != result["content_hash"]:
            self._bump("content_changed")
            _log("content_changed", url=url, key=key,
                 old_hash=previous_result.get("content_hash"), new_hash=result["content_hash"])
        entry = {
            "cache_version": CACHE_VERSION,
            "url": normalize_url(url),
            "stored_at": self._clock(),
            "result": result,
        }
        try:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            fd, tmp_name = tempfile.mkstemp(dir=self.cache_dir, prefix=".tmp-", suffix=".json")
            try:
                with os.fdopen(fd, "w", encoding="utf-8") as fh:
                    json.dump(entry, fh, ensure_ascii=False)
                os.replace(tmp_name, path)
            except BaseException:
                self._remove(Path(tmp_name))
                raise
        except OSError as exc:
            _log("cache_write_failed", logging.WARNING, url=url, key=key, error=str(exc))
            return False
        self._bump("stores")
        _log("cache_store", url=url, key=key, content_hash=result["content_hash"], ttl_seconds=self.ttl_seconds)
        return True
    def invalidate(self, url: str) -> bool:
        """Borra la entrada de una URL. True si existia."""
        path = self._path(url)
        existed = path.exists()
        self._remove(path)
        if existed:
            self._bump("invalidated")
            _log("cache_invalidate", url=url, key=cache_key(url), reason="manual")
        return existed
    def purge_expired(self) -> int:
        """Borra todas las entradas vencidas o ilegibles. Devuelve cuantas elimino."""
        removed = 0
        for path in self._entry_files():
            entry = self._read_entry(path)
            stored_at = entry.get("stored_at") if entry else None
            age = self._clock() - stored_at if isinstance(stored_at, (int, float)) else None
            if age is None or age < 0 or age >= self.ttl_seconds:
                self._remove(path)
                removed += 1
        if removed:
            _log("cache_purge", removed=removed)
        return removed
    def clear(self) -> int:
        """Borra todo el cache. Devuelve cuantas entradas elimino."""
        files = list(self._entry_files())
        for path in files:
            self._remove(path)
        _log("cache_clear", removed=len(files))
        return len(files)
    def stats(self) -> dict:
        """Metricas de este proceso + tamano actual en disco."""
        with self._lock:
            counters = dict(self._counters)
        lookups = counters["hits"] + counters["misses"]
        files = list(self._entry_files())
        size = 0
        for path in files:
            try:
                size += path.stat().st_size
            except OSError:
                pass
        return {
            **counters,
            "lookups": lookups,
            "hit_rate": counters["hits"] / lookups if lookups else 0.0,
            "miss_rate": counters["misses"] / lookups if lookups else 0.0,
            "entries": len(files),
            "size_bytes": size,
            "ttl_seconds": self.ttl_seconds,
        }
    def reset_metrics(self) -> None:
        with self._lock:
            self._counters = self._empty_counters()
    def _entry_files(self):
        if not self.cache_dir.is_dir():
            return iter(())
        return (p for p in self.cache_dir.glob("*.json") if not p.name.startswith(".tmp-"))
    def _invalidate_on_read(self, url: str, key: str, path: Path, reason: str) -> None:
        self._remove(path)
        self._bump("invalidated")
        self._bump("misses")
        _log("cache_invalidate", logging.WARNING, url=url, key=key, reason=reason)
        _log("cache_miss", url=url, key=key, reason=reason)
        return None
_default_cache: Optional[FetchCache] = None
def get_default_cache() -> FetchCache:
    """Instancia compartida por proceso (cache/ o MASF_CACHE_DIR, TTL de MASF_CACHE_TTL_SECONDS)."""
    global _default_cache
    if _default_cache is None:
        _default_cache = FetchCache()
    return _default_cache
def reset_default_cache() -> None:
    """Descarta la instancia compartida (util en tests)."""
    global _default_cache
    _default_cache = None
