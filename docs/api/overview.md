# API Overview

OpenGov-Food provides a RESTful API built with FastAPI for managing food safety inspection data and user authentication.

## Base URL

```
http://localhost:8000/api/v1
```

## Authentication

Most endpoints require authentication using JWT (JSON Web Tokens). Include the token in the Authorization header:

```
Authorization: Bearer <your-jwt-token>
```

## Response Format

All responses are in JSON format with consistent structure:

**Success Response:**
```json
{
  "data": { ... },
  "message": "Operation successful"
}
```

**Error Response:**
```json
{
  "detail": "Error message",
  "type": "error_type"
}
```

## HTTP Status Codes

- `200` - Success
- `201` - Created
- `400` - Bad Request
- `401` - Unauthorized
- `403` - Forbidden
- `404` - Not Found
- `422` - Validation Error
- `500` - Internal Server Error

## API Endpoints

### Authentication
- `POST /users/open` - Register new user
- `POST /users/login/access-token` - Login and get access token

### Items
- `GET /items/` - List items
- `POST /items/` - Create item
- `GET /items/{item_id}` - Get item by ID
- `PUT /items/{item_id}` - Update item
- `DELETE /items/{item_id}` - Delete item

## Request/Response Examples

### Authentication

**Register User:**
```bash
POST /api/v1/users/open
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "securepassword",
  "full_name": "John Doe"
}
```

**Login:**
```bash
POST /api/v1/users/login/access-token
Content-Type: application/x-www-form-urlencoded

username=user@example.com&password=securepassword
```

### Items

**Create Item:**
```bash
POST /api/v1/items/
Authorization: Bearer <token>
Content-Type: application/json

{
  "title": "Restaurant Inspection",
  "description": "Monthly health inspection",
  "status": "pending"
}
```

**List Items:**
```bash
GET /api/v1/items/
Authorization: Bearer <token>
```

## Data Models

### User
```json
{
  "id": 1,
  "email": "user@example.com",
  "full_name": "John Doe",
  "is_active": true,
  "created_at": "2024-01-01T00:00:00Z"
}
```

### Item
```json
{
  "id": 1,
  "title": "Restaurant Inspection",
  "description": "Monthly health inspection",
  "status": "pending",
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z",
  "owner_id": 1
}
```

## Rate Limiting

- Authentication endpoints: 10 requests per minute
- API endpoints: 100 requests per minute per user

## Pagination

List endpoints support pagination:

```bash
GET /api/v1/items/?skip=0&limit=10
```

Parameters:
- `skip` (int): Number of items to skip (default: 0)
- `limit` (int): Maximum number of items to return (default: 100, max: 1000)

## Filtering and Sorting

Items can be filtered and sorted:

```bash
GET /api/v1/items/?status=pending&sort=created_at:desc
```

Supported filters:
- `status`: pending, in_progress, completed, cancelled
- `owner_id`: Filter by owner
- `created_at_gte`: Created after date
- `created_at_lte`: Created before date

## Validation

The API uses Pydantic for request/response validation. Invalid requests return detailed error messages:

```json
{
  "detail": [
    {
      "loc": ["body", "email"],
      "msg": "value is not a valid email address",
      "type": "value_error.email"
    }
  ]
}
```

## Error Handling

### Common Errors

**401 Unauthorized:**
```json
{
  "detail": "Not authenticated"
}
```

**403 Forbidden:**
```json
{
  "detail": "Not enough permissions"
}
```

**404 Not Found:**
```json
{
  "detail": "Item not found"
}
```

**422 Validation Error:**
```json
{
  "detail": [
    {
      "loc": ["body", "title"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

## SDKs and Libraries

### Python Client

```python
import httpx
from typing import Optional

class OpenGovFoodClient:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.token: Optional[str] = None

    def login(self, email: str, password: str):
        response = httpx.post(
            f"{self.base_url}/api/v1/users/login/access-token",
            data={"username": email, "password": password}
        )
        self.token = response.json()["access_token"]

    def get_items(self):
        headers = {"Authorization": f"Bearer {self.token}"}
        response = httpx.get(
            f"{self.base_url}/api/v1/items/",
            headers=headers
        )
        return response.json()
```

### JavaScript/TypeScript Client

```javascript
class OpenGovFoodClient {
  constructor(baseURL = 'http://localhost:8000') {
    this.baseURL = baseURL;
    this.token = null;
  }

  async login(email, password) {
    const response = await fetch(`${this.baseURL}/api/v1/users/login/access-token`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: new URLSearchParams({ username: email, password })
    });
    const data = await response.json();
    this.token = data.access_token;
  }

  async getItems() {
    const response = await fetch(`${this.baseURL}/api/v1/items/`, {
      headers: { 'Authorization': `Bearer ${this.token}` }
    });
    return response.json();
  }
}
```

## Versioning

The API uses URL versioning (`/api/v1/`). Future versions will be added as `/api/v2/`, etc.

## Deprecation Policy

Deprecated endpoints will be marked in the documentation and supported for at least 6 months before removal.

## Support

For API support:
- Check the [API Reference](authentication.md) for detailed endpoint documentation
- View the OpenAPI specification at `/docs` or `/openapi.json`
- Report issues on [GitHub](https://github.com/llamasearchai/OpenGov-Food/issues)