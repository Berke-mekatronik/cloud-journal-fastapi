import os
import uuid
import asyncpg
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from dotenv import load_dotenv
from api.repositories.interface_respository import DatabaseInterface

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable is missing")


class PostgresDB(DatabaseInterface):
    def __init__(self):
        self.pool: Optional[asyncpg.Pool] = None

    async def __aenter__(self):
        self.pool = await asyncpg.create_pool(DATABASE_URL)
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        if self.pool:
            await self.pool.close()

    async def create_entry(self, entry_data: Dict[str, Any]) -> None:
        async with self.pool.acquire() as conn:
            query = """
            INSERT INTO entries (id, work, struggle, intention, created_at, updated_at)
            VALUES ($1, $2, $3, $4, $5, $6)
            """

            entry_id = entry_data.get("id") or uuid.uuid4()
            created_at = entry_data.get("created_at") or datetime.now(timezone.utc)
            updated_at = entry_data.get("updated_at") or created_at

            await conn.execute(
                query,
                entry_id,
                entry_data["work"],
                entry_data["struggle"],
                entry_data["intention"],
                created_at,
                updated_at,
            )

    async def get_entries(self) -> List[Dict[str, Any]]:
        async with self.pool.acquire() as conn:
            query = "SELECT * FROM entries ORDER BY created_at DESC"
            rows = await conn.fetch(query)

            return [
                {
                    "id": str(row["id"]),
                    "work": row["work"],
                    "struggle": row["struggle"],
                    "intention": row["intention"],
                    "created_at": row["created_at"],
                    "updated_at": row["updated_at"],
                }
                for row in rows
            ]

    async def get_entry(self, entry_id: str) -> Optional[Dict[str, Any]]:
        async with self.pool.acquire() as conn:
            query = "SELECT * FROM entries WHERE id = $1"
            row = await conn.fetchrow(query, uuid.UUID(entry_id))

            if not row:
                return None

            return {
                "id": str(row["id"]),
                "work": row["work"],
                "struggle": row["struggle"],
                "intention": row["intention"],
                "created_at": row["created_at"],
                "updated_at": row["updated_at"],
            }
        
    async def update_entry(self, entry_id: str, updated_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        updated_at = datetime.now(timezone.utc)

        async with self.pool.acquire() as conn:
            query = """
            UPDATE entries
            SET
                work = COALESCE($2, work),
                struggle = COALESCE($3, struggle),
                intention = COALESCE($4, intention),
                updated_at = $5
            WHERE id = $1
            RETURNING *
            """

            row = await conn.fetchrow(
                query,
                uuid.UUID(entry_id),
                updated_data.get("work"),
                updated_data.get("struggle"),
                updated_data.get("intention"),
                updated_at,
            )

            if not row:
                return None

            return {
                "id": str(row["id"]),
                "work": row["work"],
                "struggle": row["struggle"],
                "intention": row["intention"],
                "created_at": row["created_at"],
                "updated_at": row["updated_at"],
            }

    async def delete_entry(self, entry_id: str) -> int:
        async with self.pool.acquire() as conn:
            query = "DELETE FROM entries WHERE id = $1"
            result = await conn.execute(query, entry_id)
            # result: "DELETE 0" or "DELETE 1"
            return int(result.split(" ")[1])

    async def delete_all_entries(self) -> int:
        async with self.pool.acquire() as conn:
            query = "DELETE FROM entries"
            result = await conn.execute(query)
            # result: "DELETE 0" or "DELETE N"
            return int(result.split(" ")[1])
