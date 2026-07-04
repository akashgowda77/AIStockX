from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..dependencies import get_db, get_current_user
from ..models.user import User
from ..schemas.auth import (
    Token,
    UserCreate,
    UserLogin,
    UserResponse,
)
from ..services.auth_service import (
    create_access_token,
    hash_password,
    verify_password,
)

router = APIRouter(
    prefix="",
    tags=["Authentication"],
)


@router.post("/register", response_model=UserResponse)
def register(
    user_in: UserCreate,
    db: Session = Depends(get_db),
):
    """Register a new user."""

    existing_user = (
        db.query(User)
        .filter(
            (User.username == user_in.username)
            | (User.email == user_in.email)
        )
        .first()
    )

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username or email already exists.",
        )

    user = User(
        username=user_in.username,
        email=user_in.email,
        password_hash=hash_password(user_in.password),
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user


from fastapi.security import OAuth2PasswordRequestForm


@router.post("/login", response_model=Token)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    """Authenticate a user and return a JWT."""

    user = (
        db.query(User)
        .filter(
            (User.username == form_data.username)
            | (User.email == form_data.username)
        )
        .first()
    )

    if (
        user is None
        or not verify_password(
            form_data.password,
            user.password_hash,
        )
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username/email or password.",
        )

    access_token = create_access_token(
        user_id=user.id,
        email=user.email,
    )

    return Token(
        access_token=access_token,
        token_type="bearer",
    )


@router.get("/me", response_model=UserResponse)
def get_profile(
    current_user: User = Depends(get_current_user),
):
    """Return the authenticated user's profile."""

    return current_user