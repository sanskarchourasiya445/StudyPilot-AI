from backend.app.core.config import settings
from backend.app.core.security import create_access_token, decode_access_token, verify_password, get_password_hash


def test_settings_load() -> None:
    assert settings.PROJECT_NAME == "StudyPilot API"
    assert settings.API_V1_STR == "/api"
    assert settings.JWT_ALGORITHM == "HS256"


def test_security_helpers() -> None:
    raw_pwd = "my_secure_password_123"
    hashed = get_password_hash(raw_pwd)
    assert hashed != raw_pwd
    assert verify_password(raw_pwd, hashed) is True
    assert verify_password("wrong_pwd", hashed) is False

    token = create_access_token("user_12345")
    decoded = decode_access_token(token)
    assert decoded is not None
    assert decoded.get("sub") == "user_12345"
