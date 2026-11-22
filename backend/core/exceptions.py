from typing import Any


class TrazaAgroError(Exception):
    """Excepción base de dominio para TrazaAgro."""

    status_code: int = 500
    error_code: str = "INTERNAL_SERVER_ERROR"

    def __init__(
        self,
        mensaje: str,
        *,
        error_code: str | None = None,
        status_code: int | None = None,
        extra: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(mensaje)
        self.mensaje = mensaje
        if error_code is not None:
            self.error_code = error_code
        if status_code is not None:
            self.status_code = status_code
        self.extra = extra or {}


class ValidationDomainError(TrazaAgroError):
    status_code = 400
    error_code = "VALIDATION_ERROR"


class UnauthorizedError(TrazaAgroError):
    status_code = 401
    error_code = "UNAUTHORIZED"


class ForbiddenError(TrazaAgroError):
    status_code = 403
    error_code = "FORBIDDEN"


class NotFoundError(TrazaAgroError):
    status_code = 404
    error_code = "RESOURCE_NOT_FOUND"


class ConflictError(TrazaAgroError):
    status_code = 409
    error_code = "CONFLICT"


class TooManyRequestsError(TrazaAgroError):
    status_code = 429
    error_code = "TOO_MANY_REQUESTS"


class ServiceUnavailableError(TrazaAgroError):
    status_code = 503
    error_code = "SERVICE_UNAVAILABLE"
