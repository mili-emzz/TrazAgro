from datetime import datetime, timedelta, timezone

import jwt
import pytest

from backend.core.config import settings
from backend.core.exceptions import TooManyRequestsError, UnauthorizedError
from backend.core.security import (
    InMemoryRateLimiter,
    ROLE_PRODUCTOR,
    ROLE_QA,
    create_access_token,
    decode_access_token,
    hash_password,
    sanitize_text,
    verify_password,
)


def test_bcrypt_hash_and_verify():
    hashed = hash_password("MiPasswordSegura123!")
    assert hashed.startswith("$2b$12$")
    assert verify_password("MiPasswordSegura123!", hashed) is True
    assert verify_password("PasswordIncorrecta", hashed) is False


def test_jwt_create_and_decode_claims():
    token, expires_in = create_access_token(
        sub="usr-prod-01",
        username="productor_michoacan",
        nombre="Aguacateros Unidos",
        role=ROLE_PRODUCTOR,
        productor_id=1,
    )
    assert expires_in == settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    user = decode_access_token(token)
    assert user.sub == "usr-prod-01"
    assert user.role == ROLE_PRODUCTOR
    assert user.productor_id == 1


def test_jwt_rejects_alg_none():
    unsigned = jwt.encode(
        {
            "sub": "attacker",
            "role": ROLE_QA,
            "iat": int(datetime.now(timezone.utc).timestamp()),
            "exp": int((datetime.now(timezone.utc) + timedelta(hours=1)).timestamp()),
            "jti": "fake-jti",
        },
        key="",
        algorithm="none",
    )
    with pytest.raises(UnauthorizedError):
        decode_access_token(unsigned)


def test_jwt_rejects_expired_token():
    past = datetime.now(timezone.utc) - timedelta(minutes=5)
    expired = jwt.encode(
        {
            "sub": "usr-qa-01",
            "role": ROLE_QA,
            "iat": int((past - timedelta(hours=1)).timestamp()),
            "exp": int(past.timestamp()),
            "jti": "expired-jti",
        },
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )
    with pytest.raises(UnauthorizedError):
        decode_access_token(expired)


def test_jwt_rejects_productor_without_productor_id():
    now = datetime.now(timezone.utc)
    bad = jwt.encode(
        {
            "sub": "usr-prod-x",
            "role": ROLE_PRODUCTOR,
            "productor_id": None,
            "iat": int(now.timestamp()),
            "exp": int((now + timedelta(hours=1)).timestamp()),
            "jti": "no-pid",
        },
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )
    with pytest.raises(UnauthorizedError):
        decode_access_token(bad)


def test_sanitize_text_strips_html_and_script_tags():
    dirty = "  <script>alert('xss')</script><b>Lote contaminado</b> & alerta  "
    cleaned = sanitize_text(dirty)
    assert "<script>" not in cleaned
    assert "<b>" not in cleaned
    assert "Lote contaminado" in cleaned


def test_rate_limiter_blocks_after_threshold():
    limiter = InMemoryRateLimiter(max_requests=3, window_seconds=60)
    limiter.check("ip:1")
    limiter.check("ip:1")
    limiter.check("ip:1")
    with pytest.raises(TooManyRequestsError):
        limiter.check("ip:1")
