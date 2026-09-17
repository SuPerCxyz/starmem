from __future__ import annotations

import hashlib
import secrets
from datetime import UTC, datetime, timedelta
from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from pwdlib import PasswordHash
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.db import get_db
from app.models import ApiToken, User, UserSession

password_hasher = PasswordHash.recommended()
settings = get_settings()
DbSession = Annotated[Session, Depends(get_db)]


def hash_secret(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def new_secret() -> str:
    return secrets.token_urlsafe(32)


def hash_password(password: str) -> str:
    return password_hasher.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return password_hasher.verify(password, password_hash)


def create_session(db: Session, user: User) -> tuple[str, UserSession]:
    token = new_secret()
    session = UserSession(
        user_id=user.id,
        token_hash=hash_secret(token),
        csrf_token=new_secret(),
        expires_at=datetime.now(UTC) + timedelta(days=30),
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return token, session


def get_current_user(request: Request, db: DbSession) -> User:
    authorization = request.headers.get("Authorization", "")
    if authorization.startswith("Bearer "):
        token_hash = hash_secret(authorization.removeprefix("Bearer ").strip())
        token = db.scalar(
            select(ApiToken).where(ApiToken.token_hash == token_hash, ApiToken.revoked_at.is_(None))
        )
        if token:
            token.last_used_at = datetime.now(UTC)
            db.commit()
            user = db.get(User, token.user_id)
            if user and user.is_active:
                request.state.api_token_auth = True
                return user

    raw_token = request.cookies.get("starmem_session")
    if raw_token:
        session = db.scalar(
            select(UserSession).where(
                UserSession.token_hash == hash_secret(raw_token),
                UserSession.revoked_at.is_(None),
                UserSession.expires_at > datetime.now(UTC),
            )
        )
        if session:
            user = db.get(User, session.user_id)
            if user and user.is_active:
                session.last_used_at = datetime.now(UTC)
                db.commit()
                request.state.session = session
                request.state.api_token_auth = False
                return user

    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")


def require_csrf(request: Request, user: Annotated[User, Depends(get_current_user)]) -> User:
    if getattr(request.state, "api_token_auth", False):
        return user
    session: UserSession | None = getattr(request.state, "session", None)
    csrf_header = request.headers.get("X-CSRF-Token")
    csrf_cookie = request.cookies.get("starmem_csrf")
    if (
        not session
        or not csrf_header
        or not csrf_cookie
        or not secrets.compare_digest(csrf_header, session.csrf_token)
    ):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="CSRF validation failed")
    return user
