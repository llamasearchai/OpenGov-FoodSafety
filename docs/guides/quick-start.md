# Quick Start

Get OpenGov-Food up and running in minutes with this quick start guide.

## Prerequisites

Make sure you have completed the [Installation](installation.md) steps.

## 1. Initialize the Database

First, create the database tables:

```bash
# Activate virtual environment (if not already activated)
source .venv/bin/activate

# Initialize the database
opengov-food db init
```

This creates the SQLite database and all necessary tables.

## 2. Start the FastAPI Server

Launch the development server:

```bash
uvicorn opengovfood.web.app:app --reload --host 0.0.0.0 --port 8000
```

You should see output like:
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process [12345] using StatReload
INFO:     Started server process [12346]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

## 3. Access the API Documentation

Open your browser and visit:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

## 4. Test the API

Let's test the API with some basic operations.

### Register a User

```bash
curl -X POST "http://localhost:8000/api/v1/users/open" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "password123",
    "full_name": "Test User"
  }'
```

**Expected Response:**
```json
{
  "id": 1,
  "email": "test@example.com",
  "full_name": "Test User",
  "is_active": true,
  "created_at": "2024-01-01T00:00:00Z"
}
```

### Login and Get Access Token

```bash
curl -X POST "http://localhost:8000/api/v1/users/login/access-token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=test@example.com&password=password123"
```

**Expected Response:**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer"
}
```

Save the `access_token` value for the next steps.

### Create an Item

```bash
curl -X POST "http://localhost:8000/api/v1/items/" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -d '{
    "title": "Sample Food Inspection",
    "description": "Routine inspection of local restaurant",
    "status": "pending"
  }'
```

**Expected Response:**
```json
{
  "id": 1,
  "title": "Sample Food Inspection",
  "description": "Routine inspection of local restaurant",
  "status": "pending",
  "owner_id": 1
}
```

### List All Items

```bash
curl -X GET "http://localhost:8000/api/v1/items/" \
  -H "Authorization: Bearer $ACCESS_TOKEN"
```

**Expected Response:**
```json
[
  {
    "id": 1,
    "title": "Sample Food Inspection",
    "description": "Routine inspection of local restaurant",
    "status": "pending",
    "owner_id": 1
  }
]
```

## 5. Using Python Client

Instead of curl, you can use Python with httpx:

```python
import httpx

# Base URL
BASE_URL = "http://localhost:8000"

# 1. Register user
user_data = {
    "email": "python@example.com",
    "password": "password123",
    "full_name": "Python User"
}

response = httpx.post(f"{BASE_URL}/api/v1/users/open", json=user_data)
print("User registered:", response.json())

# 2. Login
login_data = {"username": "python@example.com", "password": "password123"}
response = httpx.post(
    f"{BASE_URL}/api/v1/users/login/access-token",
    data=login_data
)
token = response.json()["access_token"]
print("Access token:", token[:20] + "...")

# 3. Create item
headers = {"Authorization": f"Bearer {token}"}
item_data = {
    "title": "Python Food Inspection",
    "description": "Created via Python client",
    "status": "in_progress"
}

response = httpx.post(
    f"{BASE_URL}/api/v1/items/",
    json=item_data,
    headers=headers
)
print("Item created:", response.json())

# 4. List items
response = httpx.get(f"{BASE_URL}/api/v1/items/", headers=headers)
print("Items:", response.json())
```

## 6. Run Tests

Verify everything is working by running the test suite:

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=opengovfood --cov-report=term-missing
```

## Next Steps

- Explore the full [API Reference](../api/overview.md)
- Learn about [Configuration](configuration.md)
- Set up [Development Environment](../development/contributing.md)
- Deploy to [Production](../development/deployment.md)

## Troubleshooting

**Server won't start**: Check if port 8000 is already in use.

```bash
# Kill process using port 8000
lsof -ti:8000 | xargs kill -9

# Or use a different port
uvicorn opengovfood.web.app:app --reload --host 0.0.0.0 --port 8001
```

**Database errors**: Make sure the database was initialized properly.

```bash
# Reinitialize database
rm opengovfood.db
opengov-food db init
```

**Authentication fails**: Ensure you're using the correct token format.

```bash
# Check token format
echo "Bearer YOUR_TOKEN_HERE"
```