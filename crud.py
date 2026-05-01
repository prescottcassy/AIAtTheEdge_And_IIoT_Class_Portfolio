"""
CRUD helpers for glucose readings in the database.
Keeps all DB logic out of the router and simulator.
"""

from sqlalchemy.orm import Session
from typing import Optional

from database import ReadingORM
from models import GlucoseReading


def save_reading(db: Session, reading: GlucoseReading) -> ReadingORM:
    """Persist a GlucoseReading pydantic model to the DB."""
    row = ReadingORM(
        id=reading.id,
        device_id=reading.device_id,
        glucose_mg_dl=reading.glucose_mg_dl,
        glucose_mmol_l=reading.glucose_mmol_l,
        timestamp=reading.timestamp,
        unit=reading.unit,
        status=reading.status,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def orm_to_pydantic(row: ReadingORM) -> GlucoseReading:
    return GlucoseReading(
        id=row.id,
        device_id=row.device_id,
        glucose_mg_dl=row.glucose_mg_dl,
        glucose_mmol_l=row.glucose_mmol_l,
        timestamp=row.timestamp,
        unit=row.unit,
        status=row.status,
    )


def get_readings(
    db: Session,
    device_id: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 50,
) -> list[GlucoseReading]:
    query = db.query(ReadingORM).order_by(ReadingORM.timestamp.desc())
    if device_id:
        query = query.filter(ReadingORM.device_id == device_id)
    if status:
        query = query.filter(ReadingORM.status == status)
    rows = query.limit(limit).all()
    return [orm_to_pydantic(r) for r in reversed(rows)]  # return oldest→newest


def get_reading_by_id(db: Session, reading_id: str) -> Optional[GlucoseReading]:
    row = db.query(ReadingORM).filter(ReadingORM.id == reading_id).first()
    return orm_to_pydantic(row) if row else None


def get_latest_per_device(db: Session) -> list[GlucoseReading]:
    """Return the single most recent reading for each device."""
    from sqlalchemy import func
    subq = (
        db.query(
            ReadingORM.device_id,
            func.max(ReadingORM.timestamp).label("max_ts"),
        )
        .group_by(ReadingORM.device_id)
        .subquery()
    )
    rows = (
        db.query(ReadingORM)
        .join(subq, (ReadingORM.device_id == subq.c.device_id) &
                    (ReadingORM.timestamp == subq.c.max_ts))
        .all()
    )
    return [orm_to_pydantic(r) for r in rows]
