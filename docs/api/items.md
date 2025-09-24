# Items API

The Items API provides complete CRUD operations for managing food safety inspection items with user ownership and status tracking.

## Overview

- **CRUD Operations**: Create, Read, Update, Delete items
- **User Ownership**: Items belong to authenticated users
- **Status Tracking**: Track inspection status and progress
- **Filtering**: Advanced filtering and pagination support

## Endpoints

### List Items

Get a paginated list of items for the authenticated user.

```
GET /api/v1/items/
```

**Query Parameters:**
- `skip` (int): Number of items to skip (default: 0)
- `limit` (int): Maximum items to return (default: 100, max: 1000)
- `status` (string): Filter by status (pending, in_progress, completed, cancelled)
- `search` (string): Search in title and description

**Response (200):**
```json
{
  "items": [
    {
      "id": 1,
      "title": "Restaurant Inspection",
      "description": "Monthly health inspection",
      "status": "pending",
      "created_at": "2024-01-01T00:00:00Z",
      "updated_at": "2024-01-01T00:00:00Z",
      "owner_id": 1
    }
  ],
  "total": 1,
  "skip": 0,
  "limit": 100
}
```

**Example:**
```bash
curl -X GET "http://localhost:8000/api/v1/items/?status=pending&limit=10" \
  -H "Authorization: Bearer <token>"
```

### Create Item

Create a new item for the authenticated user.

```
POST /api/v1/items/
```

**Request Body:**
```json
{
  "title": "string",        // required, 1-100 characters
  "description": "string",  // optional, max 1000 characters
  "status": "string"        // optional, default: "pending"
}
```

**Response (201):**
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

**Example:**
```bash
curl -X POST "http://localhost:8000/api/v1/items/" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "New Inspection",
    "description": "Quarterly safety check",
    "status": "pending"
  }'
```

### Get Item

Get a specific item by ID.

```
GET /api/v1/items/{item_id}
```

**Path Parameters:**
- `item_id` (int): Item ID

**Response (200):** Same as create response

**Error Responses:**
- `404 Not Found`: Item not found or not owned by user

**Example:**
```bash
curl -X GET "http://localhost:8000/api/v1/items/1" \
  -H "Authorization: Bearer <token>"
```

### Update Item

Update an existing item.

```
PUT /api/v1/items/{item_id}
```

**Path Parameters:**
- `item_id` (int): Item ID

**Request Body:** Same as create, all fields optional

**Response (200):** Updated item data

**Example:**
```bash
curl -X PUT "http://localhost:8000/api/v1/items/1" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "status": "completed",
    "description": "Updated description"
  }'
```

### Delete Item

Delete an item.

```
DELETE /api/v1/items/{item_id}
```

**Path Parameters:**
- `item_id` (int): Item ID

**Response (204):** No content

**Example:**
```bash
curl -X DELETE "http://localhost:8000/api/v1/items/1" \
  -H "Authorization: Bearer <token>"
```

## Data Models

### Item Create/Update

```python
from pydantic import BaseModel, Field
from typing import Optional

class ItemCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=1000)
    status: str = Field("pending", regex="^(pending|in_progress|completed|cancelled)$")

class ItemUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=1000)
    status: Optional[str] = Field(None, regex="^(pending|in_progress|completed|cancelled)$")
```

### Item Response

```python
from datetime import datetime
from pydantic import BaseModel

class Item(BaseModel):
    id: int
    title: str
    description: Optional[str]
    status: str
    created_at: datetime
    updated_at: datetime
    owner_id: int

    class Config:
        from_attributes = True
```

### Paginated Response

```python
from typing import List

class PaginatedItems(BaseModel):
    items: List[Item]
    total: int
    skip: int
    limit: int
```

## Status Values

Items can have the following statuses:

- `pending`: Initial state, not yet started
- `in_progress`: Currently being worked on
- `completed`: Finished successfully
- `cancelled`: Cancelled or abandoned

