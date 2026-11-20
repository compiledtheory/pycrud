SESSION_MAX_AGE_SECONDS = 1800

import secrets
import re
from datetime import datetime, timedelta
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.identity.data.auth_repository import (
    add_session,
    add_user,
    delete_session_by_id,
    get_session_by_token,
    get_user_by_email,
    get_user_by_id,
    update_session_last_used,
)
from app.identity.model.user_orm import UserORM
from app.identity.model.user_session_orm import UserSessionORM
from app.identity.service.auth_errors import (
    AuthenticationError,
    AuthorizationError,
    UserAlreadyExistsError,
)
from app.identity.service.auth_validators import validate_password_strength
from app.identity.service.password_hasher import hash_password, verify_password
from app.REST.service.products.product_validators import ValidationError


def is_session_expired(last_used_at: datetime) -> bool:
    return datetime.now() - last_used_at > timedelta(seconds=SESSION_MAX_AGE_SECONDS)


def login_user(db: Session, email: str, password: str) -> tuple[UserORM, str]:
    user = get_user_by_email(db, email.strip())
    if user is None or not verify_password(password, user.password_hash):
        raise AuthenticationError("Nieprawidłowy e-mail lub hasło.")
    if not user.is_active:
        raise AuthorizationError("Konto użytkownika nieaktywne.")

    session_token = secrets.token_urlsafe(32)
    add_session(
        db,
        UserSessionORM(user_id=user.id, session_token=session_token),
    )
    return user, session_token


def register_user(db: Session, email: str, password: str) -> tuple[UserORM, str]:
    normalized_email = email.strip().lower()
    if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", normalized_email):
        raise ValidationError("E-mail ma nieprawidłowy format.")
    validate_password_strength(password)
    if get_user_by_email(db, normalized_email) is not None:
        raise UserAlreadyExistsError("Użytkownik o podanym adresie e-mail już istnieje.")

    user = UserORM(
        email=normalized_email,
        password_hash=hash_password(password),
        is_active=True,
    )
    try:
        add_user(db, user)
    except IntegrityError as exc:
        raise UserAlreadyExistsError(
            "Użytkownik o podanym adresie e-mail już istnieje."
        ) from exc

    session_token = secrets.token_urlsafe(32)
    add_session(db, UserSessionORM(user_id=user.id, session_token=session_token))
    return user, session_token


def get_current_user(db: Session, session_token: str) -> UserORM:
    if (session := get_session_by_token(db, session_token)) is None:
        raise AuthorizationError("Brak aktywnej sesji.")

    if is_session_expired(session.last_used_at):
        delete_session_by_id(db, session.id)
        raise AuthorizationError("Sesja wygasła")

    if (user := get_user_by_id(db, session.user_id)) is None:
        delete_session_by_id(db, session.id)
        raise AuthorizationError("Użytkownik przypisany do sesji nie istnieje.")

    if not user.is_active:
        delete_session_by_id(db, session.id)
        raise AuthorizationError("Konto użytkownika nieaktywne.")

    update_session_last_used(db, session)
    return user


def logout_user(db: Session, session_token: str) -> None:
    session = get_session_by_token(db, session_token)
    if session is not None:
        delete_session_by_id(db, session.id)