from datetime import datetime

from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.identity.model.user_orm import UserORM
from app.identity.model.user_session_orm import UserSessionORM


def get_user_by_email(db: Session, email: str) -> UserORM | None:
    return db.query(UserORM).filter(func.lower(UserORM.email) == email.lower()).first()


def add_user(db: Session, user: UserORM) -> UserORM:
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise
    db.refresh(user)
    return user


def get_user_by_id(db: Session, user_id: int) -> UserORM | None:
    return db.query(UserORM).filter(UserORM.id == user_id).first()


def get_session_by_token(db: Session, session_token: str) -> UserSessionORM | None:
    return (
        db.query(UserSessionORM)
        .filter(UserSessionORM.session_token == session_token)
        .first()
    )


def add_session(db: Session, session: UserSessionORM) -> UserSessionORM:
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


def delete_session_by_id(db: Session, session_id: int) -> None:
    session = db.query(UserSessionORM).filter(UserSessionORM.id == session_id).first()
    if session is not None:
        db.delete(session)
        db.commit()


def update_session_last_used(db: Session, session: UserSessionORM) -> None:
    session.last_used_at = datetime.now()
    db.commit()