# Testing

OpenGov-Food includes comprehensive testing with pytest, focusing on API testing, database integration, and security validation.

## Test Structure

```
tests/
├── __init__.py
├── conftest.py          # Test configuration and fixtures
├── test_api.py          # API endpoint tests
├── test_core.py         # Core functionality tests
├── test_comprehensive.py # Integration tests
└── test_security.py     # Security-specific tests
```

## Test Configuration

### pytest Configuration

```ini
# pytest.ini
[tool:pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
addopts = [
    "--strict-markers",
    "--strict-config",
    "--verbose",
    "--tb=short",
    "--cov=opengovfood",
    "--cov-report=term-missing",
    "--cov-report=html:htmlcov",
    "--cov-report=xml",
    "--cov-fail-under=85",
]
markers = [
    "slow: marks tests as slow",
    "integration: marks tests as integration tests",
    "unit: marks tests as unit tests",
    "security: marks tests as security tests",
]
```

### Test Fixtures

```python
# tests/conftest.py
import pytest
import asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from opengovfood.core.database import Base, DatabaseManager
from opengovfood.web.app import app
from opengovfood.core.security import create_access_token

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
async def test_db():
    """Create test database and tables."""
    # Use in-memory SQLite for tests
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Create session factory
    TestingSessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine,
        class_=AsyncSession
    )

    yield TestingSessionLocal

    await engine.dispose()

@pytest.fixture
async def db_session(test_db):
    """Provide database session for tests."""
    async with test_db() as session:
        yield session
        await session.rollback()

@pytest.fixture
async def client():
    """Provide test client for API tests."""
    async with AsyncClient(app=app, base_url="http://testserver") as client:
        yield client

@pytest.fixture
async def test_user(db_session):
    """Create a test user."""
    from opengovfood.crud.user import user_crud
    from opengovfood.models.user import UserCreate

    user_data = UserCreate(
        email="test@example.com",
        password="testpassword",
        full_name="Test User"
    )

    user = await user_crud.create(db_session, obj_in=user_data)
    return user

@pytest.fixture
async def test_user_token(test_user):
    """Create access token for test user."""
    return create_access_token(test_user.email)
```

## API Testing

### Authentication Tests

```python
import pytest
from httpx import AsyncClient

class TestAuthentication:
    @pytest.mark.asyncio
    async def test_user_registration(self, client: AsyncClient):
        """Test user registration endpoint."""
        user_data = {
            "email": "newuser@example.com",
            "password": "securepassword123",
            "full_name": "New User"
        }

        response = await client.post("/api/v1/users/open", json=user_data)

        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "newuser@example.com"
        assert data["full_name"] == "New User"
        assert "id" in data
        assert "created_at" in data

    @pytest.mark.asyncio
    async def test_user_login(self, client: AsyncClient, test_user):
        """Test user login endpoint."""
        login_data = {
            "username": test_user.email,
            "password": "testpassword"
        }

        response = await client.post(
            "/api/v1/users/login/access-token",
            data=login_data
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    @pytest.mark.asyncio
    async def test_invalid_login(self, client: AsyncClient):
        """Test login with invalid credentials."""
        login_data = {
            "username": "nonexistent@example.com",
            "password": "wrongpassword"
        }

        response = await client.post(
            "/api/v1/users/login/access-token",
            data=login_data
        )

        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
```

### CRUD Tests

```python
class TestCRUDOperations:
    @pytest.mark.asyncio
    async def test_create_item(self, client: AsyncClient, test_user_token: str):
        """Test creating a new item."""
        headers = {"Authorization": f"Bearer {test_user_token}"}
        item_data = {
            "title": "Test Item",
            "description": "Test description",
            "status": "pending"
        }

        response = await client.post(
            "/api/v1/items/",
            json=item_data,
            headers=headers
        )

        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "Test Item"
        assert data["status"] == "pending"
        assert "id" in data

    @pytest.mark.asyncio
    async def test_get_items(self, client: AsyncClient, test_user_token: str):
        """Test retrieving user items."""
        headers = {"Authorization": f"Bearer {test_user_token}"}

        # Create test item first
        item_data = {"title": "Test Item", "status": "pending"}
        await client.post("/api/v1/items/", json=item_data, headers=headers)

        # Get items
        response = await client.get("/api/v1/items/", headers=headers)

        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert len(data["items"]) >= 1
        assert data["items"][0]["title"] == "Test Item"

    @pytest.mark.asyncio
    async def test_update_item(self, client: AsyncClient, test_user_token: str):
        """Test updating an item."""
        headers = {"Authorization": f"Bearer {test_user_token}"}

        # Create item
        item_data = {"title": "Original Title", "status": "pending"}
        create_response = await client.post(
            "/api/v1/items/",
            json=item_data,
            headers=headers
        )
        item_id = create_response.json()["id"]

        # Update item
        update_data = {"title": "Updated Title", "status": "completed"}
        response = await client.put(
            f"/api/v1/items/{item_id}",
            json=update_data,
            headers=headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Updated Title"
        assert data["status"] == "completed"

    @pytest.mark.asyncio
    async def test_delete_item(self, client: AsyncClient, test_user_token: str):
        """Test deleting an item."""
        headers = {"Authorization": f"Bearer {test_user_token}"}

        # Create item
        item_data = {"title": "Item to Delete", "status": "pending"}
        create_response = await client.post(
            "/api/v1/items/",
            json=item_data,
            headers=headers
        )
        item_id = create_response.json()["id"]

        # Delete item
        response = await client.delete(
            f"/api/v1/items/{item_id}",
            headers=headers
        )

        assert response.status_code == 204

        # Verify item is deleted
        get_response = await client.get(
            f"/api/v1/items/{item_id}",
            headers=headers
        )
        assert get_response.status_code == 404

    @pytest.mark.asyncio
    async def test_access_other_user_item(self, client: AsyncClient, test_user_token: str):
        """Test that users cannot access other users' items."""
        headers = {"Authorization": f"Bearer {test_user_token}"}

        # Try to access non-existent item (simulating other user's item)
        response = await client.get("/api/v1/items/99999", headers=headers)

        assert response.status_code == 404
```

