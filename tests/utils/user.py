import random
import string
from sqlalchemy.orm import Session

from opengovfood import crud, models, schemas


def random_lower_string() -> str:
    return "".join(random.choices(string.ascii_lowercase, k=32))


def random_email() -> str:
    return f"{random_lower_string()}@{random_lower_string()}.com"


def create_random_user(db: Session) -> models.User:
    email = random_email()
    password = random_lower_string()
    user_in = schemas.UserCreate(email=email, password=password)
    user = crud.user.create(db, obj_in=user_in)
    return user