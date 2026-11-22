from pydantic import BaseModel, ConfigDict, Field


class LoginRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    username: str = Field(..., min_length=3, max_length=60)
    password: str = Field(..., min_length=6, max_length=128)


class UserProfile(BaseModel):
    sub: str
    username: str
    nombre: str
    role: str
    productor_id: int | None = None


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserProfile
