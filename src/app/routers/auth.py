"""Authentication endpoints."""
from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel

from src.app.auth import (
    authenticate_user,
    create_user,
    AuthenticationError,
    hash_password,
    _DEFAULT_USER_STORE,
)
from src.app.jwt_auth import (
    Token,
    create_access_token,
    create_refresh_token,
    get_current_active_user,
)
from src.app.rate_limit import rate_limit

router = APIRouter(prefix="/api/auth", tags=["auth"])


class LoginRequest(BaseModel):
    username: str
    password: str


class RegisterRequest(BaseModel):
    username: str
    password: str


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class UserResponse(BaseModel):
    username: str
    is_active: bool


@router.post("/register", response_model=Token)
async def register(request: RegisterRequest) -> Token:
    """Register a new user and return access/refresh tokens."""
    try:
        user = create_user(
            request.username,
            request.password,
            store=_DEFAULT_USER_STORE,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    access_token = create_access_token(data={"sub": user.username})
    refresh_token = create_refresh_token(data={"sub": user.username})

    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
    )


@router.post("/login", response_model=Token)
@rate_limit(requests=5, period_seconds=60)
async def login(request: LoginRequest, current_user: str = None) -> Token:
    """Authenticate user and return access/refresh tokens."""
    try:
        user = authenticate_user(
            request.username,
            request.password,
            store=_DEFAULT_USER_STORE,
        )
    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(data={"sub": user.username})
    refresh_token = create_refresh_token(data={"sub": user.username})

    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
    )


@router.post("/refresh", response_model=Token)
async def refresh_token(request: RefreshTokenRequest) -> Token:
    """Refresh access token using a refresh token."""
    try:
        from jose import jwt
        from src.app.config import settings

        payload = jwt.decode(
            request.refresh_token,
            settings.SECRET_KEY,
            algorithms=["HS256"],
        )
        username: str = payload.get("sub")
        if username is None or payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token",
            )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )

    access_token = create_access_token(data={"sub": username})
    new_refresh_token = create_refresh_token(data={"sub": username})

    return Token(
        access_token=access_token,
        refresh_token=new_refresh_token,
    )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: str = Depends(get_current_active_user),
) -> UserResponse:
    """Get current authenticated user info."""
    from src.app.auth import get_user

    user = get_user(current_user, store=_DEFAULT_USER_STORE)
    return UserResponse(
        username=user.username,
        is_active=user.is_active,
    )
