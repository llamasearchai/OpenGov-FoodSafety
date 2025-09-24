import random
import string

from fastapi.testclient import TestClient
from faker import Faker

from opengovfood.core.config import get_settings

settings = get_settings()

fake = Faker()


def random_lower_string() -> str:
    return "".join(random.choices(string.ascii_lowercase, k=32))


def random_email() -> str:
    return fake.email()


def get_superuser_token_headers(client: TestClient) -> dict[str, str]:
    login_data = {
        "username": settings.FIRST_SUPERUSER,
        "password": settings.FIRST_SUPERUSER_PASSWORD,
    }
    r = client.post(f"{settings.API_V1_STR}/login/access-token", data=login_data)
    r.raise_for_status()  # Raise an exception for bad status codes
    tokens = r.json()
    a_token = tokens.get("access_token")
    if not a_token:
        raise ValueError("No access token received from login endpoint")
    headers = {"Authorization": f"Bearer {a_token}"}
    return headers