## Security Testing

### Authentication Security Tests

```python
class TestSecurity:
    @pytest.mark.asyncio
    async def test_unauthorized_access(self, client: AsyncClient):
        """Test accessing protected endpoints without authentication."""
        response = await client.get("/api/v1/items/")

        assert response.status_code == 401
        data = response.json()
        assert "detail" in data

    @pytest.mark.asyncio
    async def test_invalid_token(self, client: AsyncClient):
        """Test accessing endpoints with invalid token."""
        headers = {"Authorization": "Bearer invalid.token.here"}

        response = await client.get("/api/v1/items/", headers=headers)

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_sql_injection_protection(self, client: AsyncClient, test_user_token: str):
        """Test protection against SQL injection."""
        headers = {"Authorization": f"Bearer {test_user_token}"}

        # Attempt SQL injection
        malicious_data = {
            "title": "'; DROP TABLE user; --",
            "status": "pending"
        }

        response = await client.post(
            "/api/v1/items/",
            json=malicious_data,
            headers=headers
        )

        # Should fail validation or be sanitized
        assert response.status_code in [201, 422]

    @pytest.mark.asyncio
    async def test_xss_protection(self, client: AsyncClient, test_user_token: str):
        """Test protection against XSS attacks."""
        headers = {"Authorization": f"Bearer {test_user_token}"}

        xss_payload = {
            "title": "<script>alert('xss')</script>",
            "description": "<img src=x onerror=alert('xss')>",
            "status": "pending"
        }

        response = await client.post(
            "/api/v1/items/",
            json=xss_payload,
            headers=headers
        )

        if response.status_code == 201:
            data = response.json()
            # Ensure scripts are not in the response
            assert "<script>" not in data.get("title", "")
            assert "onerror" not in data.get("description", "")
```

## Database Testing

### Model Tests

```python
class TestModels:
    @pytest.mark.asyncio
    async def test_user_creation(self, db_session: AsyncSession):
        """Test User model creation."""
        from opengovfood.models.user import User

        user = User(
            email="modeltest@example.com",
            hashed_password="hashedpassword",
            full_name="Model Test User"
        )

        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        assert user.id is not None
        assert user.email == "modeltest@example.com"
        assert user.is_active == True

    @pytest.mark.asyncio
    async def test_item_creation(self, db_session: AsyncSession, test_user):
        """Test Item model creation."""
        from opengovfood.models.item import Item

        item = Item(
            title="Test Item",
            description="Test description",
            status="pending",
            owner_id=test_user.id
        )

        db_session.add(item)
        await db_session.commit()
        await db_session.refresh(item)

        assert item.id is not None
        assert item.title == "Test Item"
        assert item.owner_id == test_user.id
```

## Integration Testing

### End-to-End Tests

