from datetime import datetime, timedelta, timezone
import secrets
import jwt
from pwdlib import PasswordHash
from fastapi import Depends, HTTPException, Request, Response
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session
from .config import settings
from .db import get_db
from .models import User

password_hash = PasswordHash.recommended()
bearer = HTTPBearer(auto_error=False)
SESSION_COOKIE_NAME = "casework_session"
# Equalize the expensive password-hash path for unknown users to reduce account enumeration.
_DUMMY_PASSWORD_HASH = password_hash.hash("casework-invalid-account-placeholder-password")


def hash_password(password: str) -> str:
    return password_hash.hash(password)


def verify_password(password: str, hashed: str) -> bool:
    return password_hash.verify(password, hashed)


def verify_unknown_account_password(password: str) -> None:
    """Perform the same Argon2 verification cost when an account does not exist."""
    password_hash.verify(password, _DUMMY_PASSWORD_HASH)


def create_token(user: User, csrf_token: str | None = None) -> str:
    now = datetime.now(timezone.utc)
    claims = {"sub": str(user.id), "role": user.role, "ver": user.token_version, "iat": now, "exp": now + timedelta(minutes=settings.token_minutes)}
    if csrf_token is not None:
        claims["csrf"] = csrf_token
    return jwt.encode(claims, settings.jwt_secret, algorithm="HS256")


def set_session_cookie(response: Response, user: User) -> str:
    csrf_token = secrets.token_urlsafe(32)
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=create_token(user, csrf_token),
        max_age=settings.token_minutes * 60,
        path="/api",
        secure=settings.web_origin.startswith("https://"),
        httponly=True,
        samesite="strict",
    )
    return csrf_token


def clear_session_cookie(response: Response) -> None:
    response.delete_cookie(
        key=SESSION_COOKIE_NAME,
        path="/api",
        secure=settings.web_origin.startswith("https://"),
        httponly=True,
        samesite="strict",
    )


def session_csrf_token(request: Request) -> str | None:
    if request.headers.get("authorization"):
        return None
    token = request.cookies.get(SESSION_COOKIE_NAME)
    if not token:
        return None
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])
    except jwt.PyJWTError:
        return None
    csrf_token = payload.get("csrf")
    return csrf_token if isinstance(csrf_token, str) else None


def current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
    db: Session = Depends(get_db),
) -> User:
    cookie_session = credentials is None
    if credentials is not None:
        token = credentials.credentials
    elif request.headers.get("authorization"):
        raise HTTPException(status_code=401, detail="Invalid authorization credentials", headers={"WWW-Authenticate": "Bearer"})
    else:
        token = request.cookies.get(SESSION_COOKIE_NAME, "")
    if not token:
        raise HTTPException(
            status_code=401,
            detail="Authentication credentials are required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])
        user_id = int(payload["sub"])
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired access token", headers={"WWW-Authenticate": "Bearer"})
    if cookie_session and request.method.upper() not in {"GET", "HEAD", "OPTIONS"}:
        expected_csrf = payload.get("csrf")
        supplied_csrf = request.headers.get("X-CSRF-Token", "")
        if not isinstance(expected_csrf, str) or not supplied_csrf or not secrets.compare_digest(expected_csrf, supplied_csrf):
            raise HTTPException(status_code=403, detail="A valid CSRF token is required for this session")
    user = db.get(User, user_id)
    if not user or not user.active:
        raise HTTPException(status_code=401, detail="Account is inactive or unavailable")
    if payload.get("ver") != user.token_version:
        raise HTTPException(status_code=401, detail="Session has been revoked. Sign in again.")
    return user


def require_investigator(user: User = Depends(current_user)) -> User:
    if user.role not in {"investigator", "reviewer", "admin"}:
        raise HTTPException(status_code=403, detail="Investigator access is required")
    return user


def require_reviewer(user: User = Depends(current_user)) -> User:
    if user.role not in {"reviewer", "admin"}:
        raise HTTPException(status_code=403, detail="Authorized reviewer access is required")
    return user
