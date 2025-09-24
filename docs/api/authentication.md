# Authentication API

The authentication system provides secure user registration, login, and token management using JWT (JSON Web Tokens).

## Overview

- **Registration**: Open registration for new users
- **Login**: OAuth2 compatible token endpoint
- **JWT Tokens**: Bearer token authentication
- **Security**: bcrypt password hashing

## Endpoints

### Register User

Register a new user account.

```
POST /api/v1/users/open
```

**Request Body:**
```json
{
  "email": "string",      // required, valid email
  "password": "string",   // required, min 8 characters
  "full_name": "string"   // required
}
```

**Response (201):**
```json
{
  "id": 1,
  "email": "user@example.com",
  "full_name": "John Doe",
  "is_active": true,
  "created_at": "2024-01-01T00:00:00Z"
}
```

**Error Responses:**

- `400 Bad Request`: Email already registered
- `422 Validation Error`: Invalid input data

**Example:**
```bash
curl -X POST "http://localhost:8000/api/v1/users/open" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "john@example.com",
    "password": "securepassword123",
    "full_name": "John Doe"
  }'
```

### Login Access Token

Authenticate user and receive access token.

```
POST /api/v1/users/login/access-token
```

**Request Body:** (application/x-www-form-urlencoded)
```
username: string  // user email
password: string  // user password
```

**Response (200):**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer"
}
```

**Error Responses:**

- `400 Bad Request`: Incorrect email or password
- `422 Validation Error`: Missing credentials

**Example:**
```bash
curl -X POST "http://localhost:8000/api/v1/users/login/access-token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=john@example.com&password=securepassword123"
```

## Authentication Flow

### 1. Register User

```python
import httpx

# Register new user
user_data = {
    "email": "user@example.com",
    "password": "securepassword",
    "full_name": "User Name"
}

response = httpx.post(
    "http://localhost:8000/api/v1/users/open",
    json=user_data
)
user = response.json()
print(f"User created: {user}")
```

### 2. Login and Get Token

```python
# Login to get access token
login_data = {
    "username": "user@example.com",
    "password": "securepassword"
}

response = httpx.post(
    "http://localhost:8000/api/v1/users/login/access-token",
    data=login_data
)
auth_data = response.json()
token = auth_data["access_token"]
print(f"Access token: {token}")
```

### 3. Use Token for API Calls

```python
# Use token in subsequent requests
headers = {"Authorization": f"Bearer {token}"}

response = httpx.get(
    "http://localhost:8000/api/v1/items/",
    headers=headers
)
items = response.json()
print(f"Items: {items}")
```

## Token Usage

### Bearer Token Format

Include the JWT token in the Authorization header:

```
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
```

### Token Expiration

- Default expiration: 30 minutes (configurable)
- Tokens are stateless and cannot be revoked individually
- Use refresh tokens for longer sessions (future feature)

### Token Validation

Tokens are validated on each request:

```python
from opengovfood.core.security import verify_token

# Verify token
payload = verify_token(token)
user_id = payload.get("sub")
```

## Security Features

### Password Hashing

- Uses bcrypt with automatic salt generation
- Configurable work factor for security/performance balance
- No plain text password storage

### JWT Security

- HS256 algorithm (configurable)
- Configurable secret key (must be strong in production)
- Standard JWT claims (iss, sub, exp, iat)

### Rate Limiting

- Registration: 10 requests per minute per IP
- Login: 5 attempts per minute per IP
- Failed login tracking to prevent brute force

## Data Models

### User Registration

```python
from pydantic import BaseModel, EmailStr

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str
```

### User Response

```python
from datetime import datetime
from pydantic import BaseModel

class User(BaseModel):
    id: int
    email: str
    full_name: str
    is_active: bool
    created_at: datetime
```

### Token Response

```python
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
```

## Error Handling

### Common Authentication Errors

**Invalid Credentials:**
```json
{
  "detail": "Incorrect email or password"
}
```

**Token Expired:**
```json
{
  "detail": "Token has expired"
}
```

**Invalid Token:**
```json
{
  "detail": "Could not validate credentials"
}
```

**Missing Token:**
```json
{
  "detail": "Not authenticated"
}
```

## Testing Authentication

### Register Test User

```python
def test_user_registration():
    user_data = {
        "email": "test@example.com",
        "password": "testpassword",
        "full_name": "Test User"
    }

    response = client.post("/api/v1/users/open", json=user_data)
    assert response.status_code == 201

    user = response.json()
    assert user["email"] == "test@example.com"
    assert user["is_active"] == True
```

### Login Test

```python
def test_user_login():
    # First register user
    user_data = {
        "email": "test@example.com",
        "password": "testpassword",
        "full_name": "Test User"
    }
    client.post("/api/v1/users/open", json=user_data)

    # Then login
    login_data = {
        "username": "test@example.com",
        "password": "testpassword"
    }

    response = client.post(
        "/api/v1/users/login/access-token",
        data=login_data
    )
    assert response.status_code == 200

    token_data = response.json()
    assert "access_token" in token_data
    assert token_data["token_type"] == "bearer"
```

## Configuration

Authentication settings in `.env`:

```env
# JWT Settings
SECRET_KEY=your-secret-key-here
ACCESS_TOKEN_EXPIRE_MINUTES=30
ALGORITHM=HS256

# Security
BCRYPT_ROUNDS=12
```

## Future Enhancements

- Refresh tokens for longer sessions
- Password reset functionality
- Email verification
- OAuth2 social login
- Multi-factor authentication
- Account lockout policies