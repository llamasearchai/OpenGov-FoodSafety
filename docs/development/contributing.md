# Contributing

We welcome contributions to OpenGov-Food! This document provides guidelines and information for contributors.

## Development Setup

### Prerequisites

- Python 3.11+
- uv or pip
- Git

### Clone and Setup

```bash
# Fork the repository on GitHub
# Clone your fork
git clone https://github.com/your-username/OpenGov-Food.git
cd OpenGov-Food

# Create virtual environment
uv venv
uv sync --extra dev

# Activate environment
source .venv/bin/activate

# Initialize database for development
python -c "from opengovfood.core.database import DatabaseManager; import asyncio; asyncio.run(DatabaseManager.initialize())"
```

### Development Workflow

```bash
# Create a feature branch
git checkout -b feature/your-feature-name

# Make your changes
# Write tests
# Run tests and linting

# Commit your changes
git add .
git commit -m "Add your feature"

# Push to your fork
git push origin feature/your-feature-name

# Create a Pull Request on GitHub
```

## Code Quality

### Linting and Formatting

We use several tools to maintain code quality:

```bash
# Run all linting and formatting
uv run ruff check src/
uv run black src/
uv run isort src/
uv run mypy src/

# Auto-fix issues where possible
uv run ruff check src/ --fix
uv run black src/
uv run isort src/
```

### Pre-commit Hooks

Install pre-commit hooks to run quality checks automatically:

```bash
uv run pre-commit install

# Run on all files
uv run pre-commit run --all-files
```

## Testing

### Running Tests

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=opengovfood --cov-report=html

# Run specific tests
uv run pytest tests/test_api.py::TestAuthentication::test_user_registration

# Run tests in parallel
uv run pytest -n auto

# Run tests with verbose output
uv run pytest -v
```

### Writing Tests

```python
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

@pytest.mark.asyncio
async def test_create_item(client: AsyncClient, test_user_token: str):
    """Test creating a new item."""
    headers = {"Authorization": f"Bearer {test_user_token}"}
    item_data = {
        "title": "Test Item",
        "description": "Test description",
        "status": "pending"
    }

    response = await client.post("/api/v1/items/", json=item_data, headers=headers)

    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Test Item"
    assert data["status"] == "pending"
    assert "id" in data
```

### Test Coverage

Maintain 100% test coverage for new code:

```bash
# Check coverage
uv run pytest --cov=opengovfood --cov-report=term-missing --cov-fail-under=85

# View coverage report
open htmlcov/index.html
```

## API Design Guidelines

### RESTful Principles

- Use appropriate HTTP methods (GET, POST, PUT, DELETE)
- Use plural nouns for resource names
- Use HTTP status codes correctly
- Include relevant headers

### Endpoint Structure

```
GET    /api/v1/items          # List items
POST   /api/v1/items          # Create item
GET    /api/v1/items/{id}     # Get item
PUT    /api/v1/items/{id}     # Update item
DELETE /api/v1/items/{id}     # Delete item
```

### Request/Response Format

```python
# Request validation
class ItemCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=1000)
    status: str = Field("pending", pattern="^(pending|in_progress|completed|cancelled)$")

# Response schema
class Item(ItemBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime]
    owner_id: int
```

## Database Guidelines

### Model Design

```python
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
        CheckConstraint("status IN ('pending', 'in_progress', 'completed', 'cancelled')"),
    )
```

### Migration Guidelines

```bash
# Create migration
alembic revision --autogenerate -m "Add new field to item table"

# Review and edit migration file
# Apply migration
alembic upgrade head
```

## Security Guidelines

### Authentication

- Always validate JWT tokens
- Check user ownership for data access
- Use HTTPS in production
- Implement rate limiting

### Input Validation

```python
# Validate all inputs
@validator('email')
def email_must_be_valid(cls, v):
    if not v or '@' not in v:
        raise ValueError('Invalid email address')
    return v

# Sanitize user inputs
def sanitize_input(text: str) -> str:
    return bleach.clean(text, tags=[], attributes={})
```

## Documentation

### Code Documentation

```python
def create_item(
    *,
    db: AsyncSession,
    title: str,
    description: Optional[str] = None,
    status: str = "pending",
    owner_id: int
) -> Item:
    """
    Create a new item.

    Args:
        db: Database session
        title: Item title (1-100 characters)
        description: Optional item description
        status: Item status (pending, in_progress, completed, cancelled)
        owner_id: ID of the item owner

    Returns:
        Created item instance

    Raises:
        ValueError: If validation fails
    """
```

### API Documentation

Use FastAPI's automatic documentation features:

```python
@app.post(
    "/items/",
    response_model=Item,
    summary="Create Item",
    description="Create a new item for the authenticated user."
)
async def create_item(
    item_in: ItemCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    # Implementation
```

## Commit Guidelines

### Commit Message Format

```
type(scope): description

[optional body]

[optional footer]
```

### Types

- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation
- `style`: Code style changes
- `refactor`: Code refactoring
- `test`: Testing
- `chore`: Maintenance

### Examples

```
feat(auth): add JWT token refresh endpoint

fix(api): handle empty item descriptions correctly

docs(api): update authentication examples

test(items): add comprehensive CRUD tests
```

## Pull Request Process

### PR Checklist

- [ ] Tests pass locally
- [ ] Code coverage maintained
- [ ] Linting passes
- [ ] Documentation updated
- [ ] Migration files included if needed
- [ ] Security review completed

### PR Description

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Unit tests added/updated
- [ ] Integration tests pass
- [ ] Manual testing completed

## Checklist
- [ ] Code follows style guidelines
- [ ] Documentation updated
- [ ] Migration scripts included
- [ ] Security implications reviewed
```

## Release Process

### Version Numbering

Follow [Semantic Versioning](https://semver.org/):

- `MAJOR.MINOR.PATCH`
- `MAJOR`: Breaking changes
- `MINOR`: New features
- `PATCH`: Bug fixes

### Release Checklist

- [ ] Update version in `pyproject.toml`
- [ ] Update `CHANGELOG.md`
- [ ] Create git tag
- [ ] Build and test release
- [ ] Publish to PyPI
- [ ] Deploy to production
- [ ] Update documentation

## Code Review Guidelines

### Reviewer Checklist

- [ ] Code is readable and well-documented
- [ ] Tests are comprehensive
- [ ] Security implications reviewed
- [ ] Performance considerations addressed
- [ ] Database changes are safe
- [ ] API design follows REST principles

### Review Comments

- Be constructive and specific
- Suggest improvements, don't just criticize
- Explain reasoning for suggestions
- Acknowledge good practices

## Getting Help

### Communication Channels

- **Issues**: Bug reports and feature requests
- **Discussions**: General questions and ideas
- **Pull Requests**: Code review and contributions

### Support

- Check existing issues and documentation first
- Provide detailed information when reporting bugs
- Include code samples and error messages
- Be patient and respectful

## Recognition

Contributors are recognized in:

- `CONTRIBUTORS.md` file
- GitHub contributor statistics
- Release notes
- Project documentation

Thank you for contributing to OpenGov-Food! 🎉