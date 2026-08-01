import uuid

from pydantic import BaseModel, EmailStr


class SignupRequest(BaseModel):
    email: EmailStr
    password: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class GoogleLoginRequest(BaseModel):
    id_token: str


class UserPublic(BaseModel):
    id: uuid.UUID
    email: EmailStr
    plan: str

    model_config = {"from_attributes": True}
