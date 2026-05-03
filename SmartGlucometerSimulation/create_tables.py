"""
Run this once to create all tables including the user table.
Usage: python3 create_tables.py
"""
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from users import Base

DATABASE_URL = "sqlite+aiosqlite:///./glucometer.db"

async def create_all():
    engine = create_async_engine(DATABASE_URL)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await engine.dispose()
    print("✓ All tables created successfully")

    # Verify
    from sqlalchemy import text
    async with engine.connect() as conn:
        result = await conn.execute(text("SELECT name FROM sqlite_master WHERE type='table'"))
        tables = [row[0] for row in result]
        print(f"✓ Tables in DB: {tables}")

asyncio.run(create_all())
