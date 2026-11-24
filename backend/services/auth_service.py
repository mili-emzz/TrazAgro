from dataclasses import dataclass

from backend.core.exceptions import UnauthorizedError
from backend.core.security import (
    ROLE_LABORATORIO,
    ROLE_PRODUCTOR,
    ROLE_QA,
    ROLE_RECEPCION,
    create_access_token,
    hash_password,
    verify_password,
)


@dataclass(frozen=True)
class OperationalUser:
    sub: str
    username: str
    nombre: str
    role: str
    password_hash: str
    productor_id: int | None = None


def _build_demo_users() -> dict[str, OperationalUser]:
    """Catálogo de usuarios operativos del MVP con contraseñas protegidas mediante bcrypt (12 rondas)."""
    seeds = [
        ("usr-qa-01", "qa_admin", "Ing. Valeria Mendoza (QA)", ROLE_QA, "TrazaQA2026!", None),
        ("usr-rec-01", "recepcion_cedis", "Carlos Herrera (CEDIS)", ROLE_RECEPCION, "TrazaRec2026!", None),
        ("usr-lab-01", "lab_agrobio", "Q.F.B. Sofía Ríos (Lab AgroBio)", ROLE_LABORATORIO, "TrazaLab2026!", None),
        ("usr-prod-01", "productor_michoacan", "Aguacateros Unidos de Michoacán", ROLE_PRODUCTOR, "TrazaProd1!", 1),
        ("usr-prod-02", "productor_tancitaro", "Huertas del Tancítaro", ROLE_PRODUCTOR, "TrazaProd2!", 2),
    ]
    return {
        username: OperationalUser(
            sub=sub,
            username=username,
            nombre=nombre,
            role=role,
            password_hash=hash_password(password),
            productor_id=productor_id,
        )
        for sub, username, nombre, role, password, productor_id in seeds
    }


_USERS_CACHE: dict[str, OperationalUser] | None = None


def _get_users() -> dict[str, OperationalUser]:
    global _USERS_CACHE
    if _USERS_CACHE is None:
        _USERS_CACHE = _build_demo_users()
    return _USERS_CACHE


class AuthService:
    """Servicio de autenticación JWT para los 4 actores del MVP."""

    def authenticate(self, username: str, password: str) -> dict:
        user = _get_users().get(username.strip())
        if user is None or not verify_password(password, user.password_hash):
            # Mensaje genérico para evitar enumeración de usuarios
            raise UnauthorizedError("Credenciales incorrectas.")

        token, expires_in = create_access_token(
            sub=user.sub,
            username=user.username,
            nombre=user.nombre,
            role=user.role,
            productor_id=user.productor_id,
        )
        return {
            "access_token": token,
            "token_type": "bearer",
            "expires_in": expires_in,
            "user": {
                "sub": user.sub,
                "username": user.username,
                "nombre": user.nombre,
                "role": user.role,
                "productor_id": user.productor_id,
            },
        }