```python
class TestIntegration:
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_full_user_workflow(self, client: AsyncClient):
        """Test complete user registration and item management workflow."""
        # 1. Register user
        user_data = {
            "email": "workflow@example.com",
            "password": "workflowpass123",
            "full_name": "Workflow User"
        }

        register_response = await client.post("/api/v1/users/open", json=user_data)
        assert register_response.status_code == 201
        user = register_response.json()

        # 2. Login
        login_data = {
            "username": user["email"],
            "password": "workflowpass123"
        }

        login_response = await client.post(
            "/api/v1/users/login/access-token",
            data=login_data
        )
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]

        # 3. Create items
        headers = {"Authorization": f"Bearer {token}"}

        items_data = [
            {"title": "Item 1", "status": "pending"},
            {"title": "Item 2", "status": "in_progress"},
            {"title": "Item 3", "status": "completed"}
        ]

        created_items = []
        for item_data in items_data:
            response = await client.post("/api/v1/items/", json=item_data, headers=headers)
            assert response.status_code == 201
            created_items.append(response.json())

        # 4. List items
        list_response = await client.get("/api/v1/items/", headers=headers)
        assert list_response.status_code == 200
        items_list = list_response.json()
        assert len(items_list["items"]) == 3

        # 5. Update item
        item_to_update = created_items[0]
        update_data = {"status": "completed"}

        update_response = await client.put(
            f"/api/v1/items/{item_to_update['id']}",
            json=update_data,
            headers=headers
        )
        assert update_response.status_code == 200

        # 6. Delete item
        item_to_delete = created_items[1]

        delete_response = await client.delete(
            f"/api/v1/items/{item_to_delete['id']}",
            headers=headers
        )
        assert delete_response.status_code == 204

        # 7. Verify final state
        final_list_response = await client.get("/api/v1/items/", headers=headers)
        final_items = final_list_response.json()["items"]
        assert len(final_items) == 2
```

## Performance Testing

### Load Testing

```python
import asyncio
import time
from typing import List

@pytest.mark.asyncio
@pytest.mark.slow
async def test_api_performance(client: AsyncClient, test_user_token: str):
    """Test API performance under load."""
    headers = {"Authorization": f"Bearer {test_user_token}"}

    # Create multiple items concurrently
    async def create_item(i: int):
        item_data = {
            "title": f"Performance Item {i}",
            "status": "pending"
        }
        start_time = time.time()
        response = await client.post("/api/v1/items/", json=item_data, headers=headers)
        end_time = time.time()
        return response.status_code == 201, end_time - start_time

    # Run concurrent requests
    tasks = [create_item(i) for i in range(50)]
    results = await asyncio.gather(*tasks)

    # Analyze results
    success_count = sum(1 for success, _ in results if success)
    avg_response_time = sum(duration for _, duration in results) / len(results)

    assert success_count == 50  # All requests should succeed
    assert avg_response_time < 1.0  # Average response time under 1 second
```

## Test Coverage

### Coverage Configuration

```ini
# pyproject.toml
[tool.coverage.run]
source = ["opengovfood"]
branch = true
parallel = true

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "raise AssertionError",
    "raise NotImplementedError",
]
```

### Coverage Goals

- **API Endpoints**: 100% coverage
- **Business Logic**: 100% coverage
- **Models**: 100% coverage
- **Utilities**: 90% coverage minimum
- **Error Handling**: 95% coverage

## Continuous Integration

### GitHub Actions Workflow

```yaml
# .github/workflows/ci.yml
name: CI

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: [3.11, 3.12]

    steps:
    - uses: actions/checkout@v3
    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}

    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -e .[dev]

    - name: Run tests
      run: |
        pytest --cov=opengovfood --cov-report=xml

    - name: Upload coverage
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
```

## Test Data Management

### Test Data Factories

```python
import factory
from opengovfood.models.user import User
from opengovfood.models.item import Item

class UserFactory(factory.Factory):
    class Meta:
        model = User

    email = factory.Sequence(lambda n: f"user{n}@example.com")
    full_name = factory.Faker("name")
    hashed_password = factory.PostGenerationMethodCall("set_password", "password")
    is_active = True

class ItemFactory(factory.Factory):
    class Meta:
        model = Item

    title = factory.Faker("sentence", nb_words=4)
    description = factory.Faker("paragraph")
    status = factory.Iterator(["pending", "in_progress", "completed", "cancelled"])
    owner = factory.SubFactory(UserFactory)
```

## Debugging Tests

### Common Test Issues

1. **Async Test Issues**:
   ```python
   # Ensure proper async test setup
   @pytest.mark.asyncio
   async def test_async_function(self):
       # Test async code
       pass
   ```

2. **Database State Issues**:
   ```python
   # Use fixtures with proper cleanup
   @pytest.fixture(autouse=True)
   async def cleanup_db(self, db_session):
       yield
       # Cleanup after test
       await db_session.rollback()
   ```

3. **Fixture Dependencies**:
   ```python
   # Ensure fixture dependencies are correct
   @pytest.fixture
   async def dependent_fixture(self, required_fixture):
       # Use required_fixture
       pass
   ```

## Best Practices

### Test Organization

- Group related tests in classes
- Use descriptive test names
- Keep tests focused and small
- Use fixtures for common setup

### Test Quality

- Test both success and failure cases
- Test edge cases and error conditions
- Verify data integrity
- Test performance requirements

### Maintenance

- Keep tests up to date with code changes
- Remove obsolete tests
- Refactor tests when code is refactored
- Review test coverage regularly