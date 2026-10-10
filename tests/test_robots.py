"""Tests para core/robots.py"""
from unittest.mock import patch, MagicMock
import pytest
from core.robots import RobotsChecker, get_default_checker, reset_default_checker
class TestRobotsChecker:
    def setup_method(self):
        self.checker = RobotsChecker(user_agent="*")
    def teardown_method(self):
        self.checker.clear_cache()
    @patch("core.robots.RobotFileParser")
    def test_is_allowed_when_robots_allows(self, mock_rp_class):
        """Cuando robots.txt permite, is_allowed devuelve True."""
        mock_rp = MagicMock()
        mock_rp.can_fetch.return_value = True
        mock_rp_class.return_value = mock_rp
        assert self.checker.is_allowed("https://example.com/page") is True
        mock_rp.can_fetch.assert_called_once_with("*", "https://example.com/page")
    @patch("core.robots.RobotFileParser")
    def test_is_blocked_when_robots_denies(self, mock_rp_class):
        """Cuando robots.txt bloquea, is_allowed devuelve False."""
        mock_rp = MagicMock()
        mock_rp.can_fetch.return_value = False
        mock_rp_class.return_value = mock_rp
        assert self.checker.is_allowed("https://example.com/admin") is False
    @patch("core.robots.RobotFileParser")
    def test_robots_load_failure_allows_all(self, mock_rp_class):
        """Si robots.txt falla al cargar, se permite todo (fail-open)."""
        mock_rp = MagicMock()
        mock_rp.read.side_effect = Exception("Network error")
        # Configurar can_fetch para devolver True (fail-open behavior)
        mock_rp.can_fetch.return_value = True
        mock_rp_class.return_value = mock_rp
        assert self.checker.is_allowed("https://example.com/page") is True
    @patch("core.robots.RobotFileParser")
    def test_crawl_delay_returned(self, mock_rp_class):
        """get_crawl_delay devuelve el valor de robots.txt."""
        mock_rp = MagicMock()
        mock_rp.crawl_delay.return_value = 5.0
        mock_rp_class.return_value = mock_rp
        self.checker.is_allowed("https://example.com/page")  # cargar cache
        delay = self.checker.get_crawl_delay("https://example.com/page")
        assert delay == 5.0
    @patch("core.robots.RobotFileParser")
    def test_crawl_delay_none_when_not_set(self, mock_rp_class):
        """get_crawl_delay devuelve None si no hay Crawl-delay."""
        mock_rp = MagicMock()
        mock_rp.crawl_delay.return_value = None
        mock_rp_class.return_value = mock_rp
        self.checker.is_allowed("https://example.com/page")
        delay = self.checker.get_crawl_delay("https://example.com/page")
        assert delay is None
    def test_clear_cache(self):
        """clear_cache elimina todas las entradas."""
        self.checker._cache["example.com"] = "dummy"
        self.checker.clear_cache()
        assert len(self.checker._cache) == 0
    def test_get_default_checker(self):
        """get_default_checker devuelve una instancia compartida."""
        reset_default_checker()
        checker1 = get_default_checker()
        checker2 = get_default_checker()
        assert checker1 is checker2
    def test_reset_default_checker(self):
        """reset_default_checker descarta la instancia compartida."""
        reset_default_checker()
        checker1 = get_default_checker()
        reset_default_checker()
        checker2 = get_default_checker()
        assert checker1 is not checker2
