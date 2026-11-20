from fastapi import APIRouter, Depends, HTTPException, status, Response, Cookie
from sqlalchemy.orm import Session

from app.REST.data.database import get_db
from app.identity.model.auth_schema import (
    LoginRequest,
    LoginResponse,
    UserCreate,
    UserResponse,
)
from app.identity.service.auth_errors import (
    AuthenticationError,
    AuthorizationError,
    UserAlreadyExistsError,
)
from app.identity.service.auth_service import (
    SESSION_MAX_AGE_SECONDS,
    get_current_user,
    login_user,
    logout_user,
    register_user,
)
from app.REST.service.products.product_validators import ValidationError

router = APIRouter(tags=["Identity"])


@router.post(
    "/auth/register",
    response_model=LoginResponse,
    status_code=status.HTTP_201_CREATED,
)
def register_endpoint(payload: UserCreate, response: Response, db: Session = Depends(get_db)):
    try:
        user, session_token = register_user(
            db=db,
            email=payload.email,
            password=payload.password,
        )
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except UserAlreadyExistsError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    response.set_cookie(
        key="auth_token",
        value=session_token,
        httponly=True,
        samesite="lax",
        secure=False,
        max_age=SESSION_MAX_AGE_SECONDS,
    )
    return LoginResponse(user=user)


@router.post("/auth/login", response_model=LoginResponse)
def login_endpoint(
    payload: LoginRequest,
    response: Response,
    auth_token: str | None = Cookie(default=None),
    db: Session = Depends(get_db),
):
    try:
        if auth_token is not None:
            logout_user(db, auth_token)

        user, session_token = login_user(
            db=db,
            email=payload.email,
            password=payload.password,
        )

        response.set_cookie(
            key="auth_token",
            value=session_token,
            httponly=True,
            samesite="lax",
            secure=False,
            max_age=SESSION_MAX_AGE_SECONDS,
        )

        return LoginResponse(user=user)

    except AuthenticationError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except AuthorizationError as e:
        raise HTTPException(status_code=403, detail=str(e))

@router.get("/auth/me", response_model=UserResponse, status_code=status.HTTP_200_OK)
def me_endpoint(
    response: Response,
    auth_token: str | None = Cookie(default=None),
    db: Session = Depends(get_db)
):
    if auth_token is None:
        raise HTTPException(status_code=401, detail="Brak aktywnej sesji.")

    try:
        user = get_current_user(db, auth_token)
        response.set_cookie(
            key="auth_token",
            value=auth_token,
            httponly=True,
            samesite="lax",
            secure=False,
            max_age=SESSION_MAX_AGE_SECONDS,
        )

        return user
    except AuthorizationError as e:
        raise HTTPException(status_code=401, detail=str(e))

@router.post("/auth/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout_endpoint(
    response: Response,
    auth_token: str | None = Cookie(default=None),
    db: Session = Depends(get_db),
):
    if auth_token is not None:
        logout_user(db, auth_token)

    response.delete_cookie(
        key="auth_token",
        httponly=True,
        samesite="lax",
        secure=False,
    )

    response.status_code = 204
    return response