# Configuration

OpenGov-Food uses Pydantic settings for configuration management, allowing you to configure the application through environment variables, configuration files, or direct code.

## Configuration Sources

The application loads configuration in this order (later sources override earlier ones):

1. **Default values** in the code
2. **Environment variables** (recommended for production)
3. **.env file** in the project root
4. **Configuration files** (JSON, YAML, TOML)

## Environment Variables

Create a `.env` file in your project root:

```bash
# Copy the example
cp .env.example .env
```

### Basic Configuration

```env
# Application
APP_NAME=OpenGov-Food
ENVIRONMENT=development
DEBUG=true

# Server
HOST=0.0.0.0
PORT=8000

# Database
DATABASE_URL=sqlite+aiosqlite:///./opengovfood.db

# Security
SECRET_KEY=your-super-secret-key-change-this-in-production
ACCESS_TOKEN_EXPIRE_MINUTES=30
ALGORITHM=HS256

# Optional: CORS
BACKEND_CORS_ORIGINS=["http://localhost:3000", "http://localhost:8080"]

# Optional: OpenAI (for future AI features)
OPENAI_API_KEY=your-openai-api-key

# Optional: Ollama (for local AI models)
OLLAMA_BASE_URL=http://localhost:11434
```

### Production Configuration

For production deployment, use stronger settings:

```env
# Application
APP_NAME=OpenGov-Food
ENVIRONMENT=production
DEBUG=false

# Server
HOST=0.0.0.0
PORT=8000

# Database (PostgreSQL recommended for production)
DATABASE_URL=postgresql+asyncpg://user:password@localhost/opengovfood

# Security (Generate a strong random key)
SECRET_KEY=your-very-long-random-secret-key-here-at-least-32-characters
ACCESS_TOKEN_EXPIRE_MINUTES=15
ALGORITHM=HS256

# CORS (restrict to your frontend domains)
BACKEND_CORS_ORIGINS=["https://yourdomain.com", "https://app.yourdomain.com"]
```

## Configuration Classes

The application uses Pydantic settings classes for type-safe configuration.

### Core Settings

```python
# src/opengovfood/core/config.py
from pydantic import BaseSettings, Field
from typing import List, Optional

class Settings(BaseSettings):
    # Application
    app_name: str = Field(default="OpenGov-Food", env="APP_NAME")
    environment: str = Field(default="development", env="ENVIRONMENT")
    debug: bool = Field(default=False, env="DEBUG")

    # Server
    host: str = Field(default="127.0.0.1", env="HOST")
    port: int = Field(default=8000, env="PORT")

    # Database
    database_url: str = Field(
        default="sqlite+aiosqlite:///./opengovfood.db",
        env="DATABASE_URL"
    )

    # Security
    secret_key: str = Field(
        default="your-secret-key-here",
        env="SECRET_KEY"
    )
    access_token_expire_minutes: int = Field(
        default=30,
        env="ACCESS_TOKEN_EXPIRE_MINUTES"
    )
    algorithm: str = Field(default="HS256", env="ALGORITHM")

    # CORS
    backend_cors_origins: List[str] = Field(
        default=["http://localhost:3000"],
        env="BACKEND_CORS_ORIGINS"
    )

    # Optional AI services
    openai_api_key: Optional[str] = Field(default=None, env="OPENAI_API_KEY")
    ollama_base_url: Optional[str] = Field(
        default="http://localhost:11434",
        env="OLLAMA_BASE_URL"
    )

    class Config:
        env_file = ".env"
        case_sensitive = False
```

## Database Configuration

### SQLite (Development)

Default configuration for development:

```env
DATABASE_URL=sqlite+aiosqlite:///./opengovfood.db
```

### PostgreSQL (Production)

For production, use PostgreSQL:

```env
DATABASE_URL=postgresql+asyncpg://user:password@localhost/opengovfood
```

Required packages:
```bash
pip install psycopg2-binary asyncpg
```

## Security Configuration

### JWT Settings

```env
# Use a long, random string (at least 32 characters)
SECRET_KEY=your-very-long-random-secret-key-here-at-least-32-characters

# Token expiration in minutes
ACCESS_TOKEN_EXPIRE_MINUTES=15

# JWT algorithm (HS256 is recommended)
ALGORITHM=HS256
```

### Password Security

Passwords are hashed using bcrypt. The work factor is configurable:

```python
# In security.py
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
```

## CORS Configuration

Configure allowed origins for cross-origin requests:

```env
# Development
BACKEND_CORS_ORIGINS=["http://localhost:3000", "http://localhost:8080"]

# Production
BACKEND_CORS_ORIGINS=["https://yourdomain.com", "https://app.yourdomain.com"]
```

## Logging Configuration

Logging is configured in `src/opengovfood/utils/logging.py`:

```python
# Default log level
LOG_LEVEL=INFO

# Log format
LOG_FORMAT="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
```

## Environment-Specific Configuration

### Development

```env
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=DEBUG
DATABASE_URL=sqlite+aiosqlite:///./opengovfood_dev.db
```

### Testing

```env
ENVIRONMENT=testing
DEBUG=false
LOG_LEVEL=WARNING
DATABASE_URL=sqlite+aiosqlite:///./opengovfood_test.db
```

### Production

```env
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO
DATABASE_URL=postgresql+asyncpg://user:password@localhost/opengovfood
SECRET_KEY=your-production-secret-key
ACCESS_TOKEN_EXPIRE_MINUTES=15
```

## Configuration Validation

The application validates configuration on startup:

```python
from opengovfood.core.config import settings

# Access settings
print(f"App name: {settings.app_name}")
print(f"Database URL: {settings.database_url}")
print(f"Debug mode: {settings.debug}")
```

Invalid configurations will raise validation errors with helpful messages.

## Runtime Configuration

Some settings can be changed at runtime:

```python
# Change log level
import logging
logging.getLogger().setLevel(logging.DEBUG)

# Update CORS settings (requires restart)
# This would need to be implemented in the app
```

## Best Practices

1. **Never commit secrets** to version control
2. **Use environment variables** for production
3. **Generate strong secret keys** for production
4. **Restrict CORS origins** in production
5. **Use different databases** for different environments
6. **Set short token expiration** times in production
7. **Enable debug mode** only in development

## Troubleshooting

**Configuration not loading**: Check that your `.env` file exists and has correct syntax.

```bash
# Check .env file
cat .env

# Validate with Python
python -c "from opengovfood.core.config import settings; print(settings.dict())"
```

**Database connection fails**: Verify your DATABASE_URL format.

```bash
# Test database connection
python -c "from opengovfood.core.database import DatabaseManager; import asyncio; asyncio.run(DatabaseManager.test_connection())"
```

**CORS issues**: Check your BACKEND_CORS_ORIGINS setting.

```bash
# Check CORS headers in browser dev tools
# Look for 'Access-Control-Allow-Origin' header
```