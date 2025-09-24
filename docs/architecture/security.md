# Security Architecture

OpenGov-Food implements comprehensive security measures following industry best practices for authentication, authorization, and data protection.

## Security Overview

```mermaid
graph TB
    A[Client Request] --> B[CORS Middleware]
    B --> C[Authentication]
    C --> D[JWT Validation]
    D --> E[Authorization]
    E --> F[Business Logic]

    C --> G[Rate Limiting]
    D --> H[Token Expiration]
    E --> I[Ownership Checks]

    F --> J[Input Validation]
    J --> K[SQL Injection Prevention]
    J --> L[XSS Protection]
```

## Authentication System

### JWT (JSON Web Tokens)

**Token Structure:**
```json
{
  "sub": "user@example.com",
  "exp": 1640995200,
  "iat": 1640991600,
  "type": "access"
}
```

**Configuration:**
```python
# Security settings
SECRET_KEY = "your-very-long-secret-key-here"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
```

### Password Security

**Hashing Algorithm:**
- bcrypt with automatic salt generation
- Configurable work factor (default: 12)
- No plain text password storage

```python
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)
```

### Authentication Flow

```mermaid
sequenceDiagram
    participant User
    participant API
    participant Auth
    participant DB

    User->>API: POST /login
    API->>Auth: Validate credentials
    Auth->>DB: Check user/password
    DB-->>Auth: User data
    Auth->>Auth: Generate JWT
    Auth-->>API: Return token
    API-->>User: Token response

    User->>API: GET /protected (with token)
    API->>Auth: Verify JWT
    Auth-->>API: User context
    API-->>User: Protected data
```

## Authorization

### User Ownership Model

- Users can only access their own data
- Foreign key constraints enforce ownership
- API endpoints validate user context

```python
from fastapi import Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> User:
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials"
    )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = await UserCRUD.get_by_email(db, email=email)
    if user is None:
        raise credentials_exception
    return user

async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user
```

### API Permissions

```python
# Item operations require ownership
@app.get("/items/{item_id}")
async def read_item(
    item_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    item = await ItemCRUD.get(db, item_id=item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    if item.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    return item
```

## Input Validation

### Pydantic Model Validation

```python
from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional

class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    full_name: str = Field(..., min_length=1, max_length=255)

    @validator('password')
    def password_strength(cls, v):
        if not re.match(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)', v):
            raise ValueError('Password must contain uppercase, lowercase, and digit')
        return v

class ItemCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=1000)
    status: str = Field("pending", regex=r'^(pending|in_progress|completed|cancelled)$')
```

### SQL Injection Prevention

- Parameterized queries using SQLAlchemy
- No string concatenation for SQL
- Automatic escaping of special characters

```python
# Safe parameterized query
stmt = select(User).where(User.email == email)

# Never do this (vulnerable to SQL injection)
# stmt = select(User).where(text(f"email = '{email}'"))
```

## Rate Limiting

### Implementation

```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.middleware import SlowAPIMiddleware

limiter = Limiter(key_func=get_remote_address)

# Global rate limiting
@app.middleware("http")
async def add_rate_limiting(request, call_next):
    # Custom rate limiting logic
    pass

# Endpoint-specific limits
@app.post("/users/open")
@limiter.limit("10/minute")
async def register_user():
    pass

@app.post("/users/login/access-token")
@limiter.limit("5/minute")
async def login():
    pass
```

### Rate Limit Configuration

```python
# Rate limits by endpoint
RATE_LIMITS = {
    "register": "10/minute",
    "login": "5/minute",
    "api": "100/minute"
}
```

## CORS (Cross-Origin Resource Sharing)

### Configuration

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://yourdomain.com"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)
```

### Security Considerations

- Restrict origins in production
- Use specific allowed headers
- Enable credentials only when necessary
- Regular review of allowed origins

## HTTPS and SSL/TLS

### Production SSL Setup

```python
# Uvicorn with SSL
uvicorn opengovfood.web.app:app \
    --host 0.0.0.0 \
    --port 443 \
    --ssl-keyfile /path/to/private.key \
    --ssl-certfile /path/to/certificate.crt
```

### SSL Certificate Management

- Use Let's Encrypt for free certificates
- Automatic renewal with certbot
- Strong cipher suites only
- HSTS headers for security

## Security Headers

### Helmet Middleware

```python
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

# HTTPS redirection
app.add_middleware(HTTPSRedirectMiddleware)

