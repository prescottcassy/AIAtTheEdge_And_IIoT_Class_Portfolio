"""
FastAPI Users setup — handles registration, login, JWT, and user management.
Uses SQLAlchemy (same engine as your glucose readings DB).
"""

# --- Standard library ---
import uuid
from typing import AsyncGenerator

# --- FastAPI ---
from fastapi import Depends

# --- FastAPI Users ---
from fastapi_users import BaseUserManager, FastAPIUsers, UUIDIDMixin, schemas
from fastapi_users.authentication import (
    AuthenticationBackend,
    BearerTransport,
    JWTStrategy,
)
from fastapi_users.db import SQLAlchemyUserDatabase

# --- SQLAlchemy (async) ---
from fastapi_users_db_sqlalchemy import SQLAlchemyBaseUserTableUUID
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

# ============================================================
# Config
# ============================================================
SECRET = "change-this-to-a-strong-secret"   # openssl rand -hex 32
DATABASE_URL = "sqlite+aiosqlite:///./glucometer.db"

# ============================================================
# Async engine
# ============================================================
async_engine = create_async_engine(DATABASE_URL)
async_session_maker = async_sessionmaker(async_engine, expire_on_commit=False)

# ============================================================
# ORM — Base + User table
# ============================================================
class Base(DeclarativeBase):
    pass


class User(SQLAlchemyBaseUserTableUUID, Base):
    pass

# ============================================================
# DB session dependency
# ============================================================
async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        yield session


async def get_user_db(session: AsyncSession = Depends(get_async_session)):
    yield SQLAlchemyUserDatabase(session, User)

# ============================================================
# User Manager
# ============================================================
class UserManager(UUIDIDMixin, BaseUserManager[User, uuid.UUID]):
    reset_password_token_secret = SECRET
    verification_token_secret = SECRET


async def get_user_manager(user_db: SQLAlchemyUserDatabase = Depends(get_user_db)):
    yield UserManager(user_db)

# ============================================================
# JWT Auth Backend
# ============================================================
def get_jwt_strategy() -> JWTStrategy:
    return JWTStrategy(secret=SECRET, lifetime_seconds=3600)


bearer_transport = BearerTransport(tokenUrl="/auth/jwt/login")

auth_backend = AuthenticationBackend(
    name="jwt",
    transport=bearer_transport,
    get_strategy=get_jwt_strategy,
)

# ============================================================
# Pydantic schemas
# ============================================================
class UserRead(schemas.BaseUser[uuid.UUID]):
    pass


class UserCreate(schemas.BaseUserCreate):
    pass


class UserUpdate(schemas.BaseUserUpdate):
    pass

# ============================================================
# FastAPIUsers instance
# ============================================================
fastapi_users = FastAPIUsers[User, uuid.UUID](
    get_user_manager,
    [auth_backend],
)

# Dependency — add to any route to require a valid JWT
current_active_user = fastapi_users.current_user(active=True)

# ============================================================
# Create user table on startup
# ============================================================
async def init_user_db():
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
