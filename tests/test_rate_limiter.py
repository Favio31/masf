"""Tests para core/rate_limiter.py"""
import time
from unittest.mock import patch
import pytest
from core.rate_limiter import RateLimiter, get_default_limiter, reset_default_limiter
class TestRateLimiter:
    def setup_method(self):
        self.limiter = RateLimiter(min_delay=0.1, max_delay=1.0, backoff_factor=2.0)
    def teardown_method(self):
        self.limiter.reset()
    def test_first_request_no_wait(self):
        """El primer request no debe esperar."""
        start = time.time()
        self.limiter.wait_for_domain("example.com")
        elapsed = time.time() - start
        assert elapsed < 0.05  # menos de 50ms
    def test_second_request_waits(self):
        """El segundo request debe esperar el min_delay."""
        self.limiter.wait_for_domain("example.com")
        self.limiter.record_success("example.com")
        start = time.time()
        self.limiter.wait_for_domain("example.com")
        elapsed = time.time() - start
        assert elapsed >= 0.09  # al menos 90ms (min_delay=0.1)
    def test_backoff_on_429(self):
        """Errores 429 incrementan el backoff."""
        self.limiter.wait_for_domain("example.com")
        self.limiter.record_success("example.com")
        self.limiter.record_error("example.com", 429)
        start = time.time()
        self.limiter.wait_for_domain("example.com")
        elapsed = time.time() - start
        assert elapsed >= 0.19  # min_delay * 2^1 = 0.2s
    def test_backoff_on_503(self):
        """Errores 503 incrementan el backoff."""
        self.limiter.wait_for_domain("example.com")
        self.limiter.record_success("example.com")
        self.limiter.record_error("example.com", 503)
        start = time.time()
        self.limiter.wait_for_domain("example.com")
        elapsed = time.time() - start
        assert elapsed >= 0.19
    def test_success_resets_backoff(self):
        """Un éxito resetea el contador de errores."""
        self.limiter.wait_for_domain("example.com")
        self.limiter.record_success("example.com")
        self.limiter.record_error("example.com", 429)
        self.limiter.record_error("example.com", 429)
        self.limiter.record_success("example.com")  # reset
        start = time.time()
        self.limiter.wait_for_domain("example.com")
        elapsed = time.time() - start
        assert elapsed < 0.15  # menos de 150ms (backoff reseteado)
    def test_max_delay_cap(self):
        """El delay no debe exceder max_delay."""
        self.limiter = RateLimiter(min_delay=1.0, max_delay=2.0, backoff_factor=10.0)
        self.limiter.wait_for_domain("example.com")
        self.limiter.record_success("example.com")
        # Simular muchos errores
        for _ in range(10):
            self.limiter.record_error("example.com", 429)
        start = time.time()
        self.limiter.wait_for_domain("example.com")
        elapsed = time.time() - start
        assert elapsed < 2.5  # menos de 2.5s (max_delay=2.0)
    def test_different_domains_independent(self):
        """Dominios diferentes no se afectan entre sí."""
        self.limiter.wait_for_domain("a.com")
        self.limiter.record_success("a.com")
        self.limiter.wait_for_domain("b.com")  # no debe esperar
        self.limiter.record_success("b.com")
    def test_get_default_limiter(self):
        """get_default_limiter devuelve una instancia compartida."""
        reset_default_limiter()
        limiter1 = get_default_limiter()
        limiter2 = get_default_limiter()
        assert limiter1 is limiter2
    def test_reset_default_limiter(self):
        """reset_default_limiter descarta la instancia compartida."""
        reset_default_limiter()
        limiter1 = get_default_limiter()
        reset_default_limiter()
        limiter2 = get_default_limiter()
        assert limiter1 is not limiter2