# Trusted hosts
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["yourdomain.com", "*.yourdomain.com"]
)
```

### Security Headers

```python
@app.middleware("http")
async def add_security_headers(request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Content-Security-Policy"] = "default-src 'self'"
    return response
```

## Data Protection

### Encryption at Rest

```python
# Database encryption (PostgreSQL)
# Enable encryption in database configuration
DATABASE_URL = "postgresql+asyncpg://user:password@localhost/opengovfood?ssl=require"

# File encryption for sensitive data
from cryptography.fernet import Fernet

key = Fernet.generate_key()
cipher = Fernet(key)

def encrypt_data(data: str) -> str:
    return cipher.encrypt(data.encode()).decode()

def decrypt_data(encrypted_data: str) -> str:
    return cipher.decrypt(encrypted_data.encode()).decode()
```

### Data Sanitization

```python
import bleach

def sanitize_html(text: str) -> str:
    """Sanitize HTML input to prevent XSS."""
    allowed_tags = ['p', 'br', 'strong', 'em']
    allowed_attrs = {}
    return bleach.clean(text, tags=allowed_tags, attributes=allowed_attrs)
```

## Session Management

### Stateless JWT Sessions

- No server-side session storage
- Tokens contain all necessary user information
- Automatic expiration prevents indefinite access
- Token revocation requires database tracking (future enhancement)

### Session Security

```python
# Token blacklist for logout (future implementation)
class TokenBlacklist(Base):
    __tablename__ = "token_blacklist"

    id = Column(Integer, primary_key=True)
    token = Column(String, unique=True, index=True)
    blacklisted_at = Column(DateTime, default=datetime.utcnow)
```

## Error Handling

### Secure Error Responses

```python
@app.exception_handler(HTTPException)
async def http_exception_handler(request, call_next):
    # Don't leak internal details
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": "An error occurred"}
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, call_next):
    # Log internal error details
    logger.error(f"Internal error: {exc}", exc_info=True)
    # Return generic message
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )
```

## Security Monitoring

### Logging Security Events

```python
import structlog

logger = structlog.get_logger()

async def log_security_event(event_type: str, user_id: int = None, details: dict = None):
    """Log security-related events."""
    event = {
        "event_type": event_type,
        "user_id": user_id,
        "timestamp": datetime.utcnow(),
        "ip_address": get_client_ip(),
        "user_agent": get_user_agent(),
        **(details or {})
    }
    logger.info("Security event", **event)
```

### Security Event Types

- `login_success`
- `login_failure`
- `password_change`
- `token_refresh`
- `unauthorized_access`
- `rate_limit_exceeded`

## Penetration Testing

### Security Checklist

- [ ] SQL injection testing
- [ ] XSS vulnerability testing
- [ ] CSRF protection verification
- [ ] Authentication bypass testing
- [ ] Authorization testing
- [ ] Rate limiting verification
- [ ] SSL/TLS configuration testing
- [ ] Security headers validation

### Automated Security Testing

```python
# Security test examples
def test_sql_injection_protection():
    """Test that SQL injection attempts are blocked."""
    malicious_input = "'; DROP TABLE user; --"
    response = client.post("/items/", json={"title": malicious_input})
    assert response.status_code == 422  # Validation error

def test_xss_protection():
    """Test that XSS attempts are sanitized."""
    xss_payload = "<script>alert('xss')</script>"
    response = client.post("/items/", json={"title": xss_payload})
    assert "<script>" not in response.json()["title"]
```

## Compliance

### Data Protection Regulations

- **GDPR**: EU data protection compliance
- **CCPA**: California consumer privacy
- **Data minimization**: Collect only necessary data
- **Right to erasure**: User data deletion
- **Data portability**: Export user data

### Security Standards

- **OWASP Top 10**: Address common vulnerabilities
- **NIST Cybersecurity Framework**: Security best practices
- **ISO 27001**: Information security management

## Incident Response

### Security Incident Procedure

1. **Detection**: Monitor logs and alerts
2. **Assessment**: Evaluate incident severity
3. **Containment**: Isolate affected systems
4. **Recovery**: Restore normal operations
5. **Lessons Learned**: Update security measures

### Emergency Contacts

- Security Team: security@opengovfood.com
- Infrastructure: infra@opengovfood.com
- Legal/Compliance: legal@opengovfood.com

## Future Security Enhancements

- **Multi-factor authentication (MFA)**
- **OAuth2 social login**
- **Role-based access control (RBAC)**
- **API key authentication**
- **Security audit logging**
- **Automated security scanning**
- **Zero-trust architecture**
- **End-to-end encryption**