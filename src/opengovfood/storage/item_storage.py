"""SQLite-backed storage utilities for OpenGov Food."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

import structlog
from sqlite_utils import Database
from sqlite_utils.db import NotFoundError

from ..core.config import get_settings
from ..schemas.item import Item, ItemCreate

logger = structlog.get_logger(__name__)


@dataclass
class ItemRecord:
    """Runtime representation of an inspection item stored in SQLite."""

    id: int
    title: str
    description: Optional[str]
    owner_id: int
    created_at: datetime
    updated_at: datetime

    def to_row(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "owner_id": self.owner_id,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    def to_schema(self) -> Item:
        return Item(
            id=self.id,
            title=self.title,
            description=self.description,
            owner_id=self.owner_id,
        )


def _ensure_table(db: Database) -> None:
    if db["items"].exists():  # pragma: no cover - simple guard
        return
    db["items"].create(
        {
            "id": int,
            "title": str,
            "description": str,
            "owner_id": int,
            "created_at": str,
            "updated_at": str,
        },
        pk="id",
        if_not_exists=True,
    )


class ItemStorage:
    """Utility wrapper around sqlite-utils for inspection artefacts."""

    def __init__(self, db_path: Optional[str] = None) -> None:
        settings = get_settings()
        path = db_path or settings.database_url.replace("sqlite:///", "")
        self.db = Database(path)
        _ensure_table(self.db)

    def create_item(self, item: ItemCreate, owner_id: int) -> Item:
        record = ItemRecord(
            id=self._next_id(),
            title=item.title,
            description=item.description,
            owner_id=owner_id,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        self.db["items"].insert(record.to_row())
        return record.to_schema()

    def get_item(self, item_id: int) -> Optional[Item]:
        try:
            row = self.db["items"].get(item_id)
        except NotFoundError:
            return None
        return self._row_to_schema(row)

    def list_items(self, limit: int = 100, offset: int = 0) -> List[Item]:
        rows = self.db["items"].rows_where("1=1", limit=limit, offset=offset)
        return [self._row_to_schema(row) for row in rows]

    def update_item(self, item_id: int, updates: Dict[str, Any]) -> bool:
        changes = dict(updates)
        changes["updated_at"] = datetime.utcnow().isoformat()
        return self.db["items"].update(item_id, changes) > 0

    def delete_item(self, item_id: int) -> bool:
        return self.db["items"].delete(item_id) > 0

    def get_item_stats(self) -> Dict[str, int]:
        return {"total_items": self.db["items"].count}

    def _next_id(self) -> int:
        row = self.db.query("SELECT MAX(id) AS last_id FROM items").fetchone()
        last_id = row["last_id"] if row else None
        return int(last_id) + 1 if last_id is not None else 1

    @staticmethod
    def _row_to_schema(row: Dict[str, Any]) -> Item:
        return Item(
            id=row.get("id"),
            title=row.get("title"),
            description=row.get("description"),
            owner_id=row.get("owner_id"),
        )