"""
Database setup — SQLite via SQLAlchemy (sync, lightweight).
Only glucose readings are persisted to the DB.
Devices and alerts remain in-memory (store.py).

To switch to PostgreSQL later, change DATABASE_URL to:
  postgresql://user:password@localhost/glucometer
and install psycopg2-binary.
"""

from sqlalchemy import (
    create_engine, Column, String, Float, DateTime, text
)
from sqlalchemy.orm import DeclarativeBase, sessionmaker, Session
from datetime import datetime
import uuid

DATABASE_URL = "sqlite:///./glucometer.db"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},  # needed for SQLite only
)

SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


class Base(DeclarativeBase):
    pass


class ReadingORM(Base):
    __tablename__ = "glucose_readings"

    id             = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    device_id      = Column(String, nullable=False, index=True)
    glucose_mg_dl  = Column(Float, nullable=False)
    glucose_mmol_l = Column(Float, nullable=False)
    timestamp      = Column(DateTime, default=datetime.utcnow, index=True)
    unit           = Column(String, default="mg/dL")
    status         = Column(String, nullable=False)


def init_db():
    """Create tables if they don't exist."""
    Base.metadata.create_all(bind=engine)


def get_db():
    """FastAPI dependency — yields a DB session and closes it after the request."""
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()
