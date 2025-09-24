# Data Models

OpenGov-Food uses SQLAlchemy for database models and Pydantic for API schemas, providing type safety and automatic validation.

## Database Models

### User Model

```python
from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.sql import func
from opengovfood.core.database import Base

class User(Base):
    __tablename__ = "user"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    items = relationship("Item", back_populates="owner")
```

### Item Model

```python
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from opengovfood.core.database import Base

class Item(Base):
    __tablename__ = "item"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(100), nullable=False)
    description = Column(Text)
    status = Column(String(20), nullable=False, default="pending")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    owner_id = Column(Integer, ForeignKey("user.id"), nullable=False)

    # Relationships
    owner = relationship("User", back_populates="items")

    __table_args__ = (
        CheckConstraint("status IN ('pending', 'in_progress', 'completed', 'cancelled')",
                       name="check_status"),
    )
```

## Pydantic Schemas

### User Schemas

```python
from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional

# Base user schema
class UserBase(BaseModel):
    email: EmailStr
    full_name: str
    is_active: bool = True

# User creation schema
class UserCreate(UserBase):
    password: str

# User update schema
class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    is_active: Optional[bool] = None
    password: Optional[str] = None

# User response schema
class User(UserBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

# User with items
class UserWithItems(User):
    items: List["Item"] = []
```

### Item Schemas

```python
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List

# Base item schema
class ItemBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=1000)
    status: str = Field("pending", pattern="^(pending|in_progress|completed|cancelled)$")

# Item creation schema
class ItemCreate(ItemBase):
    pass

# Item update schema
class ItemUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=1000)
    status: Optional[str] = Field(None, pattern="^(pending|in_progress|completed|cancelled)$")

# Item response schema
class Item(ItemBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime]
    owner_id: int

    class Config:
        from_attributes = True

# Item with owner
class ItemWithOwner(Item):
    owner: "User"
```

### Authentication Schemas

```python
from pydantic import BaseModel

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class TokenData(BaseModel):
    email: Optional[str] = None
```

## Database Relationships

### One-to-Many: User → Items

```python
# User has many items
user.items  # List of Item objects

# Item belongs to one user
item.owner  # User object
```

### Database Schema

```sql
-- Users table
CREATE TABLE user (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email VARCHAR UNIQUE NOT NULL,
    hashed_password VARCHAR NOT NULL,
    full_name VARCHAR NOT NULL,
    is_active BOOLEAN DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME
);

-- Items table
CREATE TABLE item (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title VARCHAR(100) NOT NULL,
    description TEXT,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME,
    owner_id INTEGER NOT NULL,
    FOREIGN KEY (owner_id) REFERENCES user (id),
    CHECK (status IN ('pending', 'in_progress', 'completed', 'cancelled'))
);

-- Indexes
CREATE INDEX ix_user_email ON user(email);
CREATE INDEX ix_user_id ON user(id);
CREATE INDEX ix_item_owner_id ON item(owner_id);
CREATE INDEX ix_item_status ON item(status);
```

## Model Validation

### Pydantic Validation

```python
from opengovfood.models.item import ItemCreate

# Valid item
item = ItemCreate(
    title="Valid Title",
    description="Valid description",
    status="pending"
)

# Invalid item - will raise ValidationError
try:
    invalid_item = ItemCreate(
        title="",  # Too short
        status="invalid_status"  # Invalid status
    )
except ValidationError as e:
    print(e.errors())
```

### SQLAlchemy Validation

```python
from opengovfood.models.item import Item

# Create item with validation
item = Item(
    title="Valid Title",
    description="Valid description",
    status="pending",
    owner_id=1
)

# Database constraints will prevent invalid data
session.add(item)
session.commit()  # May raise IntegrityError
```

## Type Safety

### Type Hints

All models use proper type hints for IDE support and runtime validation:

```python
from typing import List, Optional
from datetime import datetime

def create_item(
    title: str,
    description: Optional[str] = None,
    status: str = "pending"
) -> Item:
    # Function implementation
    pass

async def get_user_items(user_id: int) -> List[Item]:
    # Async function with proper return type
    pass
```

### Generic Types

```python
from typing import TypeVar, Generic
from pydantic.generics import GenericModel

DataT = TypeVar('DataT')

class APIResponse(GenericModel, Generic[DataT]):
    data: DataT
    message: str

# Usage
response: APIResponse[List[Item]] = APIResponse(
    data=items,
    message="Items retrieved successfully"
)
```

## Migration Support

### Alembic Migrations

Database schema changes are managed through Alembic:

```python
# alembic/env.py
from opengovfood.models import Base

# Import all models for Alembic
from opengovfood.models.user import User
from opengovfood.models.item import Item

target_metadata = Base.metadata
```

### Migration Example

```bash
# Generate migration
alembic revision --autogenerate -m "Add items table"

# Apply migration
alembic upgrade head
```

## Testing Models

### Model Factories

```python
import factory
from opengovfood.models.user import User

class UserFactory(factory.Factory):
    class Meta:
        model = User

    email = factory.Sequence(lambda n: f"user{n}@example.com")
    full_name = factory.Faker("name")
    hashed_password = factory.PostGenerationMethodCall("set_password", "password")
    is_active = True
```

### Test Fixtures

```python
@pytest.fixture
async def test_user(db_session):
    user = User(
        email="test@example.com",
        hashed_password=get_password_hash("password"),
        full_name="Test User"
    )
    db_session.add(user)
    await db_session.commit()
    return user
```

## Performance Optimizations

### Database Indexes

```python
# Automatic indexes on foreign keys and unique constraints
# Additional indexes for performance

class Item(Base):
    # ... fields ...
    __table_args__ = (
        Index('ix_item_owner_status', 'owner_id', 'status'),
        Index('ix_item_created_at', 'created_at'),
    )
```

### Query Optimization

```python
# Eager loading relationships
query = select(Item).options(selectinload(Item.owner))

# Selective field loading
query = select(Item.id, Item.title, Item.status)
```

### Connection Pooling

```python
# Database engine configuration
engine = create_async_engine(
    DATABASE_URL,
    pool_size=10,
    max_overflow=20,
    pool_timeout=30,
    pool_recycle=3600
)
```

## Future Enhancements

- Soft deletes with deleted_at timestamp
- Audit logging for all changes
- JSON fields for flexible metadata
- Full-text search capabilities
- Database partitioning for large datasets
- Read replicas for high availability