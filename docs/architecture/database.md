# Database Design

OpenGov-Food uses a relational database design with SQLAlchemy ORM, supporting both SQLite for development and PostgreSQL for production.

## Database Schema

### Core Tables

```sql
-- Users table
CREATE TABLE user (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE
);

-- Items table
CREATE TABLE item (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title VARCHAR(100) NOT NULL,
    description TEXT,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE,
    owner_id INTEGER NOT NULL,
    FOREIGN KEY (owner_id) REFERENCES user (id) ON DELETE CASCADE
);
```

### Indexes

```sql
-- User indexes
CREATE UNIQUE INDEX ix_user_email ON user (email);
CREATE INDEX ix_user_id ON user (id);
CREATE INDEX ix_user_created_at ON user (created_at);

-- Item indexes
CREATE INDEX ix_item_owner_id ON item (owner_id);
CREATE INDEX ix_item_status ON item (status);
CREATE INDEX ix_item_created_at ON item (created_at);
CREATE INDEX ix_item_owner_status ON item (owner_id, status);
```

## Entity Relationship Diagram

```mermaid
erDiagram
    USER ||--o{ ITEM : owns

    USER {
        integer id PK
        string email UK
        string hashed_password
        string full_name
        boolean is_active
        datetime created_at
        datetime updated_at
    }

    ITEM {
        integer id PK
        string title
        text description
        string status
        datetime created_at
        datetime updated_at
        integer owner_id FK
    }
```

## SQLAlchemy Models

### User Model

```python
from sqlalchemy import Column, Integer, String, Boolean, DateTime, func
from sqlalchemy.orm import relationship
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
    items = relationship("Item", back_populates="owner", cascade="all, delete-orphan")
```

### Item Model

```python
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, CheckConstraint
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

    # Constraints
    __table_args__ = (
        CheckConstraint("status IN ('pending', 'in_progress', 'completed', 'cancelled')",
                       name="check_item_status"),
    )
```

## Database Configuration

### SQLite (Development)

```python
# Default configuration
DATABASE_URL = "sqlite+aiosqlite:///./opengovfood.db"
```

**Characteristics:**
- File-based database
- No server required
- Easy development setup
- Limited concurrent access
- No advanced features

### PostgreSQL (Production)

```python
# Production configuration
DATABASE_URL = "postgresql+asyncpg://user:password@localhost/opengovfood"
```

**Characteristics:**
- Client-server architecture
- High concurrency support
- Advanced features (JSON, arrays, etc.)
- Better performance for large datasets
- ACID compliance

## Connection Management

### Async Engine Configuration

```python
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# Create async engine
engine = create_async_engine(
    DATABASE_URL,
    echo=False,  # Set to True for SQL logging
    future=True,
    pool_size=10,          # Connection pool size
    max_overflow=20,       # Max overflow connections
    pool_timeout=30,       # Connection timeout
    pool_recycle=3600,     # Recycle connections after 1 hour
)

# Create async session factory
async_session = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)
```

### Database Manager

```python
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession

class DatabaseManager:
    @staticmethod
    async def get_db() -> AsyncGenerator[AsyncSession, None]:
        """Dependency for getting async database session."""
        async with async_session() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()

    @staticmethod
    async def initialize():
        """Create all tables."""
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
```

## Migration Management

### Alembic Setup

```python
# alembic/env.py
import asyncio
from sqlalchemy import pool
from sqlalchemy.ext.asyncio import async_engine_from_config
from alembic import context

# Import models
from opengovfood.models.user import User
from opengovfood.models.item import Item

def run_migrations_offline():
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online():
    """Run migrations in 'online' mode."""
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async def do_run_migrations():
        async with connectable.connect() as connection:
            await connection.run_sync(run_migrations)

        await connectable.dispose()

    asyncio.run(do_run_migrations())

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
```

### Migration Commands

```bash
# Initialize alembic (first time)
alembic init alembic

# Generate migration
alembic revision --autogenerate -m "Add items table"

# Apply migrations
alembic upgrade head

# Downgrade
alembic downgrade -1

# Show current revision
alembic current

# Show migration history
alembic history
```

## Query Patterns

### Basic CRUD Operations

```python
from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession

class UserCRUD:
    @staticmethod
    async def get_by_email(db: AsyncSession, email: str) -> Optional[User]:
        stmt = select(User).where(User.email == email)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def create(db: AsyncSession, user_data: dict) -> User:
        user = User(**user_data)
        db.add(user)
        await db.flush()
        await db.refresh(user)
        return user

    @staticmethod
    async def get_items(db: AsyncSession, user_id: int, skip: int = 0, limit: int = 100):
        stmt = (
            select(Item)
            .where(Item.owner_id == user_id)
            .offset(skip)
            .limit(limit)
        )
        result = await db.execute(stmt)
        return result.scalars().all()
```

### Advanced Queries

