from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.user import User
from app.schemas.auth import (
    UserRegister,
    UserLogin,
    TokenResponse,
    UserResponse,
)
from app.services.auth import (
    hash_password,
    verify_password,
    create_access_token,
)


router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)


@router.post(
    "/register",
    response_model=UserResponse
)
def register_user(
    user_data: UserRegister,
    db: Session = Depends(get_db)
):
    """
    Register a new investigator account.
    """

    existing_user = (
        db.query(User)
        .filter(User.username == user_data.username)
        .first()
    )

    if existing_user is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists"
        )

    new_user = User(
        username=user_data.username,
        password_hash=hash_password(
            user_data.password
        ),
        role="investigator",
        is_active=True
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {
        "id": str(new_user.id),
        "username": new_user.username,
        "role": new_user.role,
        "is_active": new_user.is_active,
    }


@router.post(
    "/login",
    response_model=TokenResponse
)
def login_user(
    user_data: UserLogin,
    db: Session = Depends(get_db)
):
    """
    Authenticate a user and return a JWT token.
    """

    user = (
        db.query(User)
        .filter(User.username == user_data.username)
        .first()
    )

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password"
        )

    if not verify_password(
        user_data.password,
        user.password_hash
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password"
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )

    access_token = create_access_token(
        data={
            "sub": str(user.id),
            "username": user.username,
            "role": user.role,
        }
    )

    return {
        "access_token": access_token,
        "token_type": "bearer"
    }