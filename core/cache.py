"""
Core cache.
Cache de snapshots en filesystem para core/fetcher.py.
Clave de cache: SHA-256 (hex) de la URL. Por construccion el nombre de
archivo es un hex digest: no hay path traversal posible.
TTL configurable (default: 24 horas). Invalidacion automatica por:
expiracion del TTL, 2) cambio de content_hash (contenido modificado).
Metricas en memoria: hits, misses, writes, evictions, content_changes,
hit_rate, miss_rate y tamano del cache.
Logging estructurado via modulo logging (sin print, sin paths del
filesystem en los mensajes: se registra URL y clave hex, nunca rutas).
Sin dependencias nuevas: solo stdlib (Python 3.12+).
"""
import hashlib
import json
import logging
import os
import time
from pathlib import Path
logger = logging.getLogger("masf.cache")
DEFAULT_TTL_SECONDS = 24 * 60 * 60
CACHE_DIR = Path("cache")
_metrics: dict = {
    "hits": 0,
    "misses": 0,
    "writes": 0,
    "evictions": 0,
    "content_changes": 0,
}
def key_for_url(url: str) -> str:
    return hashlib.sha256(url.encode("utf-8")).hexdigest()
def _entry_path(key: str) -> Path:
    return CACHE_DIR / f"{key}.json"
def _safe_unlink(path: Path) -> None:
    try:
        path.unlink(missing_ok=True)
    except OSError as e:
        logger.warning("cache DELETE_FAILED key_prefix=%s reason=%s", path.stem[:8], type(e).__name__)
def get_cached(url: str, ttl: int = DEFAULT_TTL_SECONDS, now: float | None = None) -> dict | None:
    now = time.time() if now is None else now
    key = key_for_url(url)
    path = _entry_path(key)
    if not path.exists():
        _metrics["misses"] += 1
        logger.info("cache MISS url=%s key=%s reason=absent", url, key)
        return None
    try:
        entry = json.loads(path.read_text(encoding="utf-8"))
        stored_at = float(entry["stored_at"])
        result = dict(entry["result"])
    except (json.JSONDecodeError, KeyError, TypeError, ValueError, OSError):
        _metrics["evictions"] += 1
        _metrics["misses"] += 1
        logger.warning("cache CORRUPT_ENTRY key=%s action=discard", key)
        _safe_unlink(path)
        return None
    if now - stored_at >= ttl:
        _metrics["evictions"] += 1
        _metrics["misses"] += 1
        logger.info("cache EXPIRED url=%s key=%s ttl=%ss", url, key, ttl)
        _safe_unlink(path)
        return None
    _metrics["hits"] += 1
    logger.info("cache HIT url=%s key=%s age=%.1fs", url, key, now - stored_at)
    return result
def store(url: str, fetch_result: dict, ttl: int = DEFAULT_TTL_SECONDS, now: float | None = None) -> bool:
    if "error" in fetch_result:
        logger.info("cache SKIP_WRITE url=%s reason=fetch_error", url)
        return False
    now = time.time() if now is None else now
    key = key_for_url(url)
    path = _entry_path(key)
    content_hash = fetch_result.get("content_hash", "")
    if path.exists():
        try:
            prev = json.loads(path.read_text(encoding="utf-8"))
            if prev.get("content_hash") != content_hash:
                _metrics["content_changes"] += 1
                logger.info("cache CONTENT_CHANGED url=%s key=%s action=overwrite", url, key)
        except (json.JSONDecodeError, OSError):
            pass
    entry = {
        "url": url,
        "key": key,
        "content_hash": content_hash,
        "stored_at": now,
        "ttl": ttl,
        "result": fetch_result,
    }
    try:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(".tmp")
        tmp.write_text(json.dumps(entry, ensure_ascii=False), encoding="utf-8")
        os.replace(tmp, path)
    except OSError as e:
        logger.warning("cache WRITE_FAILED url=%s key=%s reason=%s", url, key, type(e).__name__)
        return False
    _metrics["writes"] += 1
    logger.info("cache WRITE url=%s key=%s ttl=%ss", url, key, ttl)
    return True
def invalidate(url: str) -> bool:
    path = _entry_path(key_for_url(url))
    if path.exists():
        _safe_unlink(path)
        _metrics["evictions"] += 1
        logger.info("cache INVALIDATED url=%s", url)
        return True
    return False
def purge_expired(ttl: int = DEFAULT_TTL_SECONDS, now: float | None = None) -> int:
    now = time.time() if now is None else now
    purged = 0
    if not CACHE_DIR.exists():
        return 0
    for path in CACHE_DIR.glob("*.json"):
        try:
            entry = json.loads(path.read_text(encoding="utf-8"))
            if now - float(entry["stored_at"]) >= ttl:
                _safe_unlink(path)
                _metrics["evictions"] += 1
                purged += 1
        except (json.JSONDecodeError, KeyError, TypeError, ValueError, OSError):
            _safe_unlink(path)
            _metrics["evictions"] += 1
            purged += 1
    if purged:
        logger.info("cache PURGE_EXPIRED count=%d ttl=%ss", purged, ttl)
    return purged
def cache_size() -> int:
    if not CACHE_DIR.exists():
        return 0
    return sum(1 for _ in CACHE_DIR.glob("*.json"))
def metrics() -> dict:
    hits = _metrics["hits"]
    misses = _metrics["misses"]
    total = hits + misses
    return {
        "hits": hits,
        "misses": misses,
        "hit_rate": round(hits / total, 4) if total else 0.0,
        "miss_rate": round(misses / total, 4) if total else 0.0,
        "writes": _metrics["writes"],
        "evictions": _metrics["evictions"],
        "content_changes": _metrics["content_changes"],
        "size": cache_size(),
    }
def reset_metrics() -> None:
    for k in _metrics:
        _metrics[k] = 0
