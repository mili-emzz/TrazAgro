from collections import defaultdict, deque
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import html
import re
import time
from typing import Callable
import uuid

import bcrypt
from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
import jwt
from jwt.exceptions import InvalidTokenError

from backend.core.config import settings
from backend.core.exceptions import (
    ForbiddenError,
    TooManyRequestsError,
    UnauthorizedError,
)

# Roles oficiales del MVP de TrazaAgro
ROLE_PRODUCTOR = "Productor"
ROLE_RECEPCION = "Recepcion"
ROLE_LABORATORIO = "Laboratorio"
ROLE_QA = "QA"

VALID_ROLES = {ROLE_PRODUCTOR, ROLE_RECEPCION, ROLE_LABORATORIO, ROLE_QA}

bearer_scheme = HTTPBearer(auto_error=False)

_SCRIPT_TAG_RE = re.compile(r"<\s*/?\s*script[^>]*>", re.IGNORECASE)
_HTML_TAG_RE = re.compile(r"<[^>]+>")


@dataclass(frozen=True)
class CurrentUser:
    """Usuario autenticado extraído desde el token JWT verificado."""

    sub: str
    username: str
    nombre: str
    role: str
    productor_id: int | None = None


def hash_password(plain_password: str) -> str:
    """Genera hash bcrypt con factor de costo de 12 rondas."""
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(plain_password.encode("utf-8"), salt).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Compara contraseña en tiempo constante usando bcrypt.checkpw."""
    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"),
            hashed_password.encode("utf-8"),
        )
    except ValueError:
        return False


def create_access_token(
    *,
    sub: str,
    username: str,
    nombre: str,
    role: str,
    productor_id: int | None = None,
) -> tuple[str, int]:
    """Emite un JWT firmado con HS256 y expiración finita."""
    if role not in VALID_ROLES:
        raise ValueError(f"Rol no reconocido: {role}")

    now = datetime.now(timezone.utc)
    expires_seconds = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    exp = now + timedelta(seconds=expires_seconds)

    payload = {
        "sub": sub,
        "username": username,
        "nombre": nombre,
        "role": role,
        "productor_id": productor_id if role == ROLE_PRODUCTOR else None,
        "iat": int(now.timestamp()),
        "exp": int(exp.timestamp()),
        "jti": uuid.uuid4().hex,
    }
    token = jwt.encode(
        payload,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )
    return token, expires_seconds


def decode_access_token(token: str) -> CurrentUser:
    """Valida firma, algoritmo HS256 y claims obligatorios de un JWT."""
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
            options={"require": ["sub", "role", "exp", "iat", "jti"]},
        )
    except InvalidTokenError as exc:
        raise UnauthorizedError("Token inválido o expirado.") from exc

    role = payload.get("role")
    if role not in VALID_ROLES:
        raise UnauthorizedError("El token contiene un rol inválido.")

    productor_id = payload.get("productor_id")
    if role == ROLE_PRODUCTOR and productor_id is None:
        raise UnauthorizedError("El token de Productor carece de productor_id.")

    return CurrentUser(
        sub=str(payload["sub"]),
        username=str(payload.get("username", payload["sub"])),
        nombre=str(payload.get("nombre", payload["sub"])),
        role=role,
        productor_id=int(productor_id) if productor_id is not None else None,
    )


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> CurrentUser:
    """Dependencia FastAPI que exige un Bearer JWT válido."""
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise UnauthorizedError("Se requiere encabezado Authorization: Bearer <token>.")
    return decode_access_token(credentials.credentials)


def require_roles(*allowed_roles: str) -> Callable[[CurrentUser], CurrentUser]:
    """Dependencia RBAC que restringe el acceso a los roles permitidos."""
    allowed = set(allowed_roles)

    def _checker(current_user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
        if current_user.role not in allowed:
            raise ForbiddenError(
                f"El rol '{current_user.role}' no tiene permisos para esta operación."
            )
        return current_user

    return _checker


def sanitize_text(value: str | None) -> str | None:
    """Limpia etiquetas HTML/script en campos de texto libre para prevenir XSS."""
    if value is None:
        return None
    cleaned = _SCRIPT_TAG_RE.sub("", value)
    cleaned = _HTML_TAG_RE.sub("", cleaned)
    return html.escape(cleaned.strip(), quote=False)


class InMemoryRateLimiter:
    """Limitador de tasa en memoria por ventana deslizante (IP + ruta)."""

    def __init__(self, max_requests: int, window_seconds: int) -> None:
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._hits: dict[str, deque[float]] = defaultdict(deque)

    def check(self, key: str) -> None:
        now = time.monotonic()
        bucket = self._hits[key]
        cutoff = now - self.window_seconds
        while bucket and bucket[0] <= cutoff:
            bucket.popleft()
        if len(bucket) >= self.max_requests:
            raise TooManyRequestsError(
                "Demasiadas solicitudes en un periodo corto. Intenta nuevamente en unos segundos."
            )
        bucket.append(now)

    def reset(self) -> None:
        self._hits.clear()


login_rate_limiter = InMemoryRateLimiter(max_requests=10, window_seconds=60)
recall_rate_limiter = InMemoryRateLimiter(max_requests=5, window_seconds=60)


def rate_limit_login(request: Request) -> None:
    client_ip = request.client.host if request.client else "unknown"
    login_rate_limiter.check(f"login:{client_ip}")


def rate_limit_recall(request: Request) -> None:
    client_ip = request.client.host if request.client else "unknown"
    recall_rate_limiter.check(f"recall:{client_ip}")
