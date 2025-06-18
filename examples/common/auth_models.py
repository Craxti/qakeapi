from pydantic import BaseModel

class UserResponse(BaseModel):
    username: str
    roles: list[str]

class TokenResponse(BaseModel):
    access_token: str
    token_type: str

class LoginRequest(BaseModel):
    username: str
    password: str 