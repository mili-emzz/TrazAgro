from fastapi import APIRouter, Depends

from backend.core.security import rate_limit_login
from backend.schemas.auth import LoginRequest, LoginResponse
from backend.services.auth_service import AuthService

router = APIRouter(prefix="/api/v1/auth", tags=["Autenticación"])


@router.post(
    "/login",
    response_model=LoginResponse,
    dependencies=[Depends(rate_limit_login)],
)
def login(payload: LoginRequest) -> LoginResponse:
    """Autentica un usuario operativo y emite un token JWT firmado con HS256."""
    service = AuthService()
    result = service.authenticate(payload.username, payload.password)
    return LoginResponse(**result)
