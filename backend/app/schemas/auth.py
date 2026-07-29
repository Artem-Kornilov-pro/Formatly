import re

from pydantic import BaseModel, EmailStr, Field, field_validator

_SPECIAL_CHARACTER_RE = re.compile(r"[^A-Za-z0-9]")


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)

    @field_validator("password")
    @classmethod
    def _require_special_character(cls, value: str) -> str:
        if not _SPECIAL_CHARACTER_RE.search(value):
            raise ValueError("Password must contain at least one special character")
        return value


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class UserOut(BaseModel):
    id: str
    email: str
