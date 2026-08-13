import logging
import aiosqlite
from pathlib import Path

logger = logging.getLogger(__name__)

async def init_db(db_path: str) -> aiosqlite.Connection:
    """Открывает соединение, включает WAL, применяет миграции."""
    logger.info(f"Connecting to database at {db_path}")
    conn = await aiosqlite.connect(db_path)
    
    # Включаем WAL
    await conn.execute("PRAGMA journal_mode=WAL")
    
    schema_path = Path(__file__).parent / "schema.sql"
    with open(schema_path, "r", encoding="utf-8") as f:
        schema = f.read()
        
    logger.info("Applying schema (IF NOT EXISTS)...")
    await conn.executescript(schema)
    await conn.commit()
    
    logger.info("Database initialized successfully.")
    return conn

async def close_db(conn: aiosqlite.Connection):
    """Корректное закрытие БД."""
    if conn:
        logger.info("Closing database connection...")
        await conn.close()
        logger.info("Database connection closed.")
