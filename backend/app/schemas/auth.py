import uuid

from pydantic import BaseModel

from app.schemas.common import ORMModel


class LoginRequest(BaseModel):
    email: str
    password: str


class TokenUser(ORMModel):
    id: uuid.UUID
    email: str
    role: str
    company_id: uuid.UUID | None = None


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: TokenUser


class TokenPairResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str


class LogoutRequest(BaseModel):
    refresh_token: str
