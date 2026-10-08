"""
Esquemas Pydantic específicos por perfil.
Integra las validaciones de fecha, email y URL (REQ-06 a REQ-08).
"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional
import re
from datetime import datetime


def validate_date(value: str) -> bool:
    """Valida formato de fecha ISO 8601 o DD/MM/YYYY."""
    if not value:
        return False
    for fmt in ["%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%Y/%m/%d"]:
        try:
            datetime.strptime(value, fmt)
            return True
        except ValueError:
            continue
    return False


def validate_email(value: str) -> bool:
    """Valida formato de email RFC 5322 (simplificado)."""
    if not value:
        return False
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, value))


def validate_url(value: str) -> bool:
    """Valida formato de URL HTTP/HTTPS."""
    if not value:
        return False
    pattern = r'^https?://[^\s/$.?#].[^\s]*$'
    return bool(re.match(pattern, value))


class SponsorField(BaseModel):
    """Campo individual con validación EARS integrada."""
    value: Optional[str] = None
    quote: Optional[str] = None
    status: str = "missing"
    field_type: str = "text"

    @field_validator('status')
    @classmethod
    def check_status(cls, v: str) -> str:
        if v not in ["verified", "unverified", "missing"]:
            return "unverified"
        return v


class SponsorCardPayload(BaseModel):
    """Esquema completo de una tarjeta de patrocinio."""
    sponsor_name: SponsorField = Field(default_factory=lambda: SponsorField(field_type="text"))
    program_name: SponsorField = Field(default_factory=lambda: SponsorField(field_type="text"))
    amount: SponsorField = Field(default_factory=lambda: SponsorField(field_type="text"))
    deadline: SponsorField = Field(default_factory=lambda: SponsorField(field_type="date"))
    website: SponsorField = Field(default_factory=lambda: SponsorField(field_type="url"))
    email: SponsorField = Field(default_factory=lambda: SponsorField(field_type="email"))
    status: SponsorField = Field(default_factory=lambda: SponsorField(field_type="text"))

    @field_validator('deadline')
    @classmethod
    def validate_date_field(cls, v: SponsorField) -> SponsorField:
        if v.value and not validate_date(v.value):
            v.status = "unverified"
        return v

    @field_validator('email')
    @classmethod
    def validate_email_field(cls, v: SponsorField) -> SponsorField:
        if v.value and not validate_email(v.value):
            v.status = "unverified"
        return v

    @field_validator('website')
    @classmethod
    def validate_url_field(cls, v: SponsorField) -> SponsorField:
        if v.value and not validate_url(v.value):
            v.status = "unverified"
        return v