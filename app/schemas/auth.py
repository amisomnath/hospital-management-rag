"""Authentication request and response schemas."""

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class RegisterRequest(BaseModel):
    """Information required to create a user."""

    email: EmailStr
    full_name: str = Field(min_length=2, max_length=150)
    password: str = Field(min_length=8, max_length=128)
    role: str = Field(default="staff", max_length=30)


class LoginRequest(BaseModel):
    """Email/password login payload."""

    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    """JWT bearer-token response."""

    access_token: str
    token_type: str = "bearer"


class AuthenticatedUser(BaseModel):
    """Safe user information decoded for API clients."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    email: EmailStr
    full_name: str
    role: str
    is_active: bool
