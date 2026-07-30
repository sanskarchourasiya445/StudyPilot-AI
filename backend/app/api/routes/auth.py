from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from backend.app.api.deps import get_current_user, get_db
from backend.app.core.security import create_access_token
from backend.app.db.models.user import User
from backend.app.schemas.auth import Token, UserLogin, UserRead, UserRegister
from backend.app.services.auth_service import AuthService, DuplicateUserError

router = APIRouter(prefix="/auth", tags=["Authentication"])
auth_service = AuthService()


@router.post(
    "/register",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
    description="Register a new student user with email, password, and optional name.",
)
def register(
    user_in: UserRegister,
    db: Session = Depends(get_db),
) -> Any:
    try:
        user = auth_service.register_user(db, user_in)
        return user
    except DuplicateUserError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


@router.post(
    "/login",
    response_model=Token,
    summary="User login (JSON or Form)",
    description="Authenticate user and return a JWT access token.",
)
def login(
    user_in: UserLogin,
    db: Session = Depends(get_db),
) -> Any:
    user = auth_service.authenticate_user(db, user_in.email, user_in.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(subject=user.id)
    return Token(access_token=access_token, token_type="bearer")


@router.post(
    "/login/form",
    response_model=Token,
    summary="OAuth2 Form Login (for Swagger UI)",
    include_in_schema=False,
)
def login_form(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
) -> Any:
    user = auth_service.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(subject=user.id)
    return Token(access_token=access_token, token_type="bearer")


@router.get(
    "/me",
    response_model=UserRead,
    summary="Get current user profile",
    description="Retrieve profile details for the authenticated user.",
)
def read_user_me(
    current_user: User = Depends(get_current_user),
) -> Any:
    return current_user
