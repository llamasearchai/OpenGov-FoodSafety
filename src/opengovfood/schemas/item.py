from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict

from ..models.item import ItemStatus

# Shared properties
class ItemBase(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None


# Properties to receive on item creation
class ItemCreate(ItemBase):
    title: str
    status: ItemStatus = ItemStatus.PENDING


# Properties to receive on item update
class ItemUpdate(ItemBase):
    status: Optional[ItemStatus] = None


# Properties shared by models stored in DB
class ItemInDBBase(ItemBase):
    id: int
    title: str
    owner_id: int
    status: ItemStatus
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# Properties to return to client
class Item(ItemInDBBase):
    pass


# Properties properties stored in DB
class ItemInDB(ItemInDBBase):
    pass
