from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, Field

from db.database import get_db
from db.models import User
from auth.auth_utils import hash_password, verify_password, create_token, decode_token

router = APIRouter(prefix="/api/auth", tags=["auth"])
bearer = HTTPBearer()


class RegisterRequest(BaseModel):
    name:     str = Field(..., min_length=2)
    username: str = Field(..., min_length=3)
    email:    str
    password: str = Field(..., min_length=6)

class LoginRequest(BaseModel):
    email:    str
    password: str

class AuthResponse(BaseModel):
    token:    str
    user_id:  int
    name:     str
    email:    str


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def register(body: RegisterRequest, db: AsyncSession = Depends(get_db)):
    r1 = await db.execute(select(User).where(User.username == body.username))
    if r1.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Username already taken")

    r2 = await db.execute(select(User).where(User.email == body.email))
    if r2.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Email already registered")

    user = User(
        name          = body.name,
        username      = body.username,
        email         = body.email,
        password_hash = hash_password(body.password),
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    token = create_token(user.id, user.email, user.name)
    return AuthResponse(token=token, user_id=user.id, name=user.name, email=user.email)


@router.post("/login", response_model=AuthResponse)
async def login(body: LoginRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == body.email))
    user   = result.scalar_one_or_none()

    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    token = create_token(user.id, user.email, user.name)
    return AuthResponse(token=token, user_id=user.id, name=user.name, email=user.email)


@router.get("/me")
async def me(
    credentials: HTTPAuthorizationCredentials = Depends(bearer),
    db: AsyncSession = Depends(get_db),
):
    try:
        payload = decode_token(credentials.credentials)
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))

    result = await db.execute(select(User).where(User.id == int(payload["sub"])))
    user   = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return {"user_id": user.id, "name": user.name, "email": user.email}


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer),
    db: AsyncSession = Depends(get_db),
) -> User:
    try:
        payload = decode_token(credentials.credentials)
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))

    result = await db.execute(select(User).where(User.id == int(payload["sub"])))
    user   = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user