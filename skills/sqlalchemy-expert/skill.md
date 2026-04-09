# Skill: SQLAlchemy Expert (Performance & Safety)
# Usage: Use for backend services involving SQL databases and SQLAlchemy ORM (v2.0+).

## Best Practices:
- **Async Engine:** Use `AsyncSession` and `create_async_engine` for modern FastAPI backends.
- **Declarative Mapping:** Use `Mapped` and `mapped_column` for modern v2.0 type hinting.
- **Relationship Management:** Always specify `lazy="selectin"` for collections or `joinedload` for many-to-one to avoid N+1 query problems.
- **Transaction Safety:** Use `async with session.begin()` to ensure atomicity.
- **Migration:** Always use **Alembic** for schema changes.

## Pattern: Modern SQLAlchemy 2.0 Repository
```python
from sqlalchemy import select
from sqlalchemy.orm import Mapped, mapped_column

class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(unique=True, index=True)

async def get_user_by_email(session: AsyncSession, email: str) -> User | None:
    stmt = select(User).where(User.email == email)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()
```

## Guardrails:
- Never use `session.expire_on_commit = True` in async contexts.
- Avoid raw SQL strings; use the SQL Expression Language.
- Ensure all indexes are explicitly defined in the model.