```python
# Join with owner information
stmt = (
    select(Item, User.full_name)
    .join(User, Item.owner_id == User.id)
    .where(Item.status == "pending")
)

# Aggregate queries
stmt = (
    select(
        Item.status,
        func.count(Item.id).label("count")
    )
    .group_by(Item.status)
)

# Full-text search (PostgreSQL)
stmt = select(Item).where(Item.title.ilike("%search_term%"))
```

## Performance Optimization

### Indexing Strategy

```sql
-- Single column indexes
CREATE INDEX ix_item_status ON item (status);
CREATE INDEX ix_item_created_at ON item (created_at);

-- Composite indexes
CREATE INDEX ix_item_owner_status ON item (owner_id, status);
CREATE INDEX ix_item_owner_created ON item (owner_id, created_at DESC);

-- Partial indexes
CREATE INDEX ix_active_users ON user (id) WHERE is_active = true;
```

### Query Optimization

```python
# Use selectinload for eager loading
from sqlalchemy.orm import selectinload

stmt = select(User).options(selectinload(User.items))

# Use joinedload for single query
from sqlalchemy.orm import joinedload

stmt = select(Item).options(joinedload(Item.owner))

# Selective column loading
stmt = select(Item.id, Item.title, Item.status)
```

### Connection Pool Tuning

```python
# Production settings
engine = create_async_engine(
    DATABASE_URL,
    pool_size=20,          # Base pool size
    max_overflow=30,       # Additional connections
    pool_timeout=60,       # Connection timeout
    pool_recycle=1800,     # Recycle after 30 minutes
    pool_pre_ping=True,    # Check connection health
)
```

## Data Validation

### Database Constraints

```sql
-- Check constraints
ALTER TABLE item ADD CONSTRAINT check_status
    CHECK (status IN ('pending', 'in_progress', 'completed', 'cancelled'));

-- Not null constraints
ALTER TABLE user ALTER COLUMN email SET NOT NULL;
ALTER TABLE item ALTER COLUMN title SET NOT NULL;

-- Unique constraints
ALTER TABLE user ADD CONSTRAINT unique_email UNIQUE (email);

-- Foreign key constraints
ALTER TABLE item ADD CONSTRAINT fk_item_owner
    FOREIGN KEY (owner_id) REFERENCES user (id) ON DELETE CASCADE;
```

### Application-Level Validation

```python
from pydantic import BaseModel, validator

class ItemCreate(BaseModel):
    title: str
    description: Optional[str] = None
    status: str = "pending"

    @validator('title')
    def title_must_not_be_empty(cls, v):
        if not v.strip():
            raise ValueError('Title cannot be empty')
        return v

    @validator('status')
    def status_must_be_valid(cls, v):
        valid_statuses = {'pending', 'in_progress', 'completed', 'cancelled'}
        if v not in valid_statuses:
            raise ValueError(f'Status must be one of {valid_statuses}')
        return v
```

## Backup and Recovery

### SQLite Backup

```python
import shutil
import asyncio
from pathlib import Path

async def backup_sqlite():
    """Backup SQLite database."""
    db_path = Path("opengovfood.db")
    backup_path = Path(f"backup_{db_path.stem}_{int(time.time())}{db_path.suffix}")

    # SQLite backup (simple file copy)
    shutil.copy2(db_path, backup_path)
    return backup_path
```

### PostgreSQL Backup

```bash
# Create backup
pg_dump -U username -h localhost opengovfood > backup.sql

# Restore backup
psql -U username -h localhost opengovfood < backup.sql

# Compressed backup
pg_dump -U username -h localhost opengovfood | gzip > backup.sql.gz
```

## Monitoring and Maintenance

### Database Health Checks

```python
async def check_database_health():
    """Check database connectivity and performance."""
    try:
        async with async_session() as session:
            # Simple query to test connection
            await session.execute(text("SELECT 1"))

            # Check table existence
            result = await session.execute(text("""
                SELECT name FROM sqlite_master
                WHERE type='table' AND name IN ('user', 'item')
            """))
            tables = result.fetchall()

            return {
                "status": "healthy",
                "tables": [row[0] for row in tables],
                "timestamp": datetime.utcnow()
            }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow()
        }
```

### Performance Monitoring

```sql
-- Query execution statistics (PostgreSQL)
SELECT
    query,
    calls,
    total_time,
    mean_time,
    rows
FROM pg_stat_statements
ORDER BY total_time DESC
LIMIT 10;

-- Table size information
SELECT
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

## Future Enhancements

- **Read Replicas**: Separate read and write databases
- **Database Sharding**: Horizontal scaling across multiple databases
- **JSON Fields**: Flexible metadata storage
- **Full-Text Search**: Advanced search capabilities
- **Audit Logging**: Track all data changes
- **Data Archiving**: Move old data to archive tables
- **Database Encryption**: Encrypt sensitive data at rest