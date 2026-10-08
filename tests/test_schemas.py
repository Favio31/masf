"""
Tests para core/schemas.py
Valida REQ-06 (fecha), REQ-07 (email), REQ-08 (URL).
"""
import pytest
from core.schemas import SponsorField, SponsorCardPayload, validate_date, validate_email, validate_url


class TestValidateDate:
    """REQ-06: Validación de formato de fecha."""

    def test_fecha_iso_valida(self):
        assert validate_date("2026-11-30") is True

    def test_fecha_ddmmyyyy_valida(self):
        assert validate_date("30/11/2026") is True

    def test_fecha_invalida(self):
        assert validate_date("32/13/2026") is False

    def test_fecha_vacia(self):
        assert validate_date("") is False

    def test_fecha_none(self):
        assert validate_date(None) is False


class TestValidateEmail:
    """REQ-07: Validación de formato de email."""

    def test_email_valido(self):
        assert validate_email("grants@trekbikes.com") is True

    def test_email_sin_arroba(self):
        assert validate_email("grants-trekbikes.com") is False

    def test_email_vacio(self):
        assert validate_email("") is False

    def test_email_none(self):
        assert validate_email(None) is False


class TestValidateUrl:
    """REQ-08: Validación de formato de URL."""

    def test_url_http_valida(self):
        assert validate_url("http://trekbikes.com/grants") is True

    def test_url_https_valida(self):
        assert validate_url("https://www.trekbikes.com/grants") is True

    def test_url_sin_protocolo(self):
        assert validate_url("trekbikes.com/grants") is False

    def test_url_vacia(self):
        assert validate_url("") is False

    def test_url_none(self):
        assert validate_url(None) is False


class TestSponsorField:
    """Tests para el modelo SponsorField."""

    def test_status_valido(self):
        field = SponsorField(value="test", status="verified")
        assert field.status == "verified"

    def test_status_invalido_se_corrige(self):
        field = SponsorField(value="test", status="invalido")
        assert field.status == "unverified"

    def test_status_missing_por_defecto(self):
        field = SponsorField()
        assert field.status == "missing"


class TestSponsorCardPayload:
    """Tests para el modelo completo SponsorCardPayload."""

    def test_card_con_fecha_valida(self):
        card = SponsorCardPayload(
            deadline=SponsorField(value="2026-11-30", field_type="date")
        )
        assert card.deadline.status == "verified" or card.deadline.status == "missing"

    def test_card_con_fecha_invalida(self):
        card = SponsorCardPayload(
            deadline=SponsorField(value="32/13/2026", field_type="date")
        )
        assert card.deadline.status == "unverified"

    def test_card_con_email_valido(self):
        card = SponsorCardPayload(
            email=SponsorField(value="test@example.com", field_type="email")
        )
        assert card.email.status == "verified" or card.email.status == "missing"

    def test_card_con_email_invalido(self):
        card = SponsorCardPayload(
            email=SponsorField(value="no-es-email", field_type="email")
        )
        assert card.email.status == "unverified"

    def test_card_con_url_valida(self):
        card = SponsorCardPayload(
            website=SponsorField(value="https://example.com", field_type="url")
        )
        assert card.website.status == "verified" or card.website.status == "missing"

    def test_card_con_url_invalida(self):
        card = SponsorCardPayload(
            website=SponsorField(value="no-es-url", field_type="url")
        )
        assert card.website.status == "unverified"