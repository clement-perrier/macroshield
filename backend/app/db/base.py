from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Shared declarative base — every ORM model in app/models registers on this,
    and Alembic's env.py imports Base.metadata off it to autogenerate migrations."""
