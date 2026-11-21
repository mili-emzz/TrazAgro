from pydantic import BaseModel


class MotorStatus(BaseModel):
    status: str
    detail: str | None = None


class HealthResponse(BaseModel):
    service: str
    version: str
    status: str
    databases: dict[str, MotorStatus]
