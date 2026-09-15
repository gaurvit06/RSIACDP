from pydantic import BaseModel


class UserRegister(BaseModel):
    username: str
    password: str


class UserLogin(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str


class UserResponse(BaseModel):
    id: str
    username: str
    role: str
    is_active: bool