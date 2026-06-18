from pydantic import BaseModel, EmailStr
from typing import Optional


class UserRegisterDTO(BaseModel):
    username: str
    email: EmailStr
    password: str


class UserLoginDTO(BaseModel):
    username: str
    password: str


class UserResponse(BaseModel):
    userId: int
    username: str
    email: str
    role: str

    class Config:
        from_attributes = True


class AuthResponseData(BaseModel):
    accessToken: str
    user: UserResponse


class AuthResponse(BaseModel):
    status: str
    message: str
    data: Optional[AuthResponseData] = None