## Filtering and Search

### Status Filtering

```bash
# Get only pending items
GET /api/v1/items/?status=pending

# Get completed items
GET /api/v1/items/?status=completed
```

### Text Search

```bash
# Search in title and description
GET /api/v1/items/?search=restaurant
```

### Pagination

```bash
# Get first 10 items
GET /api/v1/items/?skip=0&limit=10

# Get next page
GET /api/v1/items/?skip=10&limit=10
```

## Usage Examples

### Python Client

```python
import httpx
from typing import List, Dict, Any

class ItemsClient:
    def __init__(self, base_url: str, token: str):
        self.base_url = base_url
        self.headers = {"Authorization": f"Bearer {token}"}

    def get_items(self, status: str = None, limit: int = 100) -> Dict[str, Any]:
        params = {"limit": limit}
        if status:
            params["status"] = status

        response = httpx.get(
            f"{self.base_url}/api/v1/items/",
            headers=self.headers,
            params=params
        )
        return response.json()

    def create_item(self, title: str, description: str = "", status: str = "pending") -> Dict[str, Any]:
        data = {
            "title": title,
            "description": description,
            "status": status
        }

        response = httpx.post(
            f"{self.base_url}/api/v1/items/",
            headers=self.headers,
            json=data
        )
        return response.json()

    def update_item(self, item_id: int, **updates) -> Dict[str, Any]:
        response = httpx.put(
            f"{self.base_url}/api/v1/items/{item_id}",
            headers=self.headers,
            json=updates
        )
        return response.json()

    def delete_item(self, item_id: int) -> bool:
        response = httpx.delete(
            f"{self.base_url}/api/v1/items/{item_id}",
            headers=self.headers
        )
        return response.status_code == 204
```

### JavaScript Client

```javascript
class ItemsAPI {
  constructor(baseURL, token) {
    this.baseURL = baseURL;
    this.headers = {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    };
  }

  async getItems(params = {}) {
    const url = new URL(`${this.baseURL}/api/v1/items/`);
    Object.keys(params).forEach(key => url.searchParams.append(key, params[key]));

    const response = await fetch(url, { headers: this.headers });
    return response.json();
  }

  async createItem(itemData) {
    const response = await fetch(`${this.baseURL}/api/v1/items/`, {
      method: 'POST',
      headers: this.headers,
      body: JSON.stringify(itemData)
    });
    return response.json();
  }

  async updateItem(itemId, updates) {
    const response = await fetch(`${this.baseURL}/api/v1/items/${itemId}`, {
      method: 'PUT',
      headers: this.headers,
      body: JSON.stringify(updates)
    });
    return response.json();
  }

  async deleteItem(itemId) {
    const response = await fetch(`${this.baseURL}/api/v1/items/${itemId}`, {
      method: 'DELETE',
      headers: this.headers
    });
    return response.status_code === 204;
  }
}
```

## Error Handling

### Common Errors

**Item Not Found:**
```json
{
  "detail": "Item not found"
}
```

**Permission Denied:**
```json
{
  "detail": "Not enough permissions"
}
```

**Validation Error:**
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

## Testing

### Unit Tests

```python
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_create_item(client: AsyncClient, test_user_token: str):
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

@pytest.mark.asyncio
async def test_get_items(client: AsyncClient, test_user_token: str):
    headers = {"Authorization": f"Bearer {test_user_token}"}

    response = await client.get("/api/v1/items/", headers=headers)
    assert response.status_code == 200

    data = response.json()
    assert "items" in data
    assert "total" in data
```

## Performance Considerations

- Items are indexed by owner_id for fast user-specific queries
- Pagination prevents large result sets
- Database queries use async SQLAlchemy for optimal performance
- Response compression for large lists

## Future Enhancements

- Bulk operations (create/update multiple items)
- Advanced filtering (date ranges, custom fields)
- Item sharing between users
- File attachments for inspections
- Audit logging for changes
- Export functionality (CSV, PDF)